import pytest
from unittest.mock import MagicMock, Mock
from ai_agent_work_base.planning.models import WorkflowPlan, TaskStep
from ai_agent_work_base.planning.planner import Planner
from ai_agent_work_base.planning.executor import PlanExecutor
from ai_agent_work_base.tools.basic_tools import EchoTool

def test_planner_create_plan():
    """Plannerが正しくWorkflowPlanを生成できるかテスト"""
    mock_llm = MagicMock()
    mock_response = Mock()
    mock_message = Mock()
    
    # LLMが返すJSONモック
    plan_json = """
    {
        "goal": "Test Goal",
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
    mock_message.content = plan_json
    mock_response.choices = [Mock(message=mock_message)]
    mock_llm.chat_completion.return_value = mock_response

    planner = Planner(llm_client=mock_llm, tools=[EchoTool()])
    plan = planner.create_plan("Say hello")
    
    assert plan.goal == "Test Goal"
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "echo_tool"
    assert plan.steps[0].arguments["message"] == "hello"

def test_executor_execute_simple():
    """Executorが単純なプランを実行できるかテスト"""
    echo_tool = EchoTool()
    executor = PlanExecutor(tools=[echo_tool])
    
    plan = WorkflowPlan(
        goal="Simple Echo",
        steps=[
            TaskStep(
                step_id=1,
                description="Echo step",
                tool_name="echo_tool",
                arguments={"message": "hello"},
                dependencies=[]
            )
        ]
    )
    
    results = executor.execute(plan)
    assert results[1] == "hello"

def test_executor_execute_with_dependency():
    """依存関係（変数置換）を含むプランの実行テスト"""
    echo_tool = EchoTool()
    executor = PlanExecutor(tools=[echo_tool])
    
    # Step 1: Echo "hello"
    # Step 2: Echo "{step_1_result} world" -> "hello world"
    plan = WorkflowPlan(
        goal="Dependency Test",
        steps=[
            TaskStep(
                step_id=1,
                description="First echo",
                tool_name="echo_tool",
                arguments={"message": "hello"},
                dependencies=[]
            ),
            TaskStep(
                step_id=2,
                description="Second echo with dependency",
                tool_name="echo_tool",
                arguments={"message": "{step_1_result} world"},
                dependencies=[1]
            )
        ]
    )
    
    results = executor.execute(plan)
    assert results[1] == "hello"
    assert results[2] == "hello world"
