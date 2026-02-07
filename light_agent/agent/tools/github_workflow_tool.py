"""GitHub Actions workflow management tool."""

import asyncio
import json
import subprocess
from typing import Any, Optional

from light_agent.agent.tools.base import Tool


class GitHubWorkflowTool(Tool):
    """GitHub Actions workflow and run management."""

    @property
    def name(self) -> str:
        return "github_workflow"

    @property
    def description(self) -> str:
        return "Manage GitHub Actions workflows and runs. List, view, enable/disable workflows, and manage run status."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "list_workflows",
                        "view_workflow",
                        "enable_workflow",
                        "disable_workflow",
                        "run_workflow",
                        "list_runs",
                        "view_run",
                        "view_run_log",
                        "download_run_artifacts",
                        "rerun_workflow",
                        "cancel_workflow",
                        "approve_deployment",
                    ],
                    "description": "The workflow action to perform",
                },
                "owner": {
                    "type": "string",
                    "description": "Repository owner",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name",
                },
                "workflow": {
                    "type": "string",
                    "description": "Workflow file name or ID",
                },
                "run_id": {
                    "type": "string",
                    "description": "Workflow run ID",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch/ref for workflow run",
                },
                "inputs": {
                    "type": "object",
                    "description": "Workflow inputs (for workflow_dispatch events)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                },
            },
            "required": ["action"],
        }

    def _get_repo(self, owner: Optional[str], repo: Optional[str]) -> str:
        """Get repository string."""
        if owner and repo:
            return f"{owner}/{repo}"
        return ""

    async def _run_gh(
        self,
        args: list[str],
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> tuple[int, str, str]:
        """Execute a gh command."""
        repo_str = self._get_repo(owner, repo)
        repo_arg = ["--repo", repo_str] if repo_str else []

        cmd = ["gh"] + args + repo_arg

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()
        return (
            process.returncode,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )

    async def execute(self, **kwargs: Any) -> str:
        """Execute the workflow action."""
        action = kwargs.get("action")
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")
        workflow = kwargs.get("workflow")
        run_id = kwargs.get("run_id")
        branch = kwargs.get("branch")
        inputs = kwargs.get("inputs", {})
        limit = kwargs.get("limit", 10)

        # List workflows
        if action == "list_workflows":
            args = ["workflow", "list", "--limit", str(limit), "--json", "name,id,state,disabled"]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            try:
                workflows = json.loads(stdout)
                result = [
                    f"- {w['name']} (ID: {w['id']}, State: {w['state']}, Disabled: {w['disabled']})"
                    for w in workflows
                ]
                return "\n".join(result) if result else "No workflows found"
            except json.JSONDecodeError:
                return stdout

        # View workflow details
        elif action == "view_workflow":
            if not workflow:
                return "Error: Workflow name or ID required"
            args = ["workflow", "view", workflow, "--json", "name,id,path,state,disabled"]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            try:
                data = json.loads(stdout)
                return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                return stdout

        # Enable workflow
        elif action == "enable_workflow":
            if not workflow:
                return "Error: Workflow name or ID required"
            args = ["workflow", "enable", workflow]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Workflow '{workflow}' enabled"

        # Disable workflow
        elif action == "disable_workflow":
            if not workflow:
                return "Error: Workflow name or ID required"
            args = ["workflow", "disable", workflow]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Workflow '{workflow}' disabled"

        # Run workflow manually
        elif action == "run_workflow":
            if not workflow:
                return "Error: Workflow name or ID required"
            args = ["workflow", "run", workflow]
            if branch:
                args.extend(["--ref", branch])
            for key, value in inputs.items():
                args.extend(["--field", f"{key}={value}"])
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Workflow '{workflow}' started"

        # List workflow runs
        elif action == "list_runs":
            args = ["run", "list", "--limit", str(limit)]
            if workflow:
                args.extend(["--workflow", workflow])
            if branch:
                args.extend(["--branch", branch])
            args.extend(["--json", "status,conclusion,number,headBranch,name,createdAt"])
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            try:
                runs = json.loads(stdout)
                result = []
                for r in runs:
                    status = r.get("status", "unknown")
                    conclusion = r.get("conclusion", "")
                    result.append(
                        f"- #{r['number']}: {r['name']} ({status}/{conclusion}) - {r['headBranch']}"
                    )
                return "\n".join(result) if result else "No runs found"
            except json.JSONDecodeError:
                return stdout

        # View run details
        elif action == "view_run":
            if not run_id:
                return "Error: Run ID required"
            args = [
                "run",
                "view",
                run_id,
                "--json",
                "status,conclusion,number,headBranch,name,createdAt,updatedAt,jobs",
            ]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            try:
                data = json.loads(stdout)
                return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                return stdout

        # View run log
        elif action == "view_run_log":
            if not run_id:
                return "Error: Run ID required"
            args = ["run", "view", run_id, "--log"]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout if stdout else "No logs available"

        # Download run artifacts
        elif action == "download_run_artifacts":
            if not run_id:
                return "Error: Run ID required"
            args = ["run", "download", run_id]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Artifacts for run #{run_id} downloaded"

        # Rerun workflow
        elif action == "rerun_workflow":
            if not run_id:
                return "Error: Run ID required"
            args = ["run", "rerun", run_id]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Run #{run_id} rerun started"

        # Cancel workflow
        elif action == "cancel_workflow":
            if not run_id:
                return "Error: Run ID required"
            args = ["run", "cancel", run_id]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Run #{run_id} cancelled"

        # Approve deployment
        elif action == "approve_deployment":
            if not run_id:
                return "Error: Run ID required"
            args = ["run", "approve-deployment", run_id]
            returncode, stdout, stderr = await self._run_gh(args, owner, repo)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Deployment for run #{run_id} approved"

        return f"Error: Unknown action '{action}'"
