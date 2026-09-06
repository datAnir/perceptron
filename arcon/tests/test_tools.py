"""Tests for tool system."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from arcon.tools import (
    Tool,
    ToolMetadata,
    ToolParameter,
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    BashExecuteTool,
    ToolRegistry,
    get_global_registry,
    ToolExecutor,
    ToolExecutionResult,
)
from arcon.core.interface import ToolError


class MockTool(Tool):
    """Mock tool for testing."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="mock_tool",
            description="A mock tool for testing",
            category="test",
            tags=["mock", "test"]
        )
    
    def _create_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="param1",
                type="string",
                description="First parameter",
                required=True
            ),
            ToolParameter(
                name="param2",
                type="integer",
                description="Second parameter",
                required=False,
                default=42
            )
        ]
    
    async def execute(self, **kwargs) -> str:
        self.validate_parameters(**kwargs)
        param1 = kwargs["param1"]
        param2 = kwargs.get("param2", 42)
        return f"Executed with param1={param1}, param2={param2}"


class TestToolBase:
    """Test Tool base class."""
    
    def test_tool_metadata(self):
        """Test tool metadata."""
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
        assert tool.category == "test"
        assert "mock" in tool.metadata.tags
    
    def test_tool_parameters(self):
        """Test tool parameters."""
        tool = MockTool()
        assert len(tool.parameters) == 2
        assert tool.parameters[0].name == "param1"
        assert tool.parameters[0].required is True
        assert tool.parameters[1].name == "param2"
        assert tool.parameters[1].required is False
    
    def test_tool_to_dict(self):
        """Test converting tool to dictionary."""
        tool = MockTool()
        tool_dict = tool.to_dict()
        
        assert tool_dict["name"] == "mock_tool"
        assert tool_dict["description"] == "A mock tool for testing"
        assert "input_schema" in tool_dict
        assert "properties" in tool_dict["input_schema"]
        assert "param1" in tool_dict["input_schema"]["properties"]
        assert "param1" in tool_dict["input_schema"]["required"]
        assert "param2" not in tool_dict["input_schema"]["required"]
    
    @pytest.mark.asyncio
    async def test_validate_parameters_success(self):
        """Test parameter validation success."""
        tool = MockTool()
        result = await tool.execute(param1="test")
        assert "param1=test" in result
        assert "param2=42" in result
    
    @pytest.mark.asyncio
    async def test_validate_parameters_missing_required(self):
        """Test parameter validation with missing required parameter."""
        tool = MockTool()
        with pytest.raises(ToolError, match="Missing required parameter"):
            tool.validate_parameters()
    
    @pytest.mark.asyncio
    async def test_validate_parameters_unknown_param(self):
        """Test parameter validation with unknown parameter."""
        tool = MockTool()
        with pytest.raises(ToolError, match="Unknown parameter"):
            tool.validate_parameters(param1="test", unknown="value")


class TestBuiltinTools:
    """Test built-in tools."""
    
    @pytest.mark.asyncio
    async def test_read_file_success(self):
        """Test reading a file successfully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            tool = ReadFileTool()
            result = await tool.execute(path=temp_path)
            assert result == "Test content"
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_read_file_not_found(self):
        """Test reading non-existent file."""
        tool = ReadFileTool()
        with pytest.raises(ToolError, match="File not found"):
            await tool.execute(path="/nonexistent/file.txt")
    
    @pytest.mark.asyncio
    async def test_write_file_success(self):
        """Test writing a file successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            tool = WriteFileTool()
            result = await tool.execute(
                path=str(file_path),
                content="Hello, World!"
            )
            
            assert "Successfully wrote" in result
            assert file_path.exists()
            assert file_path.read_text() == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_write_file_creates_directories(self):
        """Test writing file creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "test.txt"
            tool = WriteFileTool()
            await tool.execute(
                path=str(file_path),
                content="Test"
            )
            
            assert file_path.exists()
            assert file_path.read_text() == "Test"
    
    @pytest.mark.asyncio
    async def test_list_dir_success(self):
        """Test listing directory contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.txt").write_text("content1")
            (Path(tmpdir) / "file2.txt").write_text("content2")
            (Path(tmpdir) / "subdir").mkdir()
            
            tool = ListDirectoryTool()
            result = await tool.execute(path=tmpdir)
            
            assert "file1.txt" in result
            assert "file2.txt" in result
            assert "subdir" in result
            assert "DIR" in result
            assert "FILE" in result
    
    @pytest.mark.asyncio
    async def test_list_dir_not_found(self):
        """Test listing non-existent directory."""
        tool = ListDirectoryTool()
        with pytest.raises(ToolError, match="Directory not found"):
            await tool.execute(path="/nonexistent/directory")
    
    @pytest.mark.asyncio
    async def test_bash_execute_success(self):
        """Test executing bash command successfully."""
        tool = BashExecuteTool()
        result = await tool.execute(command="echo 'Hello, World!'")
        
        assert "Hello, World!" in result
    
    @pytest.mark.asyncio
    async def test_bash_execute_with_error(self):
        """Test executing bash command with non-zero exit."""
        from arcon.core.interface import ToolError
        
        tool = BashExecuteTool()
        with pytest.raises(ToolError) as exc_info:
            await tool.execute(command="exit 1")
        
        assert "exit code 1" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_bash_execute_timeout(self):
        """Test bash command timeout."""
        tool = BashExecuteTool()
        with pytest.raises(ToolError, match="timed out"):
            await tool.execute(command="sleep 10", timeout=1)


class TestToolRegistry:
    """Test ToolRegistry class."""
    
    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool()
        
        registry.register(tool)
        assert registry.has("mock_tool")
        assert registry.count() == 1
    
    def test_register_duplicate_tool(self):
        """Test registering duplicate tool raises error."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = MockTool()
        
        registry.register(tool1)
        with pytest.raises(ToolError, match="already registered"):
            registry.register(tool2)
    
    def test_get_tool(self):
        """Test getting a tool by name."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        retrieved = registry.get("mock_tool")
        assert retrieved.name == "mock_tool"
    
    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool raises error."""
        registry = ToolRegistry()
        with pytest.raises(ToolError, match="not found"):
            registry.get("nonexistent")
    
    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        assert registry.has("mock_tool")
        registry.unregister("mock_tool")
        assert not registry.has("mock_tool")
    
    def test_list_all_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        tool1 = MockTool()
        registry.register(tool1)
        
        tools = registry.list_all()
        assert len(tools) == 1
        assert tools[0].name == "mock_tool"
    
    def test_list_names(self):
        """Test listing tool names."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        names = registry.list_names()
        assert "mock_tool" in names
    
    def test_get_by_category(self):
        """Test getting tools by category."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        tools = registry.get_by_category("test")
        assert len(tools) == 1
        assert tools[0].category == "test"
    
    def test_get_by_tag(self):
        """Test getting tools by tag."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        tools = registry.get_by_tag("mock")
        assert len(tools) == 1
        assert "mock" in tools[0].metadata.tags
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        assert registry.count() == 1
        registry.clear()
        assert registry.count() == 0


class TestGlobalRegistry:
    """Test global registry."""
    
    def test_global_registry_has_builtin_tools(self):
        """Test global registry includes built-in tools."""
        registry = get_global_registry()
        
        assert registry.has("read_file")
        assert registry.has("write_file")
        assert registry.has("list_dir")
        assert registry.has("bash_execute")
        assert registry.count() >= 4


class TestToolExecutor:
    """Test ToolExecutor class."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test executing a tool successfully."""
        registry = ToolRegistry()
        registry.register(MockTool())
        executor = ToolExecutor(registry=registry)
        
        result = await executor.execute("mock_tool", param1="test")
        
        assert result.success is True
        assert "param1=test" in result.output
        assert result.error is None
        assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test executing non-existent tool."""
        registry = ToolRegistry()
        executor = ToolExecutor(registry=registry)
        
        result = await executor.execute("nonexistent")
        
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_tool_timeout(self):
        """Test tool execution timeout."""
        # Use bash_execute with sleep to test timeout
        registry = ToolRegistry()
        registry.register(BashExecuteTool())
        executor = ToolExecutor(registry=registry, default_timeout=1)
        
        result = await executor.execute(
            "bash_execute",
            command="sleep 5",
            timeout=1
        )
        
        assert result.success is False
        assert "timed out" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_batch(self):
        """Test executing multiple tools in batch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "test1.txt"
            file2 = Path(tmpdir) / "test2.txt"
            file1.write_text("Content 1")
            file2.write_text("Content 2")
            
            registry = get_global_registry()
            executor = ToolExecutor(registry=registry)
            
            tool_calls = [
                {"name": "read_file", "parameters": {"path": str(file1)}},
                {"name": "read_file", "parameters": {"path": str(file2)}},
            ]
            
            results = await executor.execute_batch(tool_calls)
            
            assert len(results) == 2
            assert all(r.success for r in results)
            assert "Content 1" in results[0].output
            assert "Content 2" in results[1].output
    
    @pytest.mark.asyncio
    async def test_output_truncation(self):
        """Test output truncation for long results."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Write large content
            large_content = "x" * 100000
            f.write(large_content)
            temp_path = f.name
        
        try:
            registry = get_global_registry()
            executor = ToolExecutor(registry=registry, max_output_length=1000)
            
            result = await executor.execute("read_file", path=temp_path)
            
            assert result.success is True
            assert result.truncated is True
            assert len(result.output) < len(large_content)
            assert "truncated" in result.output.lower()
        finally:
            Path(temp_path).unlink()
    
    def test_get_available_tools(self):
        """Test getting available tools."""
        registry = ToolRegistry()
        registry.register(MockTool())
        executor = ToolExecutor(registry=registry)
        
        tools = executor.get_available_tools()
        
        assert len(tools) >= 1
        assert any(t["name"] == "mock_tool" for t in tools)
    
    def test_validate_tool_call(self):
        """Test validating tool calls."""
        registry = ToolRegistry()
        registry.register(MockTool())
        executor = ToolExecutor(registry=registry)
        
        # Valid call
        assert executor.validate_tool_call("mock_tool", param1="test") is True
        
        # Invalid call - missing required parameter
        assert executor.validate_tool_call("mock_tool") is False
        
        # Invalid call - unknown tool
        assert executor.validate_tool_call("nonexistent", param1="test") is False


class TestToolExecutionResult:
    """Test ToolExecutionResult class."""
    
    def test_result_creation(self):
        """Test creating execution result."""
        result = ToolExecutionResult(
            tool_name="test_tool",
            success=True,
            output="Test output",
            execution_time_ms=123.45
        )
        
        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.output == "Test output"
        assert result.execution_time_ms == 123.45
    
    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = ToolExecutionResult(
            tool_name="test_tool",
            success=True,
            output="Test output",
            execution_time_ms=123.45
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["tool_name"] == "test_tool"
        assert result_dict["success"] is True
        assert result_dict["output"] == "Test output"
        assert result_dict["execution_time_ms"] == 123.45
    
    def test_result_repr(self):
        """Test result string representation."""
        result = ToolExecutionResult(
            tool_name="test_tool",
            success=True,
            output="Test output",
            execution_time_ms=123.45
        )
        
        repr_str = repr(result)
        assert "test_tool" in repr_str
        assert "SUCCESS" in repr_str
        assert "123.45" in repr_str
