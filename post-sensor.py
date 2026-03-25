from utils import SENSORS_TABLE, json_response, parse_body, path_param, now_utc_iso

import json


def lambda_handler(event, context):
    try:
        sid = path_param(event, "sid")
        if not sid:
            return json_response(400, {"error": "sid path parameter is required"})

        body = parse_body(event)
        country = body.get("country")
        city = body.get("city")
        
        if not country or not city:
            return json_response(422, {"error": "country and city must be provided in request payload"})
        
        now = now_utc_iso()

        existing = SENSORS_TABLE.get_item(
            Key={"sid": sid}).get("Item")

        item = {
            "sid": sid,
            "country": country,
            "city": city,
            "createdAt": now
        }

        if existing:
            return json_response(422, {"error": "sid already exists"})

        SENSORS_TABLE.put_item(Item=item)
        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Location": f"/sensors/{sid}",
            },
            "body": json.dumps(item),
        }

    except Exception as e:
        return json_response(500, {"error": str(e)})
