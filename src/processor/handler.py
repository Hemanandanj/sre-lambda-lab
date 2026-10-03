import json
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
    return {"batchItemFailures": failures}