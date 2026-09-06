"""Base tool abstraction for Arcon."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        param_dict = {
            "type": self.type,
            "description": self.description
        }
        if self.default is not None:
            param_dict["default"] = self.default
        return param_dict


@dataclass
class ToolMetadata:
    """Tool metadata."""
    
    name: str
    description: str
    category: str = "general"
    version: str = "1.0.0"
    author: str = "arcon"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "author": self.author,
            "tags": self.tags
        }


class Tool(ABC):
    """Abstract base class for tools."""
    
    def __init__(self):
        """Initialize tool."""
        self._metadata = self._create_metadata()
        self._parameters = self._create_parameters()
    
    @abstractmethod
    def _create_metadata(self) -> ToolMetadata:
        """Create tool metadata.
        
        Returns:
            ToolMetadata instance
        """
        pass
    
    @abstractmethod
    def _create_parameters(self) -> List[ToolParameter]:
        """Create tool parameters.
        
        Returns:
            List of ToolParameter instances
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result as string
            
        Raises:
            ToolError: If execution fails
        """
        pass
    
    @property
    def name(self) -> str:
        """Get tool name."""
        return self._metadata.name
    
    @property
    def description(self) -> str:
        """Get tool description."""
        return self._metadata.description
    
    @property
    def category(self) -> str:
        """Get tool category."""
        return self._metadata.category
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self._metadata
    
    @property
    def parameters(self) -> List[ToolParameter]:
        """Get tool parameters."""
        return self._parameters
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool definition to dictionary format.
        
        Returns:
            Dictionary with tool name, description, and parameters
        """
        required_params = [p.name for p in self._parameters if p.required]
        properties = {p.name: p.to_dict() for p in self._parameters}
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required_params
            }
        }
    
    def validate_parameters(self, **kwargs: Any) -> None:
        """Validate provided parameters against tool schema.
        
        Args:
            **kwargs: Parameters to validate
            
        Raises:
            ValueError: If required parameter is missing or invalid
        """
        from ..core.interface import ToolError
        
        # Check required parameters
        for param in self._parameters:
            if param.required and param.name not in kwargs:
                raise ToolError(
                    f"Missing required parameter '{param.name}' for tool '{self.name}'"
                )
        
        # Check for unknown parameters
        param_names = {p.name for p in self._parameters}
        for key in kwargs:
            if key not in param_names:
                raise ToolError(
                    f"Unknown parameter '{key}' for tool '{self.name}'"
                )
