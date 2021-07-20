import time
import boto3
from os import environ
from datetime import datetime


def invoke(event, context):
    client = boto3.client("stepfunctions", region_name=environ.get("REGION"))
    file_name_arr = event["key"].split("/")
    file_name = file_name_arr[len(file_name_arr) - 1]
    for _ in range(3):
        response = client.get_activity_task(
            activityArn=environ.get("ACTIVITY_ARN"),
            workerName=f"{file_name.replace('.', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}"
        )
        if response["taskToken"]:
            event["taskToken"] = response["taskToken"]
            break
        else:
            time.sleep(1)
    print(f"event => {event}")
    return event
