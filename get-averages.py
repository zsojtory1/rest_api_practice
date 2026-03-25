from collections import defaultdict
from decimal import Decimal

from utils import (
    ALLOWED_METRICS,
    json_response,
    list_all_sensors,
    query_param,
    query_readings,
    require_sensor,
    validate_range,
)


def aggregate(metrics, readings):
    sums = defaultdict(float)
    counts = defaultdict(int)

    for item in readings:
        values = item.get("metrics", {})
        for metric in metrics:
            value = values.get(metric)
            if isinstance(value, (Decimal)):
                sums[metric] += float(value)
                counts[metric] += 1

    averages = {}
    for metric in metrics:
        averages[metric] = round(
            sums[metric] / counts[metric], 4) if counts[metric] else None

    return averages, max(counts.values(), default=0)


def lambda_handler(event, context):
    try:
        metrics_raw = query_param(event, "metrics")
        if not metrics_raw:
            return json_response(400, {"error": "metrics query parameter is required"})

        metrics = [m.strip() for m in metrics_raw.split(",") if m.strip()]
        if not metrics or any(m not in ALLOWED_METRICS for m in metrics):
            return json_response(422, {"error": f"metrics must be from {sorted(ALLOWED_METRICS)}"})

        sids_raw = query_param(event, "sids")
        from_s = query_param(event, "from")
        to_s = query_param(event, "to")
        group_by = query_param(event, "group_by", "sensor")

        if (from_s and not to_s) or (to_s and not from_s):
            return json_response(422, {"error": "from and to must be provided together"})

        if from_s and to_s:
            from_s, to_s = validate_range(from_s, to_s)

        if sids_raw:
            sids = [s.strip()
                          for s in sids_raw.split(",") if s.strip()]
            sensors = [require_sensor(sid) for sid in sids]
        else:
            sensors = list_all_sensors()
            sids = [s["sid"] for s in sensors]

        if group_by == "sensor":
            rows = []
            for sensor in sensors:
                readings = query_readings(sensor["sid"], from_s, to_s)
                print(readings)
                print(metrics)
                if not from_s and not to_s and readings:
                    readings = [max(readings, key=lambda x: x["recordedAt"])]

                averages, samples = aggregate(metrics, readings)
                rows.append(
                    {
                        "sid": sensor["sid"],
                        "country": sensor.get("country"),
                        "city": sensor.get("city"),
                        "samples": samples,
                        "averages": averages,
                    }
                )

            return json_response(
                200,
                {
                    "query": {
                        "sids": sids,
                        "metrics": metrics,
                        "from": from_s,
                        "to": to_s,
                        "groupBy": group_by,
                    },
                    "data": rows,
                },
            )

        all_readings = []
        for sensor in sensors:
            readings = query_readings(sensor["sid"], from_s, to_s)
            if not from_s and not to_s and readings:
                readings = [max(readings, key=lambda x: x["recordedAt"])]
            all_readings.extend(readings)

        averages, samples = aggregate(metrics, all_readings)
        return json_response(
            200,
            {
                "query": {
                    "sids": sids,
                    "metrics": metrics,
                    "from": from_s,
                    "to": to_s,
                    "groupBy": group_by,
                },
                "data": {
                    "samples": samples,
                    "averages": averages,
                },
            },
        )

    except KeyError as e:
        return json_response(404, {"error": str(e)})
    except ValueError as e:
        return json_response(422, {"error": str(e)})
    except Exception as e:
        return json_response(500, {"error": str(e)})
