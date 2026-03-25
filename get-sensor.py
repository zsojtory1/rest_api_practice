from utils import json_response, path_param, require_sensor


def lambda_handler(event, context):
    try:
        sid = path_param(event, "sid")
        if not sid:
            return json_response(400, {"error": "sid path parameter is required"})

        sensor = require_sensor(sid)
        return json_response(200, sensor)

    except KeyError as e:
        return json_response(404, {"error": str(e)})
    except Exception as e:
        return json_response(500, {"error": str(e)})
