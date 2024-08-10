import aws_cdk as core
import aws_cdk.assertions as assertions

from code_engine_cdk.code_engine_cdk_stack import CodeEngineCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in code_engine_cdk/code_engine_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CodeEngineCdkStack(app, "code-engine-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
