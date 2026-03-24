import json
import os
from datetime import datetime, timezone

import boto3

dynamodb = boto3.resource("dynamodb")
SENSORS_TABLE = dynamodb.Table(os.environ["SENSORS_TABLE"])
READINGS_TABLE = dynamodb.Table(os.environ["READINGS_TABLE"])


def json_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def parse_body(event):
    body = event.get("body")
    if not body:
        return {}
    if isinstance(body, str):
        return json.loads(body)
    return body


def path_param(event, name):
    return (event.get("pathParameters") or {}).get(name)


def now_utc_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
