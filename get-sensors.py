from utils import json_response, list_all_sensors, query_param


def lambda_handler(event, context):
    try:
        country = query_param(event, "country")
        city = query_param(event, "city")

        items = list_all_sensors()

        if country:
            items = [x for x in items if x.get("country") == country]
        if city:
            items = [x for x in items if x.get("city") == city]

        return json_response(200, {"data": items})

    except Exception as e:
        return json_response(500, {"error": str(e)})
