#!/bin/bash

# Create SQS queue for tasks
awslocal sqs create-queue --queue-name tasks

echo "LocalStack initialization complete"