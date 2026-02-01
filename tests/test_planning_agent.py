import pytest
from unittest.mock import MagicMock, Mock
from ai_agent_work_base.planning.agent import PlanningAgent
from ai_agent_work_base.planning.models import WorkflowPlan, TaskStep
from ai_agent_work_base.tools.basic_tools import EchoTool

def test_planning_agent_run():
    """PlanningAgentの正常系実行テスト"""
    mock_llm = MagicMock()
    
    # 1. Planner.create_plan 用のモックレスポンス
    mock_plan_message = Mock()
    mock_plan_message.content = """
    {
        "goal": "Echo hello",
        "steps": [
            {
                "step_id": 1,
                "description": "Echo hello",
                "tool_name": "echo_tool",
                "arguments": {"message": "hello"},
                "dependencies": []
            }
        ]
    }
    """
    mock_response_plan = Mock()
    mock_response_plan.choices = [Mock(message=mock_plan_message)]

    # 2. _generate_final_response 用のモックレスポンス
    mock_final_message = Mock()
    mock_final_message.content = "実行が完了しました。helloと返されました。"
    mock_response_final = Mock()
    mock_response_final.choices = [Mock(message=mock_final_message)]

    # side_effectで順に返す
    mock_llm.chat_completion.side_effect = [mock_response_plan, mock_response_final]

    agent = PlanningAgent(llm_client=mock_llm, tools=[EchoTool()])
    response = agent.run("say hello")
    
    assert response == "実行が完了しました。helloと返されました。"
    assert mock_llm.chat_completion.call_count == 2
