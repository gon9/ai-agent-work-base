import pytest
from ai_agent_work_base.tools.basic_tools import EchoTool, ReverseTool
from ai_agent_work_base.workflow.sequential_workflow import SequentialWorkflow

def test_echo_tool():
    """EchoToolの正常系テスト"""
    tool = EchoTool()
    assert tool.name == "echo_tool"
    assert tool.execute(message="hello") == "hello"

def test_reverse_tool():
    """ReverseToolの正常系テスト"""
    tool = ReverseTool()
    assert tool.name == "reverse_tool"
    assert tool.execute(text="hello") == "olleh"

def test_sequential_workflow():
    """SequentialWorkflowの正常系テスト"""
    echo = EchoTool()
    reverse = ReverseTool()
    
    # ワークフロー構築: Echo -> Reverse
    workflow = SequentialWorkflow(tools=[echo, reverse])
    
    # "hello" -> echo -> "hello" -> reverse -> "olleh"
    result = workflow.run("hello")
    assert result == "olleh"

def test_workflow_add_step_error():
    """登録されていないツールを追加しようとした時のエラーテスト"""
    workflow = SequentialWorkflow()
    with pytest.raises(ValueError):
        workflow.add_step("non_existent_tool")
