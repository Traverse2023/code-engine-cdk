import json

def handler(event, context):
    print("Python code execution handler running...")

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type', 'text/plain'
        },
        'body': "Hello"
    }
