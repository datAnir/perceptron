"""Tool registry for managing available tools."""

from typing import Dict, List, Optional

from .base import Tool
from ..core.interface import ToolError


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ToolError: If tool with same name already registered
        """
        if tool.name in self._tools:
            raise ToolError(f"Tool already registered: {tool.name}")
        
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool.
        
        Args:
            name: Name of tool to unregister
            
        Raises:
            ToolError: If tool not found
        """
        if name not in self._tools:
            raise ToolError(f"Tool not found: {name}")
        
        del self._tools[name]
    
    def get(self, name: str) -> Tool:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance
            
        Raises:
            ToolError: If tool not found
        """
        if name not in self._tools:
            raise ToolError(f"Tool not found: {name}")
        
        return self._tools[name]
    
    def has(self, name: str) -> bool:
        """Check if tool is registered.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool is registered
        """
        return name in self._tools
    
    def list_all(self) -> List[Tool]:
        """Get all registered tools.
        
        Returns:
            List of all tools
        """
        return list(self._tools.values())
    
    def list_names(self) -> List[str]:
        """Get all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def get_by_category(self, category: str) -> List[Tool]:
        """Get tools by category.
        
        Args:
            category: Category name
            
        Returns:
            List of tools in the category
        """
        return [
            tool for tool in self._tools.values()
            if tool.category == category
        ]
    
    def get_by_tag(self, tag: str) -> List[Tool]:
        """Get tools by tag.
        
        Args:
            tag: Tag name
            
        Returns:
            List of tools with the tag
        """
        return [
            tool for tool in self._tools.values()
            if tag in tool.metadata.tags
        ]
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
    
    def count(self) -> int:
        """Get count of registered tools.
        
        Returns:
            Number of registered tools
        """
        return len(self._tools)
    
    def to_dict(self) -> List[Dict]:
        """Convert all tools to dictionary format.
        
        Returns:
            List of tool definitions
        """
        return [tool.to_dict() for tool in self._tools.values()]


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """Get or create the global tool registry.
    
    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        _register_builtin_tools(_global_registry)
    return _global_registry


def _register_builtin_tools(registry: ToolRegistry) -> None:
    """Register built-in tools to the registry.
    
    Args:
        registry: ToolRegistry instance
    """
    from .builtin import (
        ReadFileTool,
        WriteFileTool,
        ListDirectoryTool,
        BashExecuteTool
    )
    
    # Register all built-in tools
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ListDirectoryTool())
    registry.register(BashExecuteTool())
