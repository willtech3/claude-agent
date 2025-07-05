
from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.auth import oauth2_scheme
from app.core.config import get_settings
from app.providers.base import GitProvider, Issue, PullRequest, Repository
from app.providers.factory import ProviderConfig, ProviderType, get_git_provider

router = APIRouter()
settings = get_settings()


async def get_provider(
    provider_id: str,
    x_provider_token: str | None = Header(None),
    user_token: str = Depends(oauth2_scheme)
) -> GitProvider:
    """Get provider instance based on provider ID"""
    try:
        provider_type = ProviderType(provider_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider_id}")

    # Use provided token or fall back to settings
    token = x_provider_token
    if not token:
        if provider_id == "github":
            token = settings.GITHUB_TOKEN
        elif provider_id == "gitlab":
            token = settings.GITLAB_TOKEN
        else:
            raise HTTPException(status_code=400, detail=f"No token configured for {provider_id}")

    config = ProviderConfig(provider_type, token=token)

    try:
        return get_git_provider(config)
    except NotImplementedError:
        raise HTTPException(status_code=501, detail=f"Provider {provider_id} not implemented")


@router.get("/")
async def list_git_providers(token: str = Depends(oauth2_scheme)):
    """List available git providers"""
    return [
        {"id": "github", "name": "GitHub", "enabled": True},
        {"id": "gitlab", "name": "GitLab", "enabled": False},
        {"id": "bitbucket", "name": "Bitbucket", "enabled": False}
    ]


@router.get("/{provider_id}/repositories", response_model=list[Repository])
async def list_repositories(
    provider_id: str,
    user_id: str | None = None,
    x_provider_token: str | None = Header(None),
    token: str = Depends(oauth2_scheme)
):
    """List repositories for a provider"""
    provider = await get_provider(provider_id, x_provider_token, token)
    return await provider.list_repositories(user_id)


@router.get("/{provider_id}/repositories/{owner}/{repo}", response_model=Repository)
async def get_repository(
    provider_id: str,
    owner: str,
    repo: str,
    x_provider_token: str | None = Header(None),
    token: str = Depends(oauth2_scheme)
):
    """Get repository details"""
    provider = await get_provider(provider_id, x_provider_token, token)
    repo_id = f"{owner}/{repo}"
    return await provider.get_repository(repo_id)


@router.get("/{provider_id}/repositories/{owner}/{repo}/issues", response_model=list[Issue])
async def list_issues(
    provider_id: str,
    owner: str,
    repo: str,
    state: str = "open",
    x_provider_token: str | None = Header(None),
    token: str = Depends(oauth2_scheme)
):
    """List issues for a repository"""
    provider = await get_provider(provider_id, x_provider_token, token)
    repo_id = f"{owner}/{repo}"
    return await provider.list_issues(repo_id, state)


@router.get("/{provider_id}/repositories/{owner}/{repo}/issues/{issue_number}", response_model=Issue)
async def get_issue(
    provider_id: str,
    owner: str,
    repo: str,
    issue_number: int,
    x_provider_token: str | None = Header(None),
    token: str = Depends(oauth2_scheme)
):
    """Get issue details"""
    provider = await get_provider(provider_id, x_provider_token, token)
    repo_id = f"{owner}/{repo}"
    return await provider.get_issue(repo_id, issue_number)


@router.get("/{provider_id}/repositories/{owner}/{repo}/pulls", response_model=list[PullRequest])
async def list_pull_requests(
    provider_id: str,
    owner: str,
    repo: str,
    state: str = "open",
    x_provider_token: str | None = Header(None),
    token: str = Depends(oauth2_scheme)
):
    """List pull requests for a repository"""
    provider = await get_provider(provider_id, x_provider_token, token)
    repo_id = f"{owner}/{repo}"
    return await provider.list_pull_requests(repo_id, state)


@router.get("/{provider_id}/repositories/{owner}/{repo}/pulls/{pr_number}", response_model=PullRequest)
async def get_pull_request(
    provider_id: str,
    owner: str,
    repo: str,
    pr_number: int,
    x_provider_token: str | None = Header(None),
    token: str = Depends(oauth2_scheme)
):
    """Get pull request details"""
    provider = await get_provider(provider_id, x_provider_token, token)
    repo_id = f"{owner}/{repo}"
    return await provider.get_pull_request(repo_id, pr_number)
