"""File system tools: read, write, edit."""

from pathlib import Path
from typing import Any

from lightagent.agent.tools.base import Tool


class FileToolBase(Tool):
    """Base class for file system tools with workspace restriction support."""

    def __init__(self, workspace: Path | None = None, restrict_to_workspace: bool = False):
        self.workspace = workspace
        self.restrict_to_workspace = restrict_to_workspace

    def _get_safe_path(self, path_str: str) -> Path:
        """
        Resolve and validate a path, ensuring it stays within workspace if restricted.

        Args:
            path_str: The path string to resolve.

        Returns:
            Resolved Path object.

        Raises:
            PermissionError: If restrict_to_workspace is enabled and path is outside workspace.
        """
        # Expand user home directory and resolve to absolute path
        path = Path(path_str).expanduser().resolve()

        if self.restrict_to_workspace and self.workspace:
            workspace_resolved = self.workspace.resolve()

            # Check if the path is within the workspace
            try:
                # relative_to raises ValueError if path is not within workspace
                path.relative_to(workspace_resolved)
            except ValueError:
                raise PermissionError(
                    f"Access denied: {path_str} is outside the workspace. "
                    f"Workspace is restricted to: {self.workspace}"
                )

        return path


class ReadFileTool(FileToolBase):
    """Tool to read file contents."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file at the given path."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "The file path to read"}},
            "required": ["path"],
        }

    async def execute(self, **kwargs: Any) -> str:
        path = kwargs.get("path", "")
        try:
            file_path = self._get_safe_path(path)
            if not file_path.exists():
                return f"Error: File not found: {path}"
            if not file_path.is_file():
                return f"Error: Not a file: {path}"

            content = file_path.read_text(encoding="utf-8")
            return content
        except PermissionError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


class WriteFileTool(FileToolBase):
    """Tool to write content to a file."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file at the given path. Creates parent directories if needed."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The file path to write to"},
                "content": {"type": "string", "description": "The content to write"},
            },
            "required": ["path", "content"],
        }

    async def execute(self, **kwargs: Any) -> str:
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        try:
            file_path = self._get_safe_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} bytes to {path}"
        except PermissionError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class EditFileTool(FileToolBase):
    """Tool to edit a file by replacing text."""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Edit a file by replacing old_text with new_text. The old_text must exist exactly in the file."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The file path to edit"},
                "old_text": {"type": "string", "description": "The exact text to find and replace"},
                "new_text": {"type": "string", "description": "The text to replace with"},
            },
            "required": ["path", "old_text", "new_text"],
        }

    async def execute(self, **kwargs: Any) -> str:
        path = kwargs.get("path", "")
        old_text = kwargs.get("old_text", "")
        new_text = kwargs.get("new_text", "")
        try:
            file_path = self._get_safe_path(path)
            if not file_path.exists():
                return f"Error: File not found: {path}"

            content = file_path.read_text(encoding="utf-8")

            if old_text not in content:
                return "Error: old_text not found in file. Make sure it matches exactly."

            # Count occurrences
            count = content.count(old_text)
            if count > 1:
                return f"Warning: old_text appears {count} times. Please provide more context to make it unique."

            new_content = content.replace(old_text, new_text, 1)
            file_path.write_text(new_content, encoding="utf-8")

            return f"Successfully edited {path}"
        except PermissionError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error editing file: {str(e)}"


class ListDirTool(FileToolBase):
    """Tool to list directory contents."""

    @property
    def name(self) -> str:
        return "list_dir"

    @property
    def description(self) -> str:
        return "List the contents of a directory."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "The directory path to list"}},
            "required": ["path"],
        }

    async def execute(self, **kwargs: Any) -> str:
        path = kwargs.get("path", "")
        try:
            dir_path = self._get_safe_path(path)
            if not dir_path.exists():
                return f"Error: Directory not found: {path}"
            if not dir_path.is_dir():
                return f"Error: Not a directory: {path}"

            items = []
            for item in sorted(dir_path.iterdir()):
                prefix = "📁 " if item.is_dir() else "📄 "
                items.append(f"{prefix}{item.name}")

            if not items:
                return f"Directory {path} is empty"

            return "\n".join(items)
        except PermissionError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error listing directory: {str(e)}"
