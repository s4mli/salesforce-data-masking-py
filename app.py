#!/usr/bin/env python3
import json
from aws_cdk import core as cdk
from dotted.collection import DottedDict
from infra.data_masking_trigger_stack import DataMaskingTriggerStack
from infra.data_masking_process_stack import DataMaskingProcessStack

config = {}
with open("config.json", "r") as f:
    jdata = json.load(f)
    config = DottedDict(jdata)


app = cdk.App()
for where in [
    "eng",
    # "dev", "test", "prod"
]:
    dmp_stack = DataMaskingProcessStack(
        app,
        f"DataMaskingProcessStack-{where}",
        config={
            "prefix": where,
            "region": config[where].region
        },
        env=cdk.Environment(
            account=config[where].account,
            region=config[where].region
        )
    )
    dmt_stack = DataMaskingTriggerStack(
        app,
        f"DataMaskingTriggerStack-{where}",
        config={
            "prefix": where,
            "region": config[where].region,
            "processFsmArn": dmp_stack.processFsmArn
        },
        env=cdk.Environment(
            account=config[where].account,
            region=config[where].region
        )
    )
    dmt_stack.add_dependency(dmp_stack)

app.synth()
