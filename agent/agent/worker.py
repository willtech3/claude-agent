import asyncio
import os
from typing import Optional

import structlog
from redis import asyncio as aioredis

from agent.session import SessionManager
from agent.claude_code import ClaudeCodeWrapper
from agent.sqs_handler import SQSTaskHandler
from agent.config import config

logger = structlog.get_logger()


class AgentWorker:
    def __init__(self):
        self.running = False
        self.redis_client: Optional[aioredis.Redis] = None
        
        # Initialize components
        self.session_manager = SessionManager()
        self.claude_wrapper = ClaudeCodeWrapper(self.session_manager)
        self.sqs_handler = SQSTaskHandler(self.claude_wrapper)
        
    async def start(self):
        self.running = True
        logger.info("Starting agent worker")
        
        # Initialize connections
        await self._init_connections()
        
        # Start processing loop
        while self.running:
            try:
                await self._process_messages()
            except Exception as e:
                logger.error("Error processing messages", error=str(e))
                await asyncio.sleep(5)  # Back off on error
                
    async def stop(self):
        logger.info("Stopping agent worker")
        self.running = False
        
        # Close connections
        if self.redis_client:
            await self.redis_client.close()
            
    async def _init_connections(self):
        # Initialize Redis (optional, for caching/state)
        if config.redis_url:
            try:
                self.redis_client = await aioredis.from_url(config.redis_url)
                logger.info("Connected to Redis")
            except Exception as e:
                logger.warning("Failed to connect to Redis", error=str(e))
                
    async def _process_messages(self):
        # Receive messages from SQS
        messages = await self.sqs_handler.receive_messages()
        
        if not messages:
            # No messages, short sleep
            await asyncio.sleep(1)
            return
            
        # Process messages concurrently (up to a limit)
        tasks = []
        for message in messages[:5]:  # Process max 5 messages concurrently
            task = asyncio.create_task(self.sqs_handler.process_message(message))
            tasks.append(task)
            
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)