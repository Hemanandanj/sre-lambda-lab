locals {
  function_name = "listing-processor-dev"
}

# 1. Zip the code
data "archive_file" "processor" {
  type        = "zip"
  source_dir  = "${path.module}/../src/processor"
  output_path = "${path.module}/build/processor.zip"
}

# 2. Log group (created by us so we control retention)
resource "aws_cloudwatch_log_group" "processor" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 7
}

# 3. IAM role: WHO can use it (the Lambda service)
resource "aws_iam_role" "processor" {
  name = "${local.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# 4. IAM policy: WHAT it can do (write to its own log group only)
resource "aws_iam_role_policy" "processor_logs" {
  name = "write-logs"
  role = aws_iam_role.processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = "${aws_cloudwatch_log_group.processor.arn}:*"
    }]
  })
}

# 5. The function itself
resource "aws_lambda_function" "processor" {
  function_name    = local.function_name
  role             = aws_iam_role.processor.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.processor.output_path
  source_code_hash = data.archive_file.processor.output_base64sha256
  timeout          = 30
  memory_size      = 128

  depends_on = [
    aws_cloudwatch_log_group.processor,
    aws_iam_role_policy.processor_logs,
  ]
}
