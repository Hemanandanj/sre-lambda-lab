data "aws_caller_identity" "current" {}

# ---------- S3 bucket ----------
resource "aws_s3_bucket" "uploads" {
  # Bucket names are GLOBAL across all AWS accounts, so add the account ID
  bucket        = "sre-lab-uploads-${data.aws_caller_identity.current.account_id}"
  force_destroy = true # lab only: lets destroy delete a non-empty bucket
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------- SQS: dead-letter queue ----------
resource "aws_sqs_queue" "stock_feed_dlq" {
  name                      = "stock-feed-dlq"
  message_retention_seconds = 1209600 # 14 days (the maximum)
  sqs_managed_sse_enabled   = true
}

# ---------- SQS: main queue ----------
resource "aws_sqs_queue" "stock_feed" {
  name                       = "stock-feed"
  visibility_timeout_seconds = 180    # 6 x Lambda timeout (30s)
  message_retention_seconds  = 345600 # 4 days
  receive_wait_time_seconds  = 20     # long polling
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.stock_feed_dlq.arn
    maxReceiveCount     = 3
  })
}

# ---------- Allow S3 (only OUR bucket) to send to the queue ----------
resource "aws_sqs_queue_policy" "stock_feed" {
  queue_url = aws_sqs_queue.stock_feed.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowS3BucketToSend"
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.stock_feed.arn
      Condition = {
        ArnEquals    = { "aws:SourceArn" = aws_s3_bucket.uploads.arn }
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
      }
    }]
  })
}

# ---------- S3 -> SQS notification ----------
resource "aws_s3_bucket_notification" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  queue {
    queue_arn     = aws_sqs_queue.stock_feed.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "incoming/"
    filter_suffix = ".csv"
  }

  # S3 checks it can send to the queue when you save this, so the policy must exist first
  depends_on = [aws_sqs_queue_policy.stock_feed]
}

output "bucket_name" { value = aws_s3_bucket.uploads.bucket }
output "queue_url" { value = aws_sqs_queue.stock_feed.id }
output "dlq_url" { value = aws_sqs_queue.stock_feed_dlq.id }


# ---------- Connect SQS -> Lambda ----------

# Lambda reads the queue on our behalf, so its role needs these permissions
resource "aws_iam_role_policy" "processor_sqs" {
  name = "consume-stock-feed"
  role = aws_iam_role.processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
      Resource = aws_sqs_queue.stock_feed.arn
    }]
  })
}

resource "aws_lambda_event_source_mapping" "stock_feed" {
  event_source_arn                   = aws_sqs_queue.stock_feed.arn
  function_name                      = aws_lambda_function.processor.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  function_response_types            = ["ReportBatchItemFailures"]

  scaling_config {
    maximum_concurrency = 5
  }

  depends_on = [aws_iam_role_policy.processor_sqs]
}