import os
from aws_cdk import (
    core as cdk,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_lambda as lamb,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfnt,
)


class DataMaskingProcessStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix, region = config["prefix"], config["region"]
        process_activity = sfn.Activity(
            self,
            f"{prefix}-data-masking-process-activity",
            activity_name=f"{prefix}-data-masking-process-activity"
        )
        lambda_invoke = lamb.Function(
            self,
            f"{prefix}-data-masking-process-invoke",
            function_name=f"{prefix}-data-masking-process-invoke",
            code=lamb.Code.from_asset(path="./src/lambda"),
            handler="invoke.invoke",
            runtime=lamb.Runtime.PYTHON_3_8,
            environment={
                "REGION": region,
                "ACTIVITY_ARN": process_activity.activity_arn
            }
        )
        task_definition = ecs.FargateTaskDefinition(
            self,
            f"{prefix}-data-masking-process-task",
            cpu=1024,
            memory_limit_mib=2048
        )
        contaniner_definition = task_definition.add_container(
            f"{prefix}-data-masking-process-container",
            image=ecs.ContainerImage.from_asset(
                directory=f"{os.path.dirname(os.path.realpath(__file__))}/../src/image"
            ),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=f"{prefix}-data-masking-process-logs",
                log_retention=logs.RetentionDays.TWO_WEEKS
            )
        )
        parallel = sfn.Parallel(self, f"{prefix}-invoke-and-wait").branch(
            sfnt.StepFunctionsInvokeActivity(
                self,
                f"{prefix}-wait",
                activity=process_activity,
                timeout=cdk.Duration.hours(1)
            ),
            sfnt.LambdaInvoke(
                self,
                f"{prefix}-invoke",
                lambda_function=lambda_invoke,
                payload_response_only=True
            ).next(
                sfnt.EcsRunTask(
                    self,
                    f"{prefix}-process",
                    cluster=ecs.Cluster(
                        self,
                        f"{prefix}-data-masking-process-cluster",
                        cluster_name=f"{prefix}-data-masking-process-cluster",
                        vpc=ec2.Vpc.from_lookup(
                            self,
                            f"{prefix}-data-masking-process-vpc",
                            vpc_name="AppVPC"
                        )
                    ),
                    task_definition=task_definition,
                    launch_target=sfnt.EcsFargateLaunchTarget(
                        platform_version=ecs.FargatePlatformVersion.LATEST
                    ),
                    assign_public_ip=True,
                    container_overrides=[
                        sfnt.ContainerOverride(
                            container_definition=contaniner_definition,
                            environment=[
                                sfnt.TaskEnvironmentVariable(
                                    name="REGION",
                                    value=region
                                ),
                                sfnt.TaskEnvironmentVariable(
                                    name="BUCKET",
                                    value=sfn.JsonPath.string_at("$.bucket")
                                ),
                                sfnt.TaskEnvironmentVariable(
                                    name="KEY",
                                    value=sfn.JsonPath.string_at("$.key")
                                ),
                                sfnt.TaskEnvironmentVariable(
                                    name="TASK_TOKEN",
                                    value=sfn.JsonPath.string_at("$.taskToken")
                                )
                            ]
                        )
                    ]
                )
            )
        )
        fsm = sfn.StateMachine(
            self,
            f"{prefix}-data-masking-process-fsm",
            state_machine_name=f"{prefix}-data-masking-process-fsm",
            definition=parallel.next(
                sfn.Succeed(
                    self,
                    f"{prefix}-succeed"
                )
            )
        )
        self.processFsmArn = fsm.state_machine_arn
        # permission ?
        lambda_invoke.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AWSStepFunctionsFullAccess"
            )
        )
        task_definition.execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonS3FullAccess"
            )
        )
        task_definition.execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AWSStepFunctionsFullAccess"
            )
        )
        task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonS3FullAccess"
            )
        )
        task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AWSStepFunctionsFullAccess"
            )
        )
