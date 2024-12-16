from aws_cdk import (
    Stack,
    aws_events_targets as targets,
    aws_events as events,
    aws_lambda as _lambda,
    aws_sqs as sqs, Duration,
    aws_iam as iam,
    aws_pipes as pipes,
    CfnOutput,
)
import json
import os
from constructs import Construct


class SubmissionExecutionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        env = kwargs.get("env")
        print("Executing CDK synth with env: ", env)
        account_id = env.account

        ###############      Resources      ########################################

        # Define sqs queue for submissions. To be consumed by event bus
        submissions_queue = sqs.Queue(
            self, "UserSubmissions",
            content_based_deduplication=True,
            queue_name="UserSubmissions.fifo",
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            fifo=True,
            #retention_period=Duration.seconds(60),
            #visibility_timeout=Duration.seconds(15),
            #max_message_size_bytes=
            #enforce_ssl=
        )

        # Define sqs queue for results output by code execution lambda
        # to be consumed by code-engine service
        results_queue = sqs.Queue(
            self, "UserResults",
            content_based_deduplication=True,
            queue_name="UserResults.fifo",
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            fifo=True,
            # retention_period=Duration.seconds(60),
            #visibility_timeout=Duration.seconds(15),
            #max_message_size_bytes=
            #enforce_ssl=
        )

        # Define lambda for executing python user submitted code
        python_submission_lambda = _lambda.Function(
            self, "Python Execution Handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset('submission_execution/lambda'),
            handler='python_handler.handler',
            environment={
                "RESULTS_QUEUE": results_queue.queue_url,
            },
        )

        # TODO: Define more language lambdas here

        # Define event bus for incoming user submissions from code-engine
        # to lambda handlers
        submissions_bus = events.EventBus(
            self, "CodeSubmissionsBus",
            event_bus_name="CodeSubmissionsBus",

        )

        # Event bridge rule will forward only events with language=Python3 to python lambda
        python_exec_rule = events.Rule(
            self, "PythonSubmissionRule",
            event_bus=submissions_bus,
            event_pattern=events.EventPattern(account=[account_id]),
            targets=[targets.LambdaFunction(python_submission_lambda)]
        )

        # all_events_rule = events.Rule(
        #     self, "PythonSubmissionRule",
        #     event_bus=submissions_bus,
        #     event_pattern=events.EventPattern(account=[""]),
        #     targets=[targets.LambdaFunction(python_submission_lambda)]
        # )


        # TODO: Add event rules for other languages here

        # Create role for pipe to assume and add policies to that role
        sqs_bus_pipe_role = iam.Role(
            self, 'sqs-bus-pipe-role',
            assumed_by=iam.ServicePrincipal('pipes.amazonaws.com')
        )

        # Input transformer transforms sqs event by mapping json attributes before
        # sending to the event bus
        pipe_input_transformer = {
            "id": "<$.messageId>",
            "detail": "<$.body>",
            "time": "<aws.pipes.event.ingestion-time>",
            "region": "<$.awsRegion>",
            "source": "<$.eventSource>",
            "resources": ["<$.eventSourceARN>"],
            "detail-type": "codeSubmission",
            "account": account_id
        }
        pipe_input_transformer = json.dumps(pipe_input_transformer)

        # Create cloud formation pipe to poll user submissions queue and
        # forward to the event bus.
        sqs_bus_pipe = pipes.CfnPipe(
            self, "sqsToBusPipe", source=submissions_queue.queue_arn,
            role_arn=sqs_bus_pipe_role.role_arn,
            source_parameters=pipes.CfnPipe.PipeSourceParametersProperty(
                sqs_queue_parameters=pipes.CfnPipe.PipeSourceSqsQueueParametersProperty(
                    batch_size=1
                )
            ),
            target=submissions_bus.event_bus_arn,
            target_parameters=pipes.CfnPipe.PipeTargetParametersProperty(
                event_bridge_event_bus_parameters=pipes.CfnPipe.PipeTargetEventBridgeEventBusParametersProperty(
                ),
                input_template=pipe_input_transformer
            )

        )

        # OPTIONALLY ADD 'ENRICHMENT' TO PIPE TO TRANSFORM EVENT USING A LAMBDA

        ##############      Permissions     #######################################

        # Grant python3 lambda ability to send messages to results queue
        results_queue.grant_send_messages(python_submission_lambda)

        # TODO: grant permissions to other languages lambdas here

        # Create iam policy to allow pipe to consume from submissions queue
        pipe_queue_source_policy = iam.PolicyStatement(
            actions=['sqs:ReceiveMessage', 'sqs:DeleteMessage', 'sqs:GetQueueAttributes'],
            resources=[submissions_queue.queue_arn],
            effect=iam.Effect.ALLOW
        )

        # Create iam policy to allow pipe to put events in event bus
        pipe_bus_target_policy = iam.PolicyStatement(
            actions=['events:PutEvents'],
            resources=[submissions_bus.event_bus_arn],
            effect=iam.Effect.ALLOW,
        )

        sqs_bus_pipe_role.add_to_policy(pipe_bus_target_policy)
        sqs_bus_pipe_role.add_to_policy(pipe_queue_source_policy)


        # Grant lambda ability to send messages to results queue
        results_queue.grant_send_messages(python_submission_lambda)

        # TODO: Grant  send messages to other languages lambdas here

        # Output some variables
        CfnOutput(self, "SubmissionsQueueUrl", value=submissions_queue.queue_url)
        CfnOutput(self, "ResultsQueueUrl", value=results_queue.queue_url)

