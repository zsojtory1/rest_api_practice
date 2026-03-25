from utils import json_response, list_all_sensors


def lambda_handler(event, context):
    try:
        items = list_all_sensors()

        return json_response(200, {"data": items})

    except Exception as e:
        return json_response(500, {"error": str(e)})
