import io
import logging
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, Optional

from ..core.llm import LLMClient
from .base import BaseSkill

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
あなたはPythonデバッグの専門家です。
与えられたコードとエラーメッセージを分析し、修正済みのPythonコードのみを返してください。
出力はコードブロック（```python ... ```）で囲んでください。説明は不要です。
"""

_USER_PROMPT_TEMPLATE = """\
## 実行したコード
```python
{code}
```

## 発生したエラー
```
{error}
```

修正済みのコードを返してください。
"""


def _extract_code(text: str) -> str:
    """LLMレスポンスからコードブロックを抽出する。"""
    import re

    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _run_code(code: str) -> tuple[bool, str]:
    """
    コードを安全に実行し、(成功フラグ, 出力/エラー文字列) を返す。

    Returns:
        tuple[bool, str]: (成功したか, stdout/stderrの内容またはエラートレースバック)
    """
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(code, {})  # noqa: S102
        output = stdout_buf.getvalue() + stderr_buf.getvalue()
        return True, output
    except Exception:
        tb = traceback.format_exc()
        return False, tb


class SelfDebugSkill(BaseSkill):
    """
    自己デバッグループスキル。

    コードとエラーメッセージを受け取り、LLMを使って修正→再実行を繰り返す。
    エラーがなくなるか最大試行回数に達したら終了し、最終コードと結果を返す。
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Args:
            llm_client: 使用するLLMクライアント。省略時は新規作成。
        """
        self._llm = llm_client or LLMClient()

    @property
    def name(self) -> str:
        return "self_debug"

    @property
    def description(self) -> str:
        return (
            "Pythonコードとエラーメッセージを受け取り、LLMによる修正→再実行を繰り返す"
            "自己デバッグループを実行します。修正済みコードと実行結果を返します。"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "デバッグ対象のPythonコード。",
                },
                "error": {
                    "type": "string",
                    "description": "最初に発生したエラーメッセージ（省略時は空文字）。",
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "最大デバッグ試行回数（デフォルト: 5）。",
                },
            },
            "required": ["code"],
        }

    def execute(
        self,
        code: str,
        error: str = "",
        max_iterations: int = 5,
        **kwargs,
    ) -> str:
        """
        自己デバッグループを実行する。

        Args:
            code: デバッグ対象のPythonコード。
            error: 最初のエラーメッセージ（省略時は空文字。空の場合はまず実行して確認）。
            max_iterations: 最大試行回数。

        Returns:
            str: 実行結果サマリー（最終コード・ステータス・ループ回数を含む）。
        """
        current_code = code
        current_error = error

        # errorが空の場合はまず実行してみる
        if not current_error:
            success, output = _run_code(current_code)
            if success:
                return self._format_result(
                    current_code, output, iteration=0, success=True
                )
            current_error = output

        for iteration in range(1, max_iterations + 1):
            logger.info(f"[SelfDebug] iteration={iteration}, エラー修正中...")

            prompt = _USER_PROMPT_TEMPLATE.format(
                code=current_code, error=current_error
            )
            response = self._llm.chat_completion(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            fixed_code = _extract_code(response.choices[0].message.content)

            success, output = _run_code(fixed_code)
            current_code = fixed_code

            if success:
                logger.info(f"[SelfDebug] iteration={iteration} で修正成功")
                return self._format_result(
                    current_code, output, iteration=iteration, success=True
                )

            current_error = output
            logger.warning(f"[SelfDebug] iteration={iteration} でもエラー継続: {output[:200]}")

        # 上限到達
        return self._format_result(
            current_code, current_error, iteration=max_iterations, success=False
        )

    @staticmethod
    def _format_result(code: str, output: str, iteration: int, success: bool) -> str:
        """結果を人間が読みやすい文字列にフォーマットする。"""
        status = "SUCCESS" if success else "FAILED (max iterations reached)"
        return (
            f"[SelfDebug] status={status}, iterations={iteration}\n\n"
            f"## 最終コード\n```python\n{code}\n```\n\n"
            f"## 実行結果\n```\n{output or '(出力なし)'}\n```"
        )
