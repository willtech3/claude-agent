import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.providers.base import Repository, Issue, PullRequest


@pytest.mark.asyncio
async def test_list_git_providers(client: AsyncClient, auth_headers: dict):
    """Test listing available git providers"""
    response = await client.get("/api/git-providers/", headers=auth_headers)
    assert response.status_code == 200
    providers = response.json()
    assert len(providers) == 3
    assert providers[0]["id"] == "github"
    assert providers[0]["enabled"] is True


@pytest.mark.asyncio
async def test_list_repositories(client: AsyncClient, auth_headers: dict):
    """Test listing repositories for a provider"""
    mock_repos = [
        Repository(
            id="123",
            name="test-repo",
            full_name="user/test-repo",
            description="Test repository",
            private=False,
            default_branch="main",
            url="https://github.com/user/test-repo",
            clone_url="https://github.com/user/test-repo.git"
        )
    ]
    
    with patch("app.api.git_providers.get_provider") as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.list_repositories.return_value = mock_repos
        mock_get_provider.return_value = mock_provider
        
        response = await client.get(
            "/api/git-providers/github/repositories",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        repos = response.json()
        assert len(repos) == 1
        assert repos[0]["name"] == "test-repo"


@pytest.mark.asyncio
async def test_get_repository(client: AsyncClient, auth_headers: dict):
    """Test getting a specific repository"""
    mock_repo = Repository(
        id="123",
        name="test-repo",
        full_name="user/test-repo",
        description="Test repository",
        private=False,
        default_branch="main",
        url="https://github.com/user/test-repo",
        clone_url="https://github.com/user/test-repo.git"
    )
    
    with patch("app.api.git_providers.get_provider") as mock_get_provider:
        mock_provider = AsyncMock()
        mock_provider.get_repository.return_value = mock_repo
        mock_get_provider.return_value = mock_provider
        
        response = await client.get(
            "/api/git-providers/github/repositories/user/test-repo",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        repo = response.json()
        assert repo["name"] == "test-repo"
        assert repo["full_name"] == "user/test-repo"


@pytest.mark.asyncio
async def test_invalid_provider(client: AsyncClient, auth_headers: dict):
    """Test invalid provider returns 400"""
    response = await client.get(
        "/api/git-providers/invalid/repositories",
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "Invalid provider" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unimplemented_provider(client: AsyncClient, auth_headers: dict):
    """Test unimplemented provider returns 501"""
    response = await client.get(
        "/api/git-providers/gitlab/repositories",
        headers=auth_headers
    )
    assert response.status_code == 501
    assert "not implemented" in response.json()["detail"]