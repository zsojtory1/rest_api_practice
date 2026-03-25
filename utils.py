import json
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

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


def list_all_sensors():
    items = []
    resp = SENSORS_TABLE.scan()
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = SENSORS_TABLE.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    return items


def query_param(event, name, default=None):
    params = event.get("queryStringParameters") or {}
    return params.get(name, default)


def query_readings(sid, from_s=None, to_s=None):
    if from_s and to_s:
        key_expr = Key("sid").eq(sid) & Key(
            "recordedAt").between(from_s, to_s)
    else:
        key_expr = Key("sid").eq(sid)

    items = []
    resp = READINGS_TABLE.query(KeyConditionExpression=key_expr)
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = READINGS_TABLE.query(
            KeyConditionExpression=key_expr,
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))
    return items


def validate_range(from_s, to_s):
    from_dt = parse_iso8601(from_s, "from")
    to_dt = parse_iso8601(to_s, "to")

    if from_dt >= to_dt:
        raise ValueError("'from' must be earlier than 'to'")

    days = (to_dt - from_dt).total_seconds() / 86400
    if days < 1 or days > 31:
        raise ValueError("date range must be between 1 and 31 days")

    return iso_z(from_dt), iso_z(to_dt)
