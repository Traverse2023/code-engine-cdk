#!/usr/bin/env python3
import os

import aws_cdk as cdk

from submission_execution.submission_execution_stack import SubmissionExecutionStack


app = cdk.App()
SubmissionExecutionStack(app, "CodeEngineCdkStack",
                         env=cdk.Environment(
                             account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                             region=os.getenv('CDK_DEFAULT_REGION')),
                         )

app.synth()
