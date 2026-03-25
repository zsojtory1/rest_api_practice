import json
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3

dynamodb = boto3.resource("dynamodb")
SENSORS_TABLE = dynamodb.Table(os.environ["SENSORS_TABLE"])
READINGS_TABLE = dynamodb.Table(os.environ["READINGS_TABLE"])

ALLOWED_METRICS = {"temperature", "humidity", "windSpeed"}


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


def parse_iso8601(value, field_name):
    if not value or not isinstance(value, str):
        raise ValueError(f"{field_name} must be a valid ISO-8601 string")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a valid ISO-8601 string") from exc
    if dt.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone information")
    return dt.astimezone(timezone.utc)


def require_sensor(sid):
    resp = SENSORS_TABLE.get_item(Key={"sid": sid})
    item = resp.get("Item")
    if not item:
        raise KeyError(f"Sensor '{sid}' not found")
    return item


def validate_metrics(metrics_obj):
    if not isinstance(metrics_obj, dict) or not metrics_obj:
        raise ValueError("metrics must be a non-empty object")

    unknown = set(metrics_obj.keys()) - ALLOWED_METRICS
    if unknown:
        raise ValueError(f"unsupported metrics: {sorted(unknown)}")

    normalized = {}
    for key, value in metrics_obj.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"metric '{key}' must be numeric")
        normalized[key] = Decimal(str(value))
    return normalized


def iso_z(dt):
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
