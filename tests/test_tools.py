import os
import pytest
from ai_agent_work_base.tools.file_tools import FileWriteTool, FileReadTool
from ai_agent_work_base.tools.math_tools import CalculatorTool

def test_calculator_tool():
    tool = CalculatorTool()
    assert tool.execute("2 + 2") == "4"
    assert tool.execute("10 * 5") == "50"
    assert "Error" in tool.execute("2 + abc") # Invalid input

def test_file_tools(tmp_path):
    # tmp_path は pytest の fixture で一時ディレクトリを提供
    file_path = tmp_path / "test_file.txt"
    file_path_str = str(file_path)
    
    write_tool = FileWriteTool()
    read_tool = FileReadTool()
    
    # 書き込みテスト
    result_write = write_tool.execute(file_path=file_path_str, content="Hello World")
    assert "Successfully wrote" in result_write
    assert os.path.exists(file_path_str)
    
    # 読み込みテスト
    content = read_tool.execute(file_path=file_path_str)
    assert content == "Hello World"

def test_file_read_non_existent():
    read_tool = FileReadTool()
    result = read_tool.execute(file_path="/path/to/non/existent/file.txt")
    assert "Error" in result
