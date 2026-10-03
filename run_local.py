import json
import logging
import sys

sys.path.insert(0, "src/processor")
logging.basicConfig(level=logging.INFO)

from handler import lambda_handler

with open("events/sqs_event.json") as f:
    event = json.load(f)

result = lambda_handler(event, context=None)
print("RESULT:", result)