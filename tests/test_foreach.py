"""
foreachノードとLLMのJSON出力機能のテスト
"""
import json
import pytest
from unittest.mock import MagicMock, Mock, patch
from ai_agent_work_base.engine.loader import WorkflowLoader
from ai_agent_work_base.engine.executor import GraphExecutor
from ai_agent_work_base.skills.basic import EchoSkill


def make_mock_llm(responses: list):
    """複数のレスポンスを順番に返すモックLLMを作成する"""
    mock_llm = MagicMock()
    call_count = [0]

    def mock_chat_completion(messages, model=None, response_format=None, **kwargs):
        idx = call_count[0]
        call_count[0] += 1
        content = responses[idx] if idx < len(responses) else ""
        response = Mock()
        response.choices = [Mock(message=Mock(content=content))]
        return response

    mock_llm.chat_completion = mock_chat_completion
    return mock_llm


# -----------------------------------------------------------------------
# foreachノードの基本動作
# -----------------------------------------------------------------------

def test_foreach_with_skill():
    """foreachノードがリストの各要素に対してskillを実行するかテスト"""
    yaml_content = """
name: Foreach Test
nodes:
  - id: search_all
    type: foreach
    items: "{{inputs.queries}}"
    node:
      type: skill
      skill: echo
      params:
        message: "{{item}}"
    next: end
"""
    workflow = WorkflowLoader.load(yaml_content)
    executor = GraphExecutor(workflow, [EchoSkill()], MagicMock())

    result = executor.execute({"queries": ["query1", "query2", "query3"]})

    outputs = result["search_all"]["output"]
    assert isinstance(outputs, list)
    assert len(outputs) == 3
    assert outputs[0] == "query1"
    assert outputs[1] == "query2"
    assert outputs[2] == "query3"


def test_foreach_items_not_list_raises():
    """foreachのitemsがリストでない場合にValueErrorが発生するかテスト"""
    yaml_content = """
name: Foreach Error Test
nodes:
  - id: search_all
    type: foreach
    items: "{{inputs.not_a_list}}"
    node:
      type: skill
      skill: echo
      params:
        message: "{{item}}"
    next: end
"""
    workflow = WorkflowLoader.load(yaml_content)
    executor = GraphExecutor(workflow, [EchoSkill()], MagicMock())

    with pytest.raises(ValueError, match="リストではありません"):
        executor.execute({"not_a_list": "just a string"})


# -----------------------------------------------------------------------
# LLMのJSON出力対応
# -----------------------------------------------------------------------

def test_llm_json_output():
    """output_format: json のLLMノードがdictを返すかテスト"""
    yaml_content = """
name: JSON Output Test
nodes:
  - id: plan
    type: llm
    output_format: json
    prompt: "クエリを考えてください"
    next: end
"""
    json_response = json.dumps({"queries": ["q1", "q2", "q3"]})
    mock_llm = make_mock_llm([json_response])

    workflow = WorkflowLoader.load(yaml_content)
    executor = GraphExecutor(workflow, [], mock_llm)

    result = executor.execute({})

    output = result["plan"]["output"]
    assert isinstance(output, dict)
    assert output["queries"] == ["q1", "q2", "q3"]


def test_llm_json_output_passed_response_format():
    """output_format: json のとき response_format がLLMに渡されるかテスト"""
    yaml_content = """
name: JSON Format Test
nodes:
  - id: plan
    type: llm
    output_format: json
    prompt: "クエリを考えてください"
    next: end
"""
    json_response = json.dumps({"queries": ["q1"]})
    mock_llm = MagicMock()
    response = Mock()
    response.choices = [Mock(message=Mock(content=json_response))]
    mock_llm.chat_completion.return_value = response

    workflow = WorkflowLoader.load(yaml_content)
    executor = GraphExecutor(workflow, [], mock_llm)
    executor.execute({})

    call_kwargs = mock_llm.chat_completion.call_args[1]
    assert call_kwargs.get("response_format") == {"type": "json_object"}


def test_llm_invalid_json_raises():
    """output_format: json でLLMが不正なJSONを返した場合にValueErrorが発生するかテスト"""
    yaml_content = """
name: Invalid JSON Test
nodes:
  - id: plan
    type: llm
    output_format: json
    prompt: "クエリを考えてください"
    next: end
"""
    mock_llm = make_mock_llm(["これはJSONではありません"])

    workflow = WorkflowLoader.load(yaml_content)
    executor = GraphExecutor(workflow, [], mock_llm)

    with pytest.raises(ValueError, match="パースに失敗"):
        executor.execute({})


# -----------------------------------------------------------------------
# deep_researchワークフローの統合テスト
# -----------------------------------------------------------------------

class MockWebSearchSkill(EchoSkill):
    """テスト用のweb_searchモックスキル"""
    @property
    def name(self) -> str:
        return "web_search"

    def execute(self, query: str, **kwargs) -> str:
        return f"[Mock] {query} の検索結果"


def test_deep_research_workflow():
    """deep_research.yamlのforeachフローが正しく動作するかテスト"""
    workflow = WorkflowLoader.load("workflows/deep_research.yaml")

    queries = ["AI最新動向", "機械学習応用", "AI未来予測"]
    json_response = json.dumps({"queries": queries})
    # analyze_eachがforeachでLLMを3回呼ぶ + synthesizeで1回 = 計4回
    analysis_response = "- 発見事項1\n- 発見事項2"
    synthesis_response = "# AIレポート\n統合された深掘り分析です。"

    mock_llm = make_mock_llm([
        json_response,       # plan_research
        analysis_response,   # analyze_each[0]
        analysis_response,   # analyze_each[1]
        analysis_response,   # analyze_each[2]
        synthesis_response,  # synthesize
    ])

    executor = GraphExecutor(workflow, [MockWebSearchSkill()], mock_llm)

    result = executor.execute({"topic": "AI技術", "num_queries": 3})

    # plan_researchがJSONを返している
    assert isinstance(result["plan_research"]["output"], dict)
    assert result["plan_research"]["output"]["queries"] == queries

    # execute_searchesが3件の結果リストを返している
    search_outputs = result["execute_searches"]["output"]
    assert isinstance(search_outputs, list)
    assert len(search_outputs) == 3

    # analyze_eachが3件の分析リストを返している
    analysis_outputs = result["analyze_each"]["output"]
    assert isinstance(analysis_outputs, list)
    assert len(analysis_outputs) == 3

    # synthesizeが文字列を返している
    assert result["synthesize"]["output"] == synthesis_response
