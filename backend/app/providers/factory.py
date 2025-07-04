from typing import Dict, Any
from enum import Enum

from app.providers.base import GitProvider
from app.providers.github import GitHubProvider


class ProviderType(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class ProviderConfig:
    """Configuration for a git provider"""
    def __init__(self, provider_type: ProviderType, **kwargs):
        self.type = provider_type
        self.config = kwargs


def get_git_provider(config: ProviderConfig) -> GitProvider:
    """Factory function to create git provider instances"""
    if config.type == ProviderType.GITHUB:
        return GitHubProvider(
            token=config.config.get("token"),
            base_url=config.config.get("base_url", "https://api.github.com")
        )
    elif config.type == ProviderType.GITLAB:
        # TODO: Implement GitLabProvider
        raise NotImplementedError("GitLab provider not yet implemented")
    elif config.type == ProviderType.BITBUCKET:
        # TODO: Implement BitbucketProvider
        raise NotImplementedError("Bitbucket provider not yet implemented")
    else:
        raise ValueError(f"Unknown provider type: {config.type}")