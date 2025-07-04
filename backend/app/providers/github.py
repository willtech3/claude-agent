from typing import Dict, List, Optional
import httpx
from datetime import datetime

from app.providers.base import GitProvider, Repository, Issue, PullRequest


class GitHubProvider(GitProvider):
    """GitHub provider implementation"""
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_repository(self, repo_id: str) -> Repository:
        """Get repository information from GitHub"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            return Repository(
                id=str(data["id"]),
                name=data["name"],
                full_name=data["full_name"],
                description=data.get("description"),
                private=data["private"],
                default_branch=data["default_branch"],
                url=data["html_url"],
                clone_url=data["clone_url"]
            )
    
    async def list_repositories(self, user_id: Optional[str] = None) -> List[Repository]:
        """List repositories for authenticated user or specified user"""
        async with httpx.AsyncClient() as client:
            if user_id:
                url = f"{self.base_url}/users/{user_id}/repos"
            else:
                url = f"{self.base_url}/user/repos"
            
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            repos = []
            for data in response.json():
                repos.append(Repository(
                    id=str(data["id"]),
                    name=data["name"],
                    full_name=data["full_name"],
                    description=data.get("description"),
                    private=data["private"],
                    default_branch=data["default_branch"],
                    url=data["html_url"],
                    clone_url=data["clone_url"]
                ))
            
            return repos
    
    async def get_issue(self, repo_id: str, issue_number: int) -> Issue:
        """Get issue details from GitHub"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo_id}/issues/{issue_number}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            return Issue(
                id=str(data["id"]),
                number=data["number"],
                title=data["title"],
                body=data["body"] or "",
                state=data["state"],
                author=data["user"]["login"],
                labels=[label["name"] for label in data["labels"]],
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            )
    
    async def list_issues(self, repo_id: str, state: str = "open") -> List[Issue]:
        """List issues for a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo_id}/issues",
                headers=self.headers,
                params={"state": state}
            )
            response.raise_for_status()
            
            issues = []
            for data in response.json():
                # Skip pull requests (GitHub returns them in issues endpoint)
                if "pull_request" in data:
                    continue
                    
                issues.append(Issue(
                    id=str(data["id"]),
                    number=data["number"],
                    title=data["title"],
                    body=data["body"] or "",
                    state=data["state"],
                    author=data["user"]["login"],
                    labels=[label["name"] for label in data["labels"]],
                    created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                ))
            
            return issues
    
    async def create_pull_request(
        self, 
        repo_id: str,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str
    ) -> PullRequest:
        """Create a new pull request on GitHub"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{repo_id}/pulls",
                headers=self.headers,
                json={
                    "title": title,
                    "body": body,
                    "head": source_branch,
                    "base": target_branch
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return PullRequest(
                id=str(data["id"]),
                number=data["number"],
                title=data["title"],
                body=data["body"] or "",
                state=data["state"],
                source_branch=data["head"]["ref"],
                target_branch=data["base"]["ref"],
                author=data["user"]["login"],
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            )
    
    async def get_pull_request(self, repo_id: str, pr_number: int) -> PullRequest:
        """Get pull request details from GitHub"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo_id}/pulls/{pr_number}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            return PullRequest(
                id=str(data["id"]),
                number=data["number"],
                title=data["title"],
                body=data["body"] or "",
                state=data["state"],
                source_branch=data["head"]["ref"],
                target_branch=data["base"]["ref"],
                author=data["user"]["login"],
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            )
    
    async def list_pull_requests(self, repo_id: str, state: str = "open") -> List[PullRequest]:
        """List pull requests for a repository"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo_id}/pulls",
                headers=self.headers,
                params={"state": state}
            )
            response.raise_for_status()
            
            prs = []
            for data in response.json():
                prs.append(PullRequest(
                    id=str(data["id"]),
                    number=data["number"],
                    title=data["title"],
                    body=data["body"] or "",
                    state=data["state"],
                    source_branch=data["head"]["ref"],
                    target_branch=data["base"]["ref"],
                    author=data["user"]["login"],
                    created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                ))
            
            return prs