import json
import os
import time
from datetime import datetime, timezone

import boto3


s3 = boto3.client("s3")

BUCKET = os.environ["WORKLOAD_BUCKET"]
PROJECT_NAME = os.environ["PROJECT_NAME"]


def cpu_workload(iterations: int = 250_000) -> int:
    checksum = 0

    for i in range(iterations):
        checksum = (checksum + ((i * 17) % 9973)) % 1_000_000_007

    return checksum


def lambda_handler(event, context):
    start_time = time.perf_counter()

    checksum = cpu_workload()

    duration = time.perf_counter() - start_time

    timestamp = datetime.now(timezone.utc)

    payload = {
        "project": PROJECT_NAME,
        "workload_type": "lambda_cpu",
        "timestamp_utc": timestamp.isoformat(),
        "duration_seconds": round(duration, 6),
        "iterations": 250_000,
        "checksum": checksum,
        "request_id": context.aws_request_id,
        "event": event,
    }

    key = (
        f"analytics/lambda-workloads/"
        f"{timestamp.strftime('%Y/%m/%d/%H%M%S')}-"
        f"{context.aws_request_id}.json"
    )

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Controlled Lambda workload completed",
                "duration_seconds": round(duration, 6),
                "s3_key": key,
                "checksum": checksum,
            }
        ),
    }