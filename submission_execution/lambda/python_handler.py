import json
import os

import boto3

def handler(event, context):
    print("Python code execution handler running...")

    # Initiate sqs client and get sqs que url from envs
    sqs = boto3.client('sqs')
    results_queue_url = os.getenv('RESULTS_QUEUE')


    # Send message to sqs
    sqs.send_message(
        QueueUrl=results_queue_url,
        MessageBody=(
            json.dumps(event)
        ),
        MessageGroupId="Python3"
    )

