import json
import logging

logger = logging.getLogger()
y = logger.setLevel(logging.INFO)


REQUIRED_FIELDS = {"listing_id", "make", "model", "year", "price"}


class ValidationError(Exception):
    pass

def validate(listing):
    missing = REQUIRED_FIELDS - listing.keys()
    if missing:
        raise ValidationError(f"missing fields: {sorted(missing)}")

def process_record(record):
    listing = json.loads(record["body"])
    print(listing)