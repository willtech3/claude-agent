#!/usr/bin/env python3

import asyncio
import json
import os
import sys
import logging
from typing import Optional

import boto3
import redis.asyncio as redis

from .claude_code import MinimalClaudeWrapper
from .sqs_handler import SQSHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the Claude Code wrapper."""
    
    # Configuration from environment
    sqs_queue_url = os.getenv("SQS_QUEUE_URL")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    aws_endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    
    if not sqs_queue_url:
        logger.error("SQS_QUEUE_URL environment variable is required")
        sys.exit(1)
    
    # Initialize Redis connection
    redis_client = await redis.from_url(redis_url)
    
    # Initialize SQS client
    sqs_kwargs = {}
    if aws_endpoint_url:
        sqs_kwargs["endpoint_url"] = aws_endpoint_url
    
    sqs_client = boto3.client("sqs", **sqs_kwargs)
    
    # Initialize components
    claude_wrapper = MinimalClaudeWrapper(redis_client)
    sqs_handler = SQSHandler(sqs_client, sqs_queue_url, claude_wrapper)
    
    # Start processing tasks
    logger.info("Starting Claude Code wrapper...")
    logger.info(f"SQS Queue URL: {sqs_queue_url}")
    logger.info(f"Redis URL: {redis_url}")
    
    try:
        await sqs_handler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())