"""GitHub check tool - Quick overview of public repositories.

Automatically fetches repo info + README when given a URL or owner/repo.
No authentication required.
"""

import json
import re
from typing import Any, Optional

import httpx

from light_agent.agent.tools.base import Tool


class GitHubCheckTool(Tool):
    """Quick overview of GitHub repositories. Auto-fetches info + README."""

    BASE_URL = "https://api.github.com"

    @property
    def name(self) -> str:
        return "github_check"

    @property
    def description(self) -> str:
        return "QUICK OVERVIEW of public GitHub repos. Auto-fetches repo info + README.md from URL or owner/repo. Best for: 'check repo_url', 'show me repo', 'what is repo'. No auth needed."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "GitHub repository URL (e.g., https://github.com/facebook/react) or owner/repo format",
                },
                "owner": {
                    "type": "string",
                    "description": "Repository owner (optional if repo_url provided)",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name (optional if repo_url provided)",
                },
                "include_readme": {
                    "type": "boolean",
                    "description": "Include README content (default: true)",
                },
                "max_readme_length": {
                    "type": "integer",
                    "description": "Max README characters (default: 3000)",
                },
            },
        }

    def _parse_url(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """Parse GitHub URL to (owner, repo)."""
        # Patterns:
        # https://github.com/owner/repo
        # github.com/owner/repo
        # owner/repo
        patterns = [
            r"github\.com/([^/]+)/([^/]+)/?",
            r"^([^/]+)/([^/]+)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)

        return None, None

    async def _request(self, endpoint: str) -> Optional[dict[str, Any]]:
        """Make a request to GitHub API."""
        url = f"{self.BASE_URL}/{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except Exception:
                return None

    async def _get_readme(self, owner: str, repo: str) -> str:
        """Get README content."""
        endpoint = f"repos/{owner}/{repo}/readme"
        url = f"{self.BASE_URL}/{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                if response.status_code == 404:
                    return ""
                response.raise_for_status()
                data = response.json()
                import base64

                content = data.get("content", "")
                if content:
                    return base64.b64decode(content).decode("utf-8", errors="replace")
                return ""
            except Exception:
                return ""

    async def execute(self, **kwargs: Any) -> str:
        """Execute github check."""
        repo_url = kwargs.get("repo_url", "")
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")
        include_readme = kwargs.get("include_readme", True)
        max_readme_length = kwargs.get("max_readme_length", 3000)

        # Parse URL if provided
        if repo_url and (not owner or not repo):
            owner, repo = self._parse_url(repo_url)

        if not owner or not repo:
            return "Error: Please provide a valid GitHub URL (e.g., https://github.com/owner/repo) or owner/repo"

        try:
            # Get repo info
            info = await self._request(f"repos/{owner}/{repo}")
            if not info:
                return f"Error: Repository not found: {owner}/{repo}"

            result = {
                "name": info.get("name"),
                "full_name": info.get("full_name"),
                "description": info.get("description"),
                "stars": info.get("stargazers_count"),
                "forks": info.get("forks_count"),
                "language": info.get("language"),
                "default_branch": info.get("default_branch"),
                "open_issues": info.get("open_issues_count"),
                "license": info.get("license", {}).get("name") if info.get("license") else None,
                "topics": info.get("topics", []),
                "url": f"https://github.com/{owner}/{repo}",
            }

            # Get README if requested
            if include_readme:
                readme = await self._get_readme(owner, repo)
                if readme:
                    result["readme_preview"] = readme[:max_readme_length]
                    if len(readme) > max_readme_length:
                        result["readme_truncated"] = True
                else:
                    result["readme"] = None

            # Get file count estimate
            tree = await self._request(f"repos/{owner}/{repo}/git/trees/main?recursive=1")
            if tree and not tree.get("truncated", True):
                file_count = len(tree.get("tree", []))
                result["file_count"] = file_count
            elif tree and tree.get("truncated"):
                result["file_count"] = "100+"

            return json.dumps(result, indent=2, ensure_ascii=False)

        except Exception as e:
            return f"Error: {str(e)}"
