#!/usr/bin/env python3
"""Test script to send a task to the Claude wrapper via SQS."""

import json
import boto3
import time
import os

def send_test_task():
    # Configure SQS client
    sqs = boto3.client(
        'sqs',
        endpoint_url=os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566'),
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    # Get queue URL
    queue_url = os.getenv('SQS_QUEUE_URL', 'http://localhost:4566/000000000000/tasks')
    
    # Create test message
    message = {
        "task_id": "test-task-001",
        "prompt": "Create a simple hello world Python script that prints the current date and time"
    }
    
    # Send message
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )
    
    print(f"Sent test task: {message['task_id']}")
    print(f"MessageId: {response['MessageId']}")
    
    # Instructions for monitoring
    print("\nTo monitor the output, run:")
    print(f"redis-cli subscribe 'task:{message['task_id']}'")

if __name__ == "__main__":
    send_test_task()