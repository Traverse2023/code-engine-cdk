from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_sqs as sqs,
)
from constructs import Construct

class CodeEngineCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Defined lambda for executing python user submitted code
        python_execution = _lambda.Function(
            self, "Python Execution Handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset('submission_lambda'),
            handler='python_handler.py',
        )

        # Define sqs queue for incoming user submissions from code-engine 
        # to lambda handlers 
            user_submission_queue = sqs.
        # Define sqs queue for results output by code execution lambda 
        # to be consumed by code-engine service

