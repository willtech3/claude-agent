import os
from typing import Optional
from pydantic import BaseSettings, Field


class AgentConfig(BaseSettings):
    # Claude authentication
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    claude_model: str = Field("claude-3-sonnet-20240229", env="CLAUDE_MODEL")
    
    # AWS configuration
    aws_endpoint_url: Optional[str] = Field(None, env="AWS_ENDPOINT_URL")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    
    # SQS configuration
    sqs_queue_url: Optional[str] = Field(None, env="SQS_QUEUE_URL")
    sqs_result_queue_url: Optional[str] = Field(None, env="SQS_RESULT_QUEUE_URL")
    max_task_retries: int = Field(3, env="MAX_TASK_RETRIES")
    
    # S3 configuration
    s3_bucket_name: str = Field("claude-agent-artifacts", env="S3_BUCKET_NAME")
    
    # Redis configuration
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # GitHub configuration
    gh_token: Optional[str] = Field(None, env="GH_TOKEN")
    
    # Session configuration
    session_base_dir: str = Field("/tmp/claude-sessions", env="SESSION_BASE_DIR")
    artifacts_base_dir: str = Field("/tmp/claude-artifacts", env="ARTIFACTS_BASE_DIR")
    
    # Agent configuration
    max_concurrent_tasks: int = Field(5, env="MAX_CONCURRENT_TASKS")
    task_timeout_seconds: int = Field(3600, env="TASK_TIMEOUT_SECONDS")  # 1 hour
    
    # Application configuration
    port: int = Field(8080, env="PORT")
    environment: str = Field("production", env="ENV")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global config instance
config = AgentConfig()