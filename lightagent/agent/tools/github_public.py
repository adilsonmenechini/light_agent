"""GitHub public API tool without authentication.

Uses GitHub's public REST API for basic operations on public repositories.
Rate limited to 60 requests/hour from same IP.
"""

import json
from typing import Any

import httpx

from lightagent.agent.tools.base import Tool


class GitHubPublicTool(Tool):
    """Access public GitHub repositories WITHOUT authentication. DEFAULT choice for reading public repos."""

    BASE_URL = "https://api.github.com"

    @property
    def name(self) -> str:
        return "github_public"

    @property
    def description(self) -> str:
        return "DEFAULT TOOL for accessing public GitHub repos WITHOUT authentication. Use for: repo_info, repo_contents (list files), repo_tree (all files), file_content (read files), search. Rate limited: 60 req/hour."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["repo_info", "repo_contents", "repo_tree", "file_content", "search"],
                    "description": "Action to perform",
                },
                "owner": {
                    "type": "string",
                    "description": "Repository owner (username or organization)",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path (for contents/tree actions)",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: default branch)",
                },
                "query": {
                    "type": "string",
                    "description": "Search query (for search action)",
                },
            },
            "required": ["action"],
        }

    async def _request(self, endpoint: str) -> Any:
        """Make a request to GitHub API."""
        url = f"{self.BASE_URL}/{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()

    async def _get_raw(self, url: str) -> str:
        """Get raw content from URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.text

    async def execute(self, **kwargs: Any) -> str:
        """Execute GitHub public API action."""
        action = kwargs.get("action")
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")

        try:
            if action == "repo_info":
                if not owner or not repo:
                    return "Error: owner and repo required"
                data = await self._request(f"repos/{owner}/{repo}")
                return json.dumps(
                    {
                        "name": data.get("name"),
                        "full_name": data.get("full_name"),
                        "description": data.get("description"),
                        "stars": data.get("stargazers_count"),
                        "forks": data.get("forks_count"),
                        "language": data.get("language"),
                        "default_branch": data.get("default_branch"),
                        "open_issues": data.get("open_issues_count"),
                    },
                    indent=2,
                )

            elif action == "repo_contents":
                if not owner or not repo:
                    return "Error: owner and repo required"
                path = kwargs.get("path", "")
                branch = kwargs.get("branch")
                endpoint = f"repos/{owner}/{repo}/contents/{path}"
                if branch:
                    endpoint += f"?ref={branch}"
                data = await self._request(endpoint)
                if isinstance(data, list):
                    # Directory listing
                    items: list[dict[str, Any]] = [
                        {
                            "name": item.get("name", ""),
                            "type": item.get("type", ""),
                            "size": item.get("size", 0),
                        }
                        for item in data
                    ]
                    return json.dumps(items, indent=2)
                else:
                    # Single file
                    return json.dumps(
                        {
                            "name": data.get("name"),
                            "path": data.get("path"),
                            "size": data.get("size"),
                            "type": data.get("type"),
                            "content": data.get("content", "")[:5000],
                        },
                        indent=2,
                    )

            elif action == "repo_tree":
                if not owner or not repo:
                    return "Error: owner and repo required"
                branch = kwargs.get("branch")
                # First get default branch
                if not branch:
                    info = await self._request(f"repos/{owner}/{repo}")
                    branch = info.get("default_branch", "main")
                # Get tree
                data = await self._request(f"repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
                if data.get("truncated"):
                    files = [item["path"] for item in data.get("tree", [])[:100]]
                    return json.dumps(
                        {"truncated": True, "files": files, "total": data.get("tree", [])},
                        indent=2,
                    )
                files = [item["path"] for item in data.get("tree", [])]
                return json.dumps({"truncated": False, "files": files}, indent=2)

            elif action == "file_content":
                if not owner or not repo or not kwargs.get("path"):
                    return "Error: owner, repo, and path required"
                branch = kwargs.get("branch")
                endpoint = f"repos/{owner}/{repo}/contents/{kwargs.get('path')}"
                if branch:
                    endpoint += f"?ref={branch}"
                data = await self._request(endpoint)
                import base64

                content = data.get("content", "")
                if content and data.get("encoding") == "base64":
                    try:
                        decoded = base64.b64decode(content).decode("utf-8")
                        return decoded
                    except Exception:
                        return "Error: Could not decode file content"
                return content[:10000]

            elif action == "search":
                query = kwargs.get("query", "")
                if not query:
                    return "Error: query required"
                data = await self._request(f"search/code?q={query}")
                items = [
                    {
                        "name": item["name"],
                        "path": item["path"],
                        "repo": item["repository"]["full_name"],
                    }
                    for item in data.get("items", [])[:10]
                ]
                return json.dumps({"total": data.get("total_count", 0), "results": items}, indent=2)

            return f"Error: Unknown action '{action}'"

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                return "Error: GitHub API rate limit exceeded. Try again later or use authenticated tool."
            elif e.response.status_code == 404:
                return f"Error: Repository or path not found: {owner}/{repo}"
            return f"Error: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
