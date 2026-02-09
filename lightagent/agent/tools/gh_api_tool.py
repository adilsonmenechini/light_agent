"""GitHub CLI wrapper tool with JSON parsing."""

import asyncio
import json
from typing import Any, Optional

from lightagent.agent.tools.base import Tool


class GitHubTool(Tool):
    """GitHub operations using the gh CLI with automatic JSON parsing."""

    @property
    def name(self) -> str:
        return "github"

    @property
    def description(self) -> str:
        return "GitHub operations using gh CLI (REQUIRES authentication via gh auth). Use for: PRs, issues, releases, commits, and authenticated API calls. For public repo contents WITHOUT auth, use 'github_public' tool instead."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "pr_list",
                        "pr_view",
                        "pr_create",
                        "pr_merge",
                        "pr_close",
                        "pr_reopen",
                        "pr_diff",
                        "pr_checks",
                        "issue_list",
                        "issue_view",
                        "issue_create",
                        "issue_close",
                        "issue_reopen",
                        "issue_comment",
                        "release_list",
                        "release_view",
                        "release_create",
                        "release_download",
                        "run_list",
                        "run_view",
                        "run_rerun",
                        "run_cancel",
                        "repo_view",
                        "repo_list",
                        "repo_contents",
                        "api",
                    ],
                    "description": "The GitHub action to perform",
                },
                "owner": {
                    "type": "string",
                    "description": "Repository owner (default: detected from git remote)",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name (default: detected from git remote)",
                },
                "number": {
                    "type": "integer",
                    "description": "PR/issue/run number",
                },
                "title": {
                    "type": "string",
                    "description": "Title for PR/issue/release",
                },
                "body": {
                    "type": "string",
                    "description": "Body/description for PR/issue/release",
                },
                "base": {
                    "type": "string",
                    "description": "Base branch for PR",
                },
                "head": {
                    "type": "string",
                    "description": "Head branch for PR",
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Labels to add",
                },
                "assignees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Assignees to add",
                },
                "reviewers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Reviewers for PR",
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "State filter for lists",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                },
                "tag": {
                    "type": "string",
                    "description": "Release tag",
                },
                "draft": {
                    "type": "boolean",
                    "description": "Create as draft PR/release",
                },
                "prerelease": {
                    "type": "string",
                    "description": "Create as prerelease",
                },
                "workflow": {
                    "type": "string",
                    "description": "Workflow name/id",
                },
                "endpoint": {
                    "type": "string",
                    "description": "API endpoint for gh api action",
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PATCH", "PUT", "DELETE"],
                    "description": "HTTP method for API calls",
                },
                "fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fields to extract with --jq",
                },
                "raw": {
                    "type": "boolean",
                    "description": "Return raw output instead of JSON",
                },
            },
            "required": ["action"],
        }

    def _get_repo(self, owner: Optional[str], repo: Optional[str]) -> str:
        """Get repository string for gh commands."""
        if owner and repo:
            return f"{owner}/{repo}"
        return ""  # Will use current repo

    async def _run_gh(
        self,
        args: list[str],
        capture_output: bool = True,
        json_output: bool = True,
    ) -> tuple[int | None, str, str]:
        """Execute a gh command."""
        cmd = ["gh"] + args

        if json_output:
            cmd.extend(["--jq", "."])  # Enable JSON output

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
        )

        stdout = b""
        stderr = b""

        if capture_output:
            stdout, stderr = await process.communicate()

        return (
            process.returncode,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )

    async def _parse_json(self, output: str, fields: Optional[list[str]] = None) -> Any:
        """Parse JSON output and extract specific fields."""
        try:
            data = json.loads(output)
            if fields:
                result = {}
                for field in fields:
                    result[field] = data.get(field)
                return result
            return data
        except json.JSONDecodeError:
            return output

    async def execute(self, **kwargs: Any) -> str:
        """Execute the GitHub action."""
        action = kwargs.get("action")
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")
        repo_str = self._get_repo(owner, repo)
        repo_arg = ["--repo", repo_str] if repo_str else []

        # PR operations
        if action == "pr_list":
            state = kwargs.get("state", "open")
            limit = kwargs.get("limit", 10)
            args = [
                "pr",
                "list",
                "--state",
                state,
                "--limit",
                str(limit),
                "--json",
                "number,title,state,author,labels",
            ]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return await self._parse_json(stdout)

        elif action == "pr_view":
            number = kwargs.get("number")
            if not number:
                return "Error: PR number required"
            args = [
                "pr",
                "view",
                str(number),
                "--json",
                "number,title,state,body,author,additions,deletions,changedFiles",
            ]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return await self._parse_json(stdout)

        elif action == "pr_create":
            title = kwargs.get("title")
            body = kwargs.get("body", "")
            base = kwargs.get("base", "main")
            head = kwargs.get("head")
            draft = kwargs.get("draft", False)

            if not title:
                return "Error: PR title required"

            args = ["pr", "create", "--title", title, "--base", base]
            if body:
                args.extend(["--body", body])
            if head:
                args.extend(["--head", head])
            if draft:
                args.append("--draft")

            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ PR created: {stdout.strip()}"

        elif action == "pr_merge":
            number = kwargs.get("number")
            if not number:
                return "Error: PR number required"
            args = ["pr", "merge", str(number), "--squash", "--delete-branch"]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ PR #{number} merged"

        elif action == "pr_close":
            number = kwargs.get("number")
            if not number:
                return "Error: PR number required"
            args = ["pr", "close", str(number)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ PR #{number} closed"

        elif action == "pr_reopen":
            number = kwargs.get("number")
            if not number:
                return "Error: PR number required"
            args = ["pr", "reopen", str(number)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ PR #{number} reopened"

        elif action == "pr_diff":
            number = kwargs.get("number")
            if not number:
                return "Error: PR number required"
            args = ["pr", "diff", str(number)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout if stdout else "No changes"

        elif action == "pr_checks":
            number = kwargs.get("number")
            if not number:
                return "Error: PR number required"
            args = ["pr", "checks", str(number)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout if stdout else "No checks found"

        # Issue operations
        elif action == "issue_list":
            state = kwargs.get("state", "open")
            limit = kwargs.get("limit", 10)
            args = [
                "issue",
                "list",
                "--state",
                state,
                "--limit",
                str(limit),
                "--json",
                "number,title,state,author,labels",
            ]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return await self._parse_json(stdout)

        elif action == "issue_view":
            number = kwargs.get("number")
            if not number:
                return "Error: Issue number required"
            args = [
                "issue",
                "view",
                str(number),
                "--json",
                "number,title,state,body,author,labels,comments",
            ]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return await self._parse_json(stdout)

        elif action == "issue_create":
            title = kwargs.get("title")
            body = kwargs.get("body", "")
            labels = kwargs.get("labels", [])
            assignees = kwargs.get("assignees", [])

            if not title:
                return "Error: Issue title required"

            args = ["issue", "create", "--title", title]
            if body:
                args.extend(["--body", body])
            for label in labels:
                args.extend(["--label", label])
            for assignee in assignees:
                args.extend(["--assignee", assignee])

            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Issue created: {stdout.strip()}"

        elif action == "issue_close":
            number = kwargs.get("number")
            if not number:
                return "Error: Issue number required"
            args = ["issue", "close", str(number)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Issue #{number} closed"

        elif action == "issue_reopen":
            number = kwargs.get("number")
            if not number:
                return "Error: Issue number required"
            args = ["issue", "reopen", str(number)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Issue #{number} reopened"

        elif action == "issue_comment":
            number = kwargs.get("number")
            body = kwargs.get("body", "")

            if not number or not body:
                return "Error: Issue number and body required"
            args = ["issue", "comment", str(number), "--body", body]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Comment added to issue #{number}"

        # Release operations
        elif action == "release_list":
            limit = kwargs.get("limit", 10)
            args = [
                "release",
                "list",
                "--limit",
                str(limit),
                "--json",
                "tagName,name,prerelease,draft",
            ]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return await self._parse_json(stdout)

        elif action == "release_view":
            tag = kwargs.get("tag")
            if not tag:
                return "Error: Release tag required"
            args = ["release", "view", tag, "--json", "name,body,tagName,prerelease,draft,assets"]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return await self._parse_json(stdout)

        elif action == "release_create":
            tag = kwargs.get("tag")
            title = kwargs.get("title", tag)
            body = kwargs.get("body", "")
            draft = kwargs.get("draft", False)
            prerelease = kwargs.get("prerelease", False)

            if not tag:
                return "Error: Release tag required"

            args = ["release", "create", tag, "--title", title]
            if body:
                args.extend(["--notes", body])
            if draft:
                args.append("--draft")
            if prerelease:
                args.append("--prerelease")

            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Release {tag} created"

        elif action == "release_download":
            tag = kwargs.get("tag")
            if not tag:
                return "Error: Release tag required"
            args = ["release", "download", tag]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Downloaded assets for release {tag}"

        # Workflow run operations
        elif action == "run_list":
            limit = kwargs.get("limit", 10)
            workflow = kwargs.get("workflow")
            args = ["run", "list", "--limit", str(limit)]
            if workflow:
                args.extend(["--workflow", workflow])
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout

        elif action == "run_view":
            run_id = kwargs.get("number")
            if not run_id:
                return "Error: Run ID required"
            args = ["run", "view", str(run_id)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout

        elif action == "run_rerun":
            run_id = kwargs.get("number")
            if not run_id:
                return "Error: Run ID required"
            args = ["run", "rerun", str(run_id)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Run #{run_id} rerun"

        elif action == "run_cancel":
            run_id = kwargs.get("number")
            if not run_id:
                return "Error: Run ID required"
            args = ["run", "cancel", str(run_id)]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Run #{run_id} cancelled"

        # Repository operations
        elif action == "repo_view":
            args = ["repo", "view", "--json", "name,description,defaultBranch,visibility"]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return await self._parse_json(stdout)

        elif action == "repo_list":
            """List repository contents (files and directories)."""
            path = kwargs.get("path", "")
            args = ["repo", "view", "--json", "name"]
            if path:
                args.append(path)
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout

        elif action == "repo_contents":
            """Get file content from repository using gh api."""
            path = kwargs.get("path", "")
            if not path:
                return "Error: path required for repo_contents"
            endpoint = f"repos/{repo_str}/contents/{path}" if repo_str else f"contents/{path}"
            args = ["api", endpoint, "--method", "GET"]
            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout

        # API calls
        elif action == "api":
            endpoint = kwargs.get("endpoint")
            method = kwargs.get("method", "GET")
            fields = kwargs.get("fields")

            if not endpoint:
                return "Error: API endpoint required"

            args = ["api", endpoint, "--method", method]
            if fields:
                for field in fields:
                    args.extend(["--jq", field])

            returncode, stdout, stderr = await self._run_gh(args + repo_arg)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout

        return f"Error: Unknown action '{action}'"
