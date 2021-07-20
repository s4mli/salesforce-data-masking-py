from aws_cdk import (
    core as cdk,
    aws_s3 as s3,
    aws_ssm as ssm,
    aws_lambda as lamb,
    aws_stepfunctions as sfn,
    aws_s3_notifications as s3n
)


class DataMaskingTriggerStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix, region, processFsmArn = config["prefix"], config["region"], config["processFsmArn"]
        lambda_layer = lamb.LayerVersion(
            self,
            f"{prefix}-data-masking-helper",
            code=lamb.Code.from_asset(path="./src/layer"),
            compatible_runtimes=[lamb.Runtime.PYTHON_3_8],
            layer_version_name=f"{prefix}-data-masking-helper"
        )
        ssm.StringParameter(
            self,
            f"{prefix}-data-masking-helper-latest",
            parameter_name=f"/{prefix}/data-masking-helper/latest",
            string_value=lambda_layer.layer_version_arn
        )
        dropbox_bucket = s3.Bucket(
            self,
            f"{prefix}-data-masking-dropbox",
            bucket_name=f"{prefix}-data-masking-dropbox"
        )
        dropbox_bucket_trigger = lamb.Function(
            self,
            f"{prefix}-data-masking-dropbox-trigger",
            function_name=f"{prefix}-data-masking-dropbox-trigger",
            code=lamb.Code.from_asset(path="./src/lambda"),
            handler="trigger.trigger",
            runtime=lamb.Runtime.PYTHON_3_8,
            memory_size=512,
            timeout=cdk.Duration.minutes(10),
            environment={
                "REGION": region,
                "FSM_ARN": processFsmArn
            }
        )
        dropbox_bucket_trigger.add_layers(lambda_layer)

        dropbox_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(dropbox_bucket_trigger),
            s3.NotificationKeyFilter(suffix=".csv")
        )
        dropbox_bucket.grant_read_write(dropbox_bucket_trigger)

        data_masking_process_fsm = sfn.StateMachine.from_state_machine_arn(
            self,
            f"{prefix}-existing-data-masking-precess-fsm",
            state_machine_arn=processFsmArn
        )
        data_masking_process_fsm.grant_start_execution(dropbox_bucket_trigger)
