# filepath: c:\Agents-for-python\test_samples\app_style\shared\github_api_client.py
import aiohttp
from typing import List, Dict, Any


class PullRequest:
    """
    Represents a GitHub pull request.
    """

    def __init__(self, id: int, title: str, url: str):
        self.id = id
        self.title = title
        self.url = url

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "title": self.title, "url": self.url}


async def get_current_profile(token: str) -> Dict[str, Any]:
    """
    Get information about the current authenticated user.
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentsSDKDemo",
            "Content-Type": "application/json",
        }
        async with session.get(
            "https://api.github.com/user", headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "displayName": data.get("name", ""),
                    "mail": data.get("html_url", ""),
                    "jobTitle": "",
                    "givenName": data.get("login", ""),
                    "surname": "",
                    "imageUri": data.get("avatar_url", ""),
                }
            else:
                error_text = await response.text()
                raise Exception(
                    f"Error fetching user profile: {response.status} - {error_text}"
                )


async def get_pull_requests(owner: str, repo: str, token: str) -> List[PullRequest]:
    """
    Get pull requests for a specific repository.
    """
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "test-agent",
        }
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return [
                    PullRequest(
                        id=pr.get("id"),
                        title=pr.get("title"),
                        url=pr.get("htmlUrl"),
                    )
                    for pr in data[-5:-1]
                ]
            else:
                error_text = await response.text()
                raise Exception(
                    f"Error fetching pull requests: {response.status} - {error_text}"
                )
