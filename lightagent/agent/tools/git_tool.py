"""Git operations tool with safety validation."""

import asyncio
from pathlib import Path
from typing import Any, Optional

from lightagent.agent.tools.base import Tool


class GitTool(Tool):
    """Safe Git operations tool with validation."""

    @property
    def name(self) -> str:
        return "git"

    @property
    def description(self) -> str:
        return "Perform safe Git operations. Supports status, branch, commit, and merge operations with validation."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "status",
                        "diff",
                        "log",
                        "branch_list",
                        "branch_create",
                        "branch_delete",
                        "checkout",
                        "add",
                        "commit",
                        "push",
                        "pull",
                        "merge_check",
                        "revert_check",
                        "show",
                        "blame",
                    ],
                    "description": "The Git action to perform",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files to operate on",
                },
                "message": {
                    "type": "string",
                    "description": "Commit message for commit action",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name for branch operations",
                },
                "target_branch": {
                    "type": "string",
                    "description": "Target branch for merge/checkout",
                },
                "commit": {
                    "type": "string",
                    "description": "Commit hash for show/blame/revert",
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                },
                "max_count": {
                    "type": "integer",
                    "description": "Maximum number of commits to show",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for the command",
                },
            },
            "required": ["action"],
        }

    async def _run_git(
        self,
        args: list[str],
        working_dir: Optional[str] = None,
        capture_output: bool = True,
    ) -> tuple[int | None, str, str]:
        """Execute a git command safely."""
        cwd = working_dir or str(Path.cwd())

        process = await asyncio.create_subprocess_exec(
            "git",
            *args,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            cwd=cwd,
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

    async def _validate_commit_message(self, message: str) -> tuple[bool, str]:
        """Validate commit message format."""
        if len(message) < 3:
            return False, "Commit message too short (min 3 characters)"
        if len(message) > 200:
            return False, "Commit message too long (max 200 characters)"
        return True, ""

    async def _validate_branch_name(self, branch: str) -> tuple[bool, str]:
        """Validate branch name format."""
        import re

        # Git branch name rules
        if not branch:
            return False, "Branch name cannot be empty"
        if branch.startswith("-") or branch.startswith("/"):
            return False, "Branch name cannot start with dash or slash"
        if " " in branch:
            return False, "Branch name cannot contain spaces"
        if not re.match(r"^[a-zA-Z0-9._/-]+$", branch):
            return False, "Branch name contains invalid characters"

        return True, ""

    async def execute(self, **kwargs: Any) -> str:
        """Execute the git action."""
        action = kwargs.get("action")
        files = kwargs.get("files", [])
        message = kwargs.get("message", "")
        branch = kwargs.get("branch", "")
        target_branch = kwargs.get("target_branch", "")
        commit = kwargs.get("commit", "")
        remote = kwargs.get("remote", "origin")
        max_count = kwargs.get("max_count", 10)
        working_dir = kwargs.get("working_dir")

        # Validate message for commit
        if action == "commit":
            if not message:
                return "Error: Commit message is required"
            is_valid, error = await self._validate_commit_message(message)
            if not is_valid:
                return f"Error: {error}"

        # Validate branch name for branch operations
        if action in ("branch_create", "branch_delete", "checkout"):
            if not branch and action != "branch_list":
                return f"Error: Branch name is required for {action}"

            if action == "branch_delete":
                # Prevent deleting main/master branches
                protected = ["main", "master", "develop", "dev"]
                if branch in protected:
                    return f"Error: Cannot delete protected branch '{branch}'"
                # Require --force for non-empty deletes
                if not kwargs.get("force"):
                    return "Error: Deleting branch requires --force flag"

            if action == "branch_create":
                is_valid, error = await self._validate_branch_name(branch)
                if not is_valid:
                    return f"Error: {error}"

        # Build git arguments
        if action == "status":
            args = ["status", "-s"]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout if stdout else "Working tree is clean"

        elif action == "diff":
            args = ["diff", "--stat"]
            if files:
                args.extend(files)
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout if stdout else "No changes to show"

        elif action == "log":
            args = ["log", f"--max-count={max_count}", "--oneline"]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout if stdout else "No commits found"

        elif action == "branch_list":
            args = ["branch", "-a"]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            if not stdout:
                return "No branches found"
            # Format output
            lines = [
                f"* {b[2:]}" if b.startswith("* ") else f"  {b}" for b in stdout.strip().split("\n")
            ]
            return "\n".join(lines)

        elif action == "branch_create":
            args = ["checkout", "-b", branch]
            if target_branch:
                args = ["checkout", target_branch, "-b", branch]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Created and checked out branch: {branch}"

        elif action == "branch_delete":
            args = ["branch", "-d", branch]
            if kwargs.get("force"):
                args = ["branch", "-D", branch]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Deleted branch: {branch}"

        elif action == "checkout":
            args = ["checkout", branch]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Checked out branch: {branch}"

        elif action == "add":
            if not files:
                args = ["add", "."]
            else:
                args = ["add"] + files
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Added {len(files) if files else 'all'} file(s) to staging"

        elif action == "commit":
            args = ["commit", "-m", message]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Commit created: {message[:50]}..."

        elif action == "push":
            args = ["push", remote, "--"]
            # Get current branch
            cb_args = ["rev-parse", "--abbrev-ref", "HEAD"]
            _, current_branch, _ = await self._run_git(cb_args, working_dir)
            current_branch = current_branch.strip()
            args = ["push", remote, current_branch]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return f"✓ Pushed to {remote}/{current_branch}"

        elif action == "pull":
            args = ["pull", "--ff-only"]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return "✓ Pulled latest changes"

        elif action == "merge_check":
            # Check if branch can be merged cleanly
            source = branch or kwargs.get("source", "")
            target = target_branch or "main"

            if not source:
                return "Error: Source branch required for merge_check"

            # Get merge-base
            args = ["merge-base", source, target]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error finding merge base: {stderr}"

            merge_base = stdout.strip()

            # Check if source is ahead of target
            args = ["rev-list", "--count", f"{merge_base}..{source}"]
            returncode, ahead, _ = await self._run_git(args, working_dir)

            # Check if target has changes since merge-base
            args = ["rev-list", "--count", f"{merge_base}..{target}"]
            returncode, behind, _ = await self._run_git(args, working_dir)

            ahead_count = int(ahead.strip()) if ahead.strip().isdigit() else 0
            behind_count = int(behind.strip()) if behind.strip().isdigit() else 0

            return f"Merge check: {source} is {ahead_count} commits ahead, {target} is {behind_count} commits behind"

        elif action == "revert_check":
            if not commit:
                return "Error: Commit hash required for revert_check"

            # Get commit info
            args = ["show", "--no-patch", "--format=%H %s", commit]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"

            return f"✓ Commit available for revert: {stdout.strip()}"

        elif action == "show":
            args = ["show"]
            if commit:
                args.append(commit)
            if files:
                args.extend(["--", ",".join(files)])
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            return stdout if stdout else "No changes to show"

        elif action == "blame":
            if not files:
                return "Error: File path required for blame"
            args = ["blame", "--line-porcelain", files[0]]
            returncode, stdout, stderr = await self._run_git(args, working_dir)
            if returncode != 0:
                return f"Error: {stderr}"
            # Return simplified blame info
            lines = stdout.strip().split("\n")[:20]  # First 20 lines
            result = []
            for line in lines:
                if line.startswith("author "):
                    result.append(f"Author: {line[7:]}")
                elif line.startswith("summary "):
                    result.append(f"Commit: {line[7:]}")
            return "\n".join(result) if result else "No blame info available"

        return f"Error: Unknown action '{action}'"
