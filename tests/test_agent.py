import pytest
from unittest.mock import MagicMock, Mock
from ai_agent_work_base.core.agent import Agent
from ai_agent_work_base.tools.basic_tools import EchoTool

def test_agent_run_simple_response():
    """ツール呼び出しなしで回答する場合のテスト"""
    mock_llm = MagicMock()
    # モックレスポンスの構築
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = "Hello there!"
    mock_message.tool_calls = None
    mock_message.role = "assistant" # role属性が必要
    mock_response.choices = [Mock(message=mock_message)]
    
    mock_llm.chat_completion.return_value = mock_response

    agent = Agent(llm_client=mock_llm, tools=[])
    response = agent.run("Hello")
    
    assert response == "Hello there!"
    mock_llm.chat_completion.assert_called_once()

def test_agent_run_with_tool():
    """ツール呼び出しを含む場合のテスト"""
    mock_llm = MagicMock()
    echo_tool = EchoTool()
    
    # 1回目のレスポンス: ツール呼び出し要求
    mock_response1 = Mock()
    mock_message1 = Mock()
    mock_message1.content = None
    mock_message1.role = "assistant"
    
    mock_tool_call = Mock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "echo_tool"
    mock_tool_call.function.arguments = '{"message": "test echo"}'
    
    mock_message1.tool_calls = [mock_tool_call]
    mock_response1.choices = [Mock(message=mock_message1)]

    # 2回目のレスポンス: 最終回答
    mock_response2 = Mock()
    mock_message2 = Mock()
    mock_message2.content = "I echoed: test echo"
    mock_message2.tool_calls = None
    mock_message2.role = "assistant"
    mock_response2.choices = [Mock(message=mock_message2)]

    # side_effectで呼び出しごとに異なるレスポンスを返す
    mock_llm.chat_completion.side_effect = [mock_response1, mock_response2]

    agent = Agent(llm_client=mock_llm, tools=[echo_tool])
    response = agent.run("Please echo 'test echo'")
    
    assert response == "I echoed: test echo"
    assert mock_llm.chat_completion.call_count == 2
