"""SelfDebugSkillのユニットテスト（正常系・異常系）"""
import pytest
from unittest.mock import MagicMock, patch
from ai_agent_work_base.skills.self_debug import SelfDebugSkill, _extract_code, _run_code


# -----------------------------------------------------------------------
# ヘルパー関数のテスト
# -----------------------------------------------------------------------


def test_extract_code_with_python_block():
    """```python ... ``` ブロックからコードを抽出できる"""
    text = "```python\nprint('hello')\n```"
    assert _extract_code(text) == "print('hello')"


def test_extract_code_with_plain_block():
    """``` ... ``` ブロック（言語指定なし）からコードを抽出できる"""
    text = "```\nprint('hello')\n```"
    assert _extract_code(text) == "print('hello')"


def test_extract_code_without_block():
    """コードブロックがない場合はテキストをそのまま返す"""
    text = "print('hello')"
    assert _extract_code(text) == "print('hello')"


def test_run_code_success():
    """正常なコードは (True, stdout) を返す"""
    success, output = _run_code("print('ok')")
    assert success is True
    assert "ok" in output


def test_run_code_failure():
    """エラーのあるコードは (False, traceback) を返す"""
    success, output = _run_code("raise ValueError('bad')")
    assert success is False
    assert "ValueError" in output


# -----------------------------------------------------------------------
# 正常系
# -----------------------------------------------------------------------


def _make_llm_mock(fixed_code: str) -> MagicMock:
    """指定コードを返すLLMモックを作成する。"""
    llm = MagicMock()
    choice = MagicMock()
    choice.message.content = f"```python\n{fixed_code}\n```"
    llm.chat_completion.return_value.choices = [choice]
    return llm


def test_execute_no_error_runs_immediately():
    """errorが空でコードが正常なら、LLMを呼ばずに即成功する"""
    llm = MagicMock()
    skill = SelfDebugSkill(llm_client=llm)
    result = skill.execute(code="x = 1 + 1")
    assert "SUCCESS" in result
    assert "iterations=0" in result
    llm.chat_completion.assert_not_called()


def test_execute_fixes_on_first_iteration():
    """1回目のLLM修正でエラーが解消される"""
    fixed_code = "print('fixed')"
    llm = _make_llm_mock(fixed_code)
    skill = SelfDebugSkill(llm_client=llm)

    result = skill.execute(
        code="raise RuntimeError('oops')",
        error="RuntimeError: oops",
    )

    assert "SUCCESS" in result
    assert "iterations=1" in result
    assert fixed_code in result
    llm.chat_completion.assert_called_once()


def test_execute_fixes_on_second_iteration():
    """2回目のLLM修正でエラーが解消される"""
    llm = MagicMock()
    # 1回目は壊れたコード、2回目は正常コードを返す
    bad_choice = MagicMock()
    bad_choice.message.content = "```python\nraise ValueError('still bad')\n```"
    good_choice = MagicMock()
    good_choice.message.content = "```python\nprint('ok')\n```"
    llm.chat_completion.side_effect = [
        MagicMock(choices=[bad_choice]),
        MagicMock(choices=[good_choice]),
    ]

    skill = SelfDebugSkill(llm_client=llm)
    result = skill.execute(
        code="raise ValueError('bad')",
        error="ValueError: bad",
        max_iterations=5,
    )

    assert "SUCCESS" in result
    assert "iterations=2" in result
    assert llm.chat_completion.call_count == 2


def test_execute_with_no_initial_error_but_code_fails():
    """errorが空でもコードが失敗する場合はデバッグループに入る"""
    fixed_code = "print('repaired')"
    llm = _make_llm_mock(fixed_code)
    skill = SelfDebugSkill(llm_client=llm)

    result = skill.execute(code="1 / 0")  # ZeroDivisionError

    assert "SUCCESS" in result
    llm.chat_completion.assert_called_once()


# -----------------------------------------------------------------------
# 異常系
# -----------------------------------------------------------------------


def test_execute_max_iterations_reached():
    """最大試行回数に達してもエラーが解消されない場合はFAILEDを返す"""
    llm = MagicMock()
    choice = MagicMock()
    choice.message.content = "```python\nraise RuntimeError('still broken')\n```"
    llm.chat_completion.return_value = MagicMock(choices=[choice])

    skill = SelfDebugSkill(llm_client=llm)
    result = skill.execute(
        code="raise RuntimeError('broken')",
        error="RuntimeError: broken",
        max_iterations=3,
    )

    assert "FAILED" in result
    assert "iterations=3" in result
    assert llm.chat_completion.call_count == 3


def test_skill_name():
    """スキル名が正しく返される"""
    skill = SelfDebugSkill(llm_client=MagicMock())
    assert skill.name == "self_debug"


def test_skill_parameters_required():
    """parametersにcodeが必須として含まれる"""
    skill = SelfDebugSkill(llm_client=MagicMock())
    params = skill.parameters
    assert "code" in params["properties"]
    assert "code" in params["required"]


def test_skill_parameters_optional_fields():
    """error と max_iterations はオプションパラメータとして定義されている"""
    skill = SelfDebugSkill(llm_client=MagicMock())
    props = skill.parameters["properties"]
    assert "error" in props
    assert "max_iterations" in props
    assert "error" not in skill.parameters["required"]
    assert "max_iterations" not in skill.parameters["required"]
