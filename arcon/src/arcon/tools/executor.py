"""Tool execution engine with error handling and output management."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .base import Tool
from .registry import ToolRegistry, get_global_registry
from ..core.interface import ToolError


class ToolExecutionResult:
    """Result of tool execution."""
    
    def __init__(
        self,
        tool_name: str,
        success: bool,
        output: str,
        error: Optional[str] = None,
        execution_time_ms: float = 0.0,
        truncated: bool = False
    ):
        """Initialize execution result.
        
        Args:
            tool_name: Name of the tool executed
            success: Whether execution was successful
            output: Tool output
            error: Error message if failed
            execution_time_ms: Execution time in milliseconds
            truncated: Whether output was truncated
        """
        self.tool_name = tool_name
        self.success = success
        self.output = output
        self.error = error
        self.execution_time_ms = execution_time_ms
        self.truncated = truncated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation
        """
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "truncated": self.truncated
        }
    
    def __repr__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"ToolExecutionResult({self.tool_name}, {status}, {self.execution_time_ms:.2f}ms)"


class ToolExecutor:
    """Tool execution engine with error handling and timeout."""
    
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        default_timeout: int = 30,
        max_output_length: int = 50000
    ):
        """Initialize tool executor.
        
        Args:
            registry: Tool registry to use (defaults to global registry)
            default_timeout: Default timeout in seconds
            max_output_length: Maximum output length before truncation
        """
        self.registry = registry or get_global_registry()
        self.default_timeout = default_timeout
        self.max_output_length = max_output_length
    
    async def execute(
        self,
        tool_name: str,
        timeout: Optional[int] = None,
        **kwargs: Any
    ) -> ToolExecutionResult:
        """Execute a tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            timeout: Execution timeout in seconds (overrides default)
            **kwargs: Tool parameters
            
        Returns:
            ToolExecutionResult with execution details
        """
        start_time = datetime.now(timezone.utc)
        timeout_seconds = timeout or self.default_timeout
        
        try:
            # Get tool from registry
            tool = self.registry.get(tool_name)
            
            # Execute with timeout
            try:
                output = await asyncio.wait_for(
                    tool.execute(**kwargs),
                    timeout=timeout_seconds
                )
                
                # Truncate output if too long
                truncated = False
                if len(output) > self.max_output_length:
                    truncated = True
                    output = (
                        output[:self.max_output_length] +
                        f"\n\n... [Output truncated at {self.max_output_length} characters]"
                    )
                
                # Calculate execution time
                end_time = datetime.now(timezone.utc)
                execution_time_ms = (end_time - start_time).total_seconds() * 1000
                
                return ToolExecutionResult(
                    tool_name=tool_name,
                    success=True,
                    output=output,
                    execution_time_ms=execution_time_ms,
                    truncated=truncated
                )
                
            except asyncio.TimeoutError:
                end_time = datetime.now(timezone.utc)
                execution_time_ms = (end_time - start_time).total_seconds() * 1000
                
                error_msg = f"Tool execution timed out after {timeout_seconds}s"
                return ToolExecutionResult(
                    tool_name=tool_name,
                    success=False,
                    output="",
                    error=error_msg,
                    execution_time_ms=execution_time_ms
                )
                
        except ToolError as e:
            end_time = datetime.now(timezone.utc)
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=str(e),
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Unexpected error: {e}",
                execution_time_ms=execution_time_ms
            )
    
    async def execute_batch(
        self,
        tool_calls: list[Dict[str, Any]],
        timeout: Optional[int] = None
    ) -> list[ToolExecutionResult]:
        """Execute multiple tools in parallel.
        
        Args:
            tool_calls: List of tool calls with format:
                       [{"name": "tool_name", "parameters": {...}}, ...]
            timeout: Execution timeout per tool in seconds
            
        Returns:
            List of ToolExecutionResult for each tool call
        """
        tasks = []
        for call in tool_calls:
            tool_name = call.get("name")
            parameters = call.get("parameters", {})
            
            if not tool_name:
                continue
            
            task = self.execute(tool_name, timeout=timeout, **parameters)
            tasks.append(task)
        
        if not tasks:
            return []
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    ToolExecutionResult(
                        tool_name=tool_calls[i].get("name", "unknown"),
                        success=False,
                        output="",
                        error=f"Execution failed: {result}"
                    )
                )
            else:
                final_results.append(result)
        
        return final_results
    
    def get_available_tools(self) -> list[Dict[str, Any]]:
        """Get list of available tools with their definitions.
        
        Returns:
            List of tool definitions
        """
        return self.registry.to_dict()
    
    def validate_tool_call(self, tool_name: str, **kwargs: Any) -> bool:
        """Validate a tool call before execution.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Returns:
            True if valid, False otherwise
        """
        try:
            tool = self.registry.get(tool_name)
            tool.validate_parameters(**kwargs)
            return True
        except (ToolError, ValueError):
            return False
