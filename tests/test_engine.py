import pytest
from unittest.mock import MagicMock, Mock
from ai_agent_work_base.schemas.workflow import WorkflowDefinition
from ai_agent_work_base.engine.context import WorkflowContext
from ai_agent_work_base.engine.executor import GraphExecutor
from ai_agent_work_base.skills.base import BaseSkill

class MockSkill(BaseSkill):
    @property
    def name(self): return "mock_skill"
    @property
    def description(self): return "mock"
    @property
    def parameters(self): return {}
    def execute(self, **kwargs):
        return f"executed with {kwargs}"

def test_context_resolution():
    context = WorkflowContext({"topic": "AI"})
    context.set_step_output("step1", {"result": "ok"})
    
    # テンプレート置換
    assert context.resolve_template("Research about {{inputs.topic}}") == "Research about AI"
    
    # 値の解決 (辞書内)
    data = {"query": "{{inputs.topic}}", "prev": "{{step1.output.result}}"}
    resolved = context.resolve_value(data)
    assert resolved["query"] == "AI"
    assert resolved["prev"] == "ok"

def test_executor_simple_flow():
    # モックLLM
    mock_llm = MagicMock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="LLM Result"))]
    mock_llm.chat_completion.return_value = mock_response

    # 定義
    yaml_content = """
    name: Test Flow
    nodes:
      - id: step1
        type: llm
        prompt: "Hello {{inputs.name}}"
        next: step2
      - id: step2
        type: skill
        skill: mock_skill
        params:
            arg: "{{step1.output}}"
        next: end
    """
    
    from ai_agent_work_base.engine.loader import WorkflowLoader
    workflow = WorkflowLoader.load(yaml_content)
    
    skill = MockSkill()
    executor = GraphExecutor(workflow, [skill], mock_llm)
    
    result = executor.execute({"name": "User"})
    
    # contextの状態を確認
    assert result["step1"]["output"] == "LLM Result"
    assert result["step2"]["output"] == "executed with {'arg': 'LLM Result'}"
