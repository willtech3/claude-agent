import pytest
import os
from unittest.mock import patch

from agent.config import AgentConfig


class TestAgentConfig:
    def test_default_values(self):
        # Test with minimal environment
        with patch.dict(os.environ, {}, clear=True):
            config = AgentConfig()
            
            # Check defaults
            assert config.anthropic_api_key is None
            assert config.claude_model == "claude-3-sonnet-20240229"
            assert config.aws_region == "us-east-1"
            assert config.max_task_retries == 3
            assert config.s3_bucket_name == "claude-agent-artifacts"
            assert config.session_base_dir == "/tmp/claude-sessions"
            assert config.max_concurrent_tasks == 5
            assert config.task_timeout_seconds == 3600
            assert config.port == 8080
            assert config.environment == "production"
            assert config.log_level == "INFO"
            
    def test_env_var_loading(self):
        # Test environment variable loading
        env_vars = {
            "ANTHROPIC_API_KEY": "test-key",
            "CLAUDE_MODEL": "claude-3-opus",
            "AWS_ENDPOINT_URL": "http://localstack:4566",
            "AWS_REGION": "eu-west-1",
            "SQS_QUEUE_URL": "http://queue-url",
            "SQS_RESULT_QUEUE_URL": "http://result-queue-url",
            "MAX_TASK_RETRIES": "5",
            "S3_BUCKET_NAME": "test-bucket",
            "REDIS_URL": "redis://redis:6379",
            "GH_TOKEN": "github-token",
            "SESSION_BASE_DIR": "/custom/sessions",
            "MAX_CONCURRENT_TASKS": "10",
            "TASK_TIMEOUT_SECONDS": "7200",
            "PORT": "8000",
            "ENV": "development",
            "LOG_LEVEL": "DEBUG"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AgentConfig()
            
            assert config.anthropic_api_key == "test-key"
            assert config.claude_model == "claude-3-opus"
            assert config.aws_endpoint_url == "http://localstack:4566"
            assert config.aws_region == "eu-west-1"
            assert config.sqs_queue_url == "http://queue-url"
            assert config.sqs_result_queue_url == "http://result-queue-url"
            assert config.max_task_retries == 5
            assert config.s3_bucket_name == "test-bucket"
            assert config.redis_url == "redis://redis:6379"
            assert config.gh_token == "github-token"
            assert config.session_base_dir == "/custom/sessions"
            assert config.max_concurrent_tasks == 10
            assert config.task_timeout_seconds == 7200
            assert config.port == 8000
            assert config.environment == "development"
            assert config.log_level == "DEBUG"
            
    def test_optional_fields(self):
        # Test that optional fields can be None
        with patch.dict(os.environ, {}, clear=True):
            config = AgentConfig()
            
            assert config.anthropic_api_key is None
            assert config.aws_endpoint_url is None
            assert config.aws_access_key_id is None
            assert config.aws_secret_access_key is None
            assert config.sqs_queue_url is None
            assert config.sqs_result_queue_url is None
            assert config.redis_url is None
            assert config.gh_token is None
            
    def test_type_conversion(self):
        # Test integer type conversion
        env_vars = {
            "MAX_TASK_RETRIES": "10",
            "MAX_CONCURRENT_TASKS": "20",
            "TASK_TIMEOUT_SECONDS": "1800",
            "PORT": "9000"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AgentConfig()
            
            assert isinstance(config.max_task_retries, int)
            assert config.max_task_retries == 10
            assert isinstance(config.max_concurrent_tasks, int)
            assert config.max_concurrent_tasks == 20
            assert isinstance(config.task_timeout_seconds, int)
            assert config.task_timeout_seconds == 1800
            assert isinstance(config.port, int)
            assert config.port == 9000
            
    def test_case_insensitive(self):
        # Pydantic settings should be case-insensitive for env vars
        env_vars = {
            "anthropic_api_key": "lower-case-key",
            "CLAUDE_MODEL": "upper-case-model"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AgentConfig()
            
            assert config.anthropic_api_key == "lower-case-key"
            assert config.claude_model == "upper-case-model"