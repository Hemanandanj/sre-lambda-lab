'''import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REQUIRED_FIELDS = {"listing_id", "make", "model", "year", "price"}


class ValidationError(Exception):
    pass


def validate(listing):
    missing = REQUIRED_FIELDS - listing.keys()
    if missing:
        raise ValidationError(f"missing fields: {sorted(missing)}")
    if listing["price"] <= 0:
        raise ValidationError("price must be positive")
    if not isinstance(listing["price"], (int, float)):
        raise ValidationError(f"price must be a number, got {type(listing['price']).__name__}")
    if listing["price"] <= 0:
        raise ValidationError("price must be positive")


def process_record(record):
    listing = json.loads(record["body"])
    validate(listing)
    logger.info("Valid listing %s: %s %s",
                listing["listing_id"], listing["make"], listing["model"])


def lambda_handler(event, context):
    failures = []
    records = event.get("Records", [])

    for record in records:
        try:
            process_record(record)
        except Exception as exc:
            logger.error("Message %s failed: %s: %s",
                         record["messageId"], type(exc).__name__, exc)
            failures.append({"itemIdentifier": record["messageId"]})

    logger.info("Batch done: %d received, %d failed", len(records), len(failures))
    return {"batchItemFailures": failures} '''


import json
import logging
from urllib.parse import unquote_plus

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_s3_objects(sqs_record):
    """Return a list of (bucket, key, size) from one SQS message."""
    body = json.loads(sqs_record["body"])

    # S3 sends this once when the notification is created. Not an error.
    if body.get("Event") == "s3:TestEvent":
        logger.info("Ignoring s3:TestEvent")
        return []

    objects = []
    for s3_record in body["Records"]:
        bucket = s3_record["s3"]["bucket"]["name"]
        key = unquote_plus(s3_record["s3"]["object"]["key"])  # "stock+feed" -> "stock feed"
        size = s3_record["s3"]["object"]["size"]
        objects.append((bucket, key, size))
    return objects


def process_object(bucket, key, size):
    # Step 6: download the CSV and read stock_id + price here
    logger.info("New file: s3://%s/%s (%d bytes)", bucket, key, size)


def lambda_handler(event, context):
    request_id = getattr(context, "aws_request_id", "local")
    records = event.get("Records", [])
    failures = []
    logger.info("request_id=%s received %d SQS message(s)", request_id, len(records))

    for record in records:
        try:
            for bucket, key, size in parse_s3_objects(record):
                process_object(bucket, key, size)
        except Exception as exc:
            attempt = record.get("attributes", {}).get("ApproximateReceiveCount", "?")
            logger.error("Message %s failed (attempt %s): %s: %s",
                         record["messageId"], attempt, type(exc).__name__, exc)
            failures.append({"itemIdentifier": record["messageId"]})

    logger.info("request_id=%s done, %d failed", request_id, len(failures))
    return {"batchItemFailures": failures}