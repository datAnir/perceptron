"""Built-in tools for Arcon."""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, List

from .base import Tool, ToolMetadata, ToolParameter
from ..core.interface import ToolError


class ReadFileTool(Tool):
    """Tool to read file contents."""
    
    def _create_metadata(self) -> ToolMetadata:
        """Create tool metadata."""
        return ToolMetadata(
            name="read_file",
            description="Read the contents of a file from the filesystem",
            category="filesystem",
            tags=["io", "file", "read"]
        )
    
    def _create_parameters(self) -> List[ToolParameter]:
        """Create tool parameters."""
        return [
            ToolParameter(
                name="path",
                type="string",
                description="Path to the file to read (relative or absolute)",
                required=True
            )
        ]
    
    async def execute(self, **kwargs: Any) -> str:
        """Execute read file operation.
        
        Args:
            path: File path to read
            
        Returns:
            File contents as string
            
        Raises:
            ToolError: If file cannot be read
        """
        self.validate_parameters(**kwargs)
        path = kwargs["path"]
        
        try:
            file_path = Path(path).expanduser().resolve()
            
            if not file_path.exists():
                raise ToolError(f"File not found: {path}")
            
            if not file_path.is_file():
                raise ToolError(f"Path is not a file: {path}")
            
            # Read file with size limit (10MB)
            max_size = 10 * 1024 * 1024
            if file_path.stat().st_size > max_size:
                raise ToolError(f"File too large (max 10MB): {path}")
            
            content = file_path.read_text(encoding="utf-8")
            return content
            
        except UnicodeDecodeError:
            raise ToolError(f"File is not valid UTF-8 text: {path}")
        except PermissionError:
            raise ToolError(f"Permission denied: {path}")
        except Exception as e:
            raise ToolError(f"Failed to read file: {e}")


class WriteFileTool(Tool):
    """Tool to write content to a file."""
    
    def _create_metadata(self) -> ToolMetadata:
        """Create tool metadata."""
        return ToolMetadata(
            name="write_file",
            description="Write content to a file on the filesystem",
            category="filesystem",
            tags=["io", "file", "write"]
        )
    
    def _create_parameters(self) -> List[ToolParameter]:
        """Create tool parameters."""
        return [
            ToolParameter(
                name="path",
                type="string",
                description="Path to the file to write (relative or absolute)",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write to the file",
                required=True
            )
        ]
    
    async def execute(self, **kwargs: Any) -> str:
        """Execute write file operation.
        
        Args:
            path: File path to write
            content: Content to write
            
        Returns:
            Success message
            
        Raises:
            ToolError: If file cannot be written
        """
        self.validate_parameters(**kwargs)
        path = kwargs["path"]
        content = kwargs["content"]
        
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_path.write_text(content, encoding="utf-8")
            
            return f"Successfully wrote {len(content)} bytes to: {path}"
            
        except PermissionError:
            raise ToolError(f"Permission denied: {path}")
        except Exception as e:
            raise ToolError(f"Failed to write file: {e}")


class ListDirectoryTool(Tool):
    """Tool to list directory contents."""
    
    def _create_metadata(self) -> ToolMetadata:
        """Create tool metadata."""
        return ToolMetadata(
            name="list_dir",
            description="List the contents of a directory",
            category="filesystem",
            tags=["io", "directory", "list"]
        )
    
    def _create_parameters(self) -> List[ToolParameter]:
        """Create tool parameters."""
        return [
            ToolParameter(
                name="path",
                type="string",
                description="Path to the directory to list (defaults to current directory)",
                required=False,
                default="."
            )
        ]
    
    async def execute(self, **kwargs: Any) -> str:
        """Execute list directory operation.
        
        Args:
            path: Directory path to list (default: current directory)
            
        Returns:
            Directory listing
            
        Raises:
            ToolError: If directory cannot be listed
        """
        self.validate_parameters(**kwargs)
        path = kwargs.get("path", ".")
        
        try:
            dir_path = Path(path).expanduser().resolve()
            
            if not dir_path.exists():
                raise ToolError(f"Directory not found: {path}")
            
            if not dir_path.is_dir():
                raise ToolError(f"Path is not a directory: {path}")
            
            # List directory contents
            entries = []
            for entry in sorted(dir_path.iterdir()):
                entry_type = "DIR" if entry.is_dir() else "FILE"
                size = entry.stat().st_size if entry.is_file() else "-"
                entries.append(f"{entry_type:6} {size:>12} {entry.name}")
            
            if not entries:
                return f"Directory is empty: {path}"
            
            header = f"Directory: {path}\n\n{'TYPE':6} {'SIZE':>12} NAME\n{'-' * 60}"
            return f"{header}\n" + "\n".join(entries)
            
        except PermissionError:
            raise ToolError(f"Permission denied: {path}")
        except Exception as e:
            raise ToolError(f"Failed to list directory: {e}")


class BashExecuteTool(Tool):
    """Tool to execute bash commands."""
    
    def _create_metadata(self) -> ToolMetadata:
        """Create tool metadata."""
        return ToolMetadata(
            name="bash_execute",
            description="Execute a bash command and return its output",
            category="system",
            tags=["shell", "bash", "execute"]
        )
    
    def _create_parameters(self) -> List[ToolParameter]:
        """Create tool parameters."""
        return [
            ToolParameter(
                name="command",
                type="string",
                description="Bash command to execute",
                required=True
            ),
            ToolParameter(
                name="cwd",
                type="string",
                description="Working directory for command execution",
                required=False
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="Command timeout in seconds (default: 30)",
                required=False,
                default=30
            )
        ]
    
    async def execute(self, **kwargs: Any) -> str:
        """Execute bash command.
        
        Args:
            command: Bash command to execute
            cwd: Working directory (optional)
            timeout: Timeout in seconds (default: 30)
            
        Returns:
            Command output (stdout + stderr)
            
        Raises:
            ToolError: If command execution fails
        """
        self.validate_parameters(**kwargs)
        command = kwargs["command"]
        cwd = kwargs.get("cwd")
        timeout = kwargs.get("timeout", 30)
        
        try:
            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                shell=True
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise ToolError(f"Command timed out after {timeout}s: {command}")
            
            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            
            # Check exit code and raise error if command failed
            if process.returncode != 0:
                error_msg = stderr_text or stdout_text or "Command failed"
                raise ToolError(f"Command failed with exit code {process.returncode}: {error_msg.strip()}")
            
            # Return combined output
            output = stdout_text
            if stderr_text:
                output = output + "\n" + stderr_text if output else stderr_text
            
            return output or "(no output)"
            
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Failed to execute command: {e}")
