from uuid import uuid4
import json

from utils import (
    READINGS_TABLE,
    json_response,
    parse_body,
    parse_iso8601,
    path_param,
    require_sensor,
    validate_metrics,
    iso_z,
    now_utc_iso,
)


def lambda_handler(event, context):
    try:
        sid = path_param(event, "sid")
        if not sid:
            return json_response(400, {"error": "sid path parameter is required"})

        require_sensor(sid)

        body = parse_body(event)
        recorded_at = iso_z(parse_iso8601(
            body.get("recordedAt"), "recordedAt"))
        metrics = validate_metrics(body.get("metrics"))

        item = {
            "sid": sid,
            "recordedAt": recorded_at,
            "rid": str(uuid4()),
            "metrics": metrics,
            "createdAt": now_utc_iso(),
        }

        READINGS_TABLE.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(sid) AND attribute_not_exists(recordedAt)",
        )

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "id": item["rid"],
                    "sid": sid,
                    "recordedAt": recorded_at,
                    "metrics": metrics,
                    "createdAt": item["createdAt"],
                }, default=str
            ),
        }

    except KeyError as e:
        return json_response(404, {"error": str(e)})
    except ValueError as e:
        return json_response(422, {"error": str(e)})
    except Exception as e:
        if "ConditionalCheckFailedException" in str(e):
            return json_response(409, {"error": "reading already exists for this sid + recordedAt"})
        return json_response(500, {"error": str(e)})
