import json
import boto3
from os import environ
from datetime import datetime


def trigger(event, context):
    region, fsm = environ.get('REGION'), environ.get('FSM_ARN')
    print(f"region => {region} FSM => {fsm}")
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    print(f"bucket => {bucket} key => {key}")

    file_name_arr = key.split("/")
    file_name = file_name_arr[len(file_name_arr) - 1]
    client = boto3.client("stepfunctions", region_name=region)
    return client.start_execution(
        stateMachineArn=fsm,
        name=f"{file_name.replace('.', '_')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}",
        input=json.dumps({"bucket": bucket, "key": key})
    )["executionArn"]
