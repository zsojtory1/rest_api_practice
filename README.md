# rest_api_practice

## Implementation
REST API hosted in AWS with serverless Lambdas handling logic and storage in DynamoDB.

## API Endpoints
Base URL: https://53v89bd7sf.execute-api.eu-north-1.amazonaws.com/test

All endpoints require an API key in the request header (Attached in email).

- GET /sensors
  - return all registered sensors with metadata
- GET /sensors/{sid}
  - returns the metadata of the sensor corresponding to sid (sensor ID)
- POST /sensors/{sid}
  - creates a new sensor with chosen sid
  - Payload body: 
  ```json
  {
    "country": "xxx",
    "city": "xxx"
  }
- POST /sensors/{sid}/readings
  - add a new reading entry for a specific time to a sensor, for any (or all) of the metrics: temperature, humidity, windSpeed
  - example payload: 
  ```json
  {
    "recordedAt": "2026-03-24T12:00:00Z",
    "metrics": {
        "temperature": 21,
        "humidity": 65,
        "windSpeed": 6
    }
  }
- GET /reading-averages
  - Complex endpoint to get metric averages using query parameters
  - Query parameters:
    - sids: comma separated list of sensor ids
    - metrics (required): comma separated list of metrics (temperature, humidity, windSpeed)
    - from: timestamp in ISO8601 format
    - to (required if from): timestamp in ISO8601 format
    - group_by: 'sensor' or 'none'

## TODO List
- Documentation
- IaC for AWS Services + CICD
- IAM Roles - not individually configured
- Logging - Monitoring and Alarming in CloudWatch
- DELETE endpoints
- TTL for old readings
- Lambda layer for utils
- Reduce the number of lambdas, using routing based on httpMethod and Resource
- Schema checks
- Wrapper and/or Front-end
- Unit + Integration testing
- API Throttling + Quota
- Custom domain name
- Abstract internal errors
- Pagination for get-sensors