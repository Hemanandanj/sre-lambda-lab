'''import json
import logging
import sys

sys.path.insert(0, "src/processor")
logging.basicConfig(level=logging.INFO)

from handler import lambda_handler

with open("events/sqs_event.json") as f:
    event = json.load(f)

result = lambda_handler(event, context=None)
print("RESULT:", result)

'''

import json
import logging
import sys

sys.path.insert(0, "src/processor")
logging.basicConfig(level=logging.INFO)

from handler import lambda_handler


def s3_event_body(key):
    return {"Records": [{
        "eventSource": "aws:s3",
        "eventName": "ObjectCreated:Put",
        "s3": {"bucket": {"name": "local-bucket"},
               "object": {"key": key, "size": 215}},
    }]}


bodies = [
    {"Service": "Amazon S3", "Event": "s3:TestEvent", "Bucket": "local-bucket"},
    s3_event_body("incoming/stock_feed_001.csv"),
    s3_event_body("incoming/stock+feed+002.csv"),   # URL-encoded, like real S3
    "not json",                                      # a broken message
]

event = {"Records": [
    {"messageId": f"msg-{i}",
     "body": b if isinstance(b, str) else json.dumps(b),   # SQS body is always a string
     "attributes": {"ApproximateReceiveCount": "1"}}
    for i, b in enumerate(bodies, start=1)
]}

print(json.dumps(lambda_handler(event, None), indent=2))