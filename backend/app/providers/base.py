from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class Repository(BaseModel):
    id: str
    name: str
    full_name: str
    description: str | None = None
    private: bool
    default_branch: str
    url: str
    clone_url: str


class Issue(BaseModel):
    id: str
    number: int
    title: str
    body: str
    state: str
    author: str
    labels: list[str]
    created_at: datetime
    updated_at: datetime


class PullRequest(BaseModel):
    id: str
    number: int
    title: str
    body: str
    state: str
    source_branch: str
    target_branch: str
    author: str
    created_at: datetime
    updated_at: datetime


class GitProvider(Protocol):
    """Protocol for Git provider implementations"""

    async def get_repository(self, repo_id: str) -> Repository:
        """Get repository information"""
        ...

    async def list_repositories(self, user_id: str | None = None) -> list[Repository]:
        """List repositories for a user or organization"""
        ...

    async def get_issue(self, repo_id: str, issue_number: int) -> Issue:
        """Get issue details"""
        ...

    async def list_issues(self, repo_id: str, state: str = "open") -> list[Issue]:
        """List issues for a repository"""
        ...

    async def create_pull_request(
        self,
        repo_id: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str
    ) -> PullRequest:
        """Create a new pull request"""
        ...

    async def get_pull_request(self, repo_id: str, pr_number: int) -> PullRequest:
        """Get pull request details"""
        ...

    async def list_pull_requests(self, repo_id: str, state: str = "open") -> list[PullRequest]:
        """List pull requests for a repository"""
        ...
