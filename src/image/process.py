import csv
import json
import boto3
import codecs
from os import environ

region, bucket, key, task_token = environ.get(
    "REGION"
), environ.get(
    "BUCKET"
), environ.get(
    "KEY"
), environ.get(
    "TASK_TOKEN"
)
s3c, sfnc = boto3.client(
    "s3",
    region_name=region
), boto3.client(
    "stepfunctions",
    region_name=region
)
try:
    rows = []
    file = s3c.get_object(Bucket=bucket, Key=key)["Body"]
    for row in csv.DictReader(codecs.getreader("utf-8")(file)):
        rows.append(row)
    print(rows)
    sfnc.send_task_success(
        taskToken=task_token,
        output=json.dumps({
            "bucket": bucket,
            "key": key,
            "data": rows
        })
    )
except Exception as e:
    sfnc.send_task_failure(
        taskToken=task_token,
        error=str(e),
        cause="exception"
    )
