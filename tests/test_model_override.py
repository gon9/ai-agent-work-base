import pytest
from unittest.mock import MagicMock, Mock
from ai_agent_work_base.engine.loader import WorkflowLoader
from ai_agent_work_base.engine.executor import GraphExecutor
from ai_agent_work_base.skills.basic import EchoSkill

def test_llm_node_with_model_override():
    """LLMノードでモデル指定が正しく動作するかテスト"""
    mock_llm = MagicMock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test Result"))]
    mock_llm.chat_completion.return_value = mock_response

    yaml_content = """
    name: Model Test Flow
    nodes:
      - id: step1
        type: llm
        model: gpt-4o-mini
        prompt: "Test prompt"
        next: end
    """
    
    workflow = WorkflowLoader.load(yaml_content)
    executor = GraphExecutor(workflow, [], mock_llm)
    
    result = executor.execute({})
    
    # モデル指定が正しく渡されたか確認
    mock_llm.chat_completion.assert_called_once()
    call_args = mock_llm.chat_completion.call_args
    assert call_args[1]["model"] == "gpt-4o-mini"
    assert result["step1"]["output"] == "Test Result"

def test_llm_node_without_model():
    """モデル指定なしの場合、デフォルトモデルが使用されるかテスト"""
    mock_llm = MagicMock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test Result"))]
    mock_llm.chat_completion.return_value = mock_response

    yaml_content = """
    name: Default Model Test
    nodes:
      - id: step1
        type: llm
        prompt: "Test prompt"
        next: end
    """
    
    workflow = WorkflowLoader.load(yaml_content)
    executor = GraphExecutor(workflow, [], mock_llm)
    
    result = executor.execute({})
    
    # model=Noneが渡されることを確認
    mock_llm.chat_completion.assert_called_once()
    call_args = mock_llm.chat_completion.call_args
    assert call_args[1]["model"] is None
