"""Tool workflow integration tests."""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

from arcon.tools import get_global_registry
from arcon.tools.executor import ToolExecutor
from arcon.tools.builtin import ReadFileTool, WriteFileTool, ListDirectoryTool, BashExecuteTool


@pytest.fixture
def test_workspace():
    """Create temporary workspace."""
    workspace = Path(tempfile.mkdtemp(prefix="arcon_test_"))
    yield workspace
    shutil.rmtree(workspace, ignore_errors=True)


@pytest.mark.asyncio
async def test_file_operations_workflow(test_workspace):
    """Test complete file operations workflow."""
    registry = get_global_registry()
    executor = ToolExecutor(registry)
    
    test_file = test_workspace / "test.txt"
    test_content = "Hello, World!\nThis is a test file."
    
    # Write file
    write_result = await executor.execute(
        "write_file",
        path=str(test_file),
        content=test_content
    )
    assert write_result.success
    assert test_file.exists()
    
    # Read file
    read_result = await executor.execute(
        "read_file",
        path=str(test_file)
    )
    assert read_result.success
    assert read_result.output == test_content
    
    # List directory
    list_result = await executor.execute(
        "list_dir",
        path=str(test_workspace)
    )
    assert list_result.success
    assert "test.txt" in list_result.output


@pytest.mark.asyncio
async def test_bash_execution_workflow(test_workspace):
    """Test bash command execution workflow."""
    registry = get_global_registry()
    executor = ToolExecutor(registry)
    
    # Simple command
    result = await executor.execute(
        "bash_execute",
        command="echo 'Hello from bash'"
    )
    assert result.success
    assert "Hello from bash" in result.output
    
    # Command with working directory
    result = await executor.execute(
        "bash_execute",
        command="pwd",
        cwd=str(test_workspace)
    )
    assert result.success
    assert str(test_workspace) in result.output


@pytest.mark.asyncio
async def test_complex_tool_chain(test_workspace):
    """Test chaining multiple tools together."""
    registry = get_global_registry()
    executor = ToolExecutor(registry)
    
    # Create a Python script
    script_path = test_workspace / "script.py"
    script_content = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

print(f"Addition: {add(5, 3)}")
print(f"Multiplication: {multiply(5, 3)}")
"""
    
    # Step 1: Write script
    write_result = await executor.execute(
        "write_file",
        path=str(script_path),
        content=script_content
    )
    assert write_result.success
    
    # Step 2: Execute script
    exec_result = await executor.execute(
        "bash_execute",
        command=f"python {script_path}"
    )
    assert exec_result.success
    assert "Addition: 8" in exec_result.output
    assert "Multiplication: 15" in exec_result.output
    
    # Step 3: Read script to verify
    read_result = await executor.execute(
        "read_file",
        path=str(script_path)
    )
    assert read_result.success
    assert "def add(a, b):" in read_result.output


@pytest.mark.asyncio
async def test_tool_error_handling(test_workspace):
    """Test tool error handling."""
    registry = get_global_registry()
    executor = ToolExecutor(registry)
    
    # Try to read non-existent file
    result = await executor.execute(
        "read_file",
        path=str(test_workspace / "nonexistent.txt")
    )
    assert not result.success
    assert result.error is not None
    
    # Try invalid bash command
    result = await executor.execute(
        "bash_execute",
        command="nonexistent_command_xyz"
    )
    assert not result.success


@pytest.mark.asyncio
async def test_tool_output_truncation(test_workspace):
    """Test that large outputs are truncated."""
    registry = get_global_registry()
    # Configure executor with 10KB output limit
    executor = ToolExecutor(registry, max_output_length=10240)
    
    # Create a large file
    large_content = "x" * 15000  # Larger than 10KB limit
    large_file = test_workspace / "large.txt"
    
    write_result = await executor.execute(
        "write_file",
        path=str(large_file),
        content=large_content
    )
    assert write_result.success
    
    # Read should truncate
    read_result = await executor.execute(
        "read_file",
        path=str(large_file)
    )
    assert read_result.success
    # Note: Truncation adds the message, so actual length will be slightly over 10KB
    assert "truncated" in read_result.output.lower()
    assert read_result.truncated


@pytest.mark.asyncio
async def test_concurrent_tool_execution(test_workspace):
    """Test concurrent tool execution."""
    import asyncio
    
    registry = get_global_registry()
    executor = ToolExecutor(registry)
    
    # Create multiple files concurrently
    tasks = []
    for i in range(5):
        file_path = test_workspace / f"file_{i}.txt"
        task = executor.execute(
            "write_file",
            path=str(file_path),
            content=f"Content {i}"
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # All should succeed
    assert all(r.success for r in results)
    
    # Verify all files exist
    for i in range(5):
        assert (test_workspace / f"file_{i}.txt").exists()


@pytest.mark.asyncio
async def test_tool_timeout(test_workspace):
    """Test tool execution timeout."""
    registry = get_global_registry()
    executor = ToolExecutor(registry)
    
    # Command that sleeps longer than timeout
    result = await executor.execute(
        "bash_execute",
        timeout=2,
        command="sleep 35"  # Longer than timeout
    )
    
    # Should timeout or be handled
    # Note: This test may need adjustment based on timeout implementation
    assert result.error is not None or "timeout" in result.output.lower()
