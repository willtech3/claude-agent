#!/bin/bash
# LocalStack initialization script
# This script runs when LocalStack is ready

echo "Initializing LocalStack AWS resources..."

# Create SQS queue for tasks
aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name tasks \
    --attributes VisibilityTimeout=300,MessageRetentionPeriod=1209600

# Create S3 bucket for artifacts
aws --endpoint-url=http://localhost:4566 s3 mb s3://claude-agent-artifacts

# Create S3 bucket for workspaces
aws --endpoint-url=http://localhost:4566 s3 mb s3://claude-agent-workspaces

echo "LocalStack initialization complete!"