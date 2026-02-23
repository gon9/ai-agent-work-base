"""
pptxgenjsを使用してリッチなPowerPointファイルを生成するスキル。

LLMがpptxgenjsのNode.jsスクリプトを生成し、nodeコマンドで実行する方式。
LLMがレイアウト・デザイン・図表を自由にコード化できるため、
固定テンプレート方式より高品質なPPTXを生成できる。
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseSkill

# pptxgenjsのnode_modulesパス（スキルファイルと同階層のpptxjs_env/）
_PPTXJS_ENV = Path(__file__).parent / "pptxjs_env"
_NODE_MODULES = _PPTXJS_ENV / "node_modules"


class PptxJsGenerationSkill(BaseSkill):
    """
    LLMが生成したpptxgenjsスクリプトをNode.jsで実行してPPTXを生成するスキル。

    LLMがスライドのレイアウト・デザイン・図表をJavaScriptコードとして
    自由に表現できるため、固定テンプレート方式より高品質な出力が得られる。
    生成された.pptxファイルはPowerPoint/LibreOfficeで直接編集可能。
    """

    @property
    def name(self) -> str:
        return "generate_pptx_js"

    @property
    def description(self) -> str:
        return (
            "pptxgenjsのNode.jsスクリプトを受け取り、実行してPowerPoint(.pptx)ファイルを生成します。"
            "LLMが生成したスクリプトをそのまま実行するため、自由度の高いデザインが可能です。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": (
                        "pptxgenjsを使用したNode.jsスクリプト文字列。"
                        "pres.writeFile()で指定パスに保存すること。"
                        "require('pptxgenjs')で読み込み可能。"
                    ),
                },
                "file_path": {
                    "type": "string",
                    "description": "出力ファイルパス (例: output/presentation.pptx)",
                },
            },
            "required": ["script", "file_path"],
        }

    def execute(self, script: str, file_path: str, **kwargs) -> str:
        """
        pptxgenjsスクリプトをNode.jsで実行してPPTXを生成する。

        Args:
            script: pptxgenjsのNode.jsスクリプト文字列
            file_path: 出力ファイルパス

        Returns:
            生成結果メッセージ
        """
        # コードブロック除去（LLMがmarkdownで返す場合）
        script = re.sub(r"^```[a-zA-Z]*\n?", "", script.strip())
        script = re.sub(r"\n?```$", "", script.strip())

        # 出力ディレクトリ作成
        abs_file_path = os.path.abspath(file_path)
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)

        # スクリプト内のファイルパスを絶対パスに書き換え
        script = self._inject_file_path(script, abs_file_path)

        # 一時スクリプトファイルに書き出して実行
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(script)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["node", tmp_path],
                capture_output=True,
                text=True,
                timeout=60,
                env={
                    **os.environ,
                    "NODE_PATH": str(_NODE_MODULES),
                },
                cwd=str(_PPTXJS_ENV),
            )

            if result.returncode != 0:
                err = result.stderr.strip() or result.stdout.strip()
                return f"スクリプト実行エラー (exit {result.returncode}):\n{err}"

            if not os.path.exists(abs_file_path):
                stdout = result.stdout.strip()
                return (
                    f"スクリプトは正常終了しましたが、ファイルが生成されませんでした: {abs_file_path}\n"
                    f"stdout: {stdout}"
                )

            size_kb = os.path.getsize(abs_file_path) // 1024
            return f"PowerPointファイルを生成しました: {file_path} ({size_kb}KB)"

        except subprocess.TimeoutExpired:
            return "スクリプト実行がタイムアウトしました（60秒）"
        except FileNotFoundError:
            return "nodeコマンドが見つかりません。Node.jsがインストールされているか確認してください。"
        finally:
            os.unlink(tmp_path)

    def _inject_file_path(self, script: str, abs_file_path: str) -> str:
        """
        スクリプト内のwriteFile呼び出しを絶対パスに書き換える。

        LLMが相対パスや仮のパスを使っている場合に対応する。
        """
        escaped = abs_file_path.replace("\\", "\\\\")

        # writeFile({ fileName: "..." }) 形式
        script = re.sub(
            r'writeFile\s*\(\s*\{[^}]*fileName\s*:\s*["\'][^"\']*["\'][^}]*\}\s*\)',
            f'writeFile({{ fileName: "{escaped}" }})',
            script,
        )
        # writeFile("...") 形式
        script = re.sub(
            r'writeFile\s*\(\s*["\'][^"\']*["\']\s*\)',
            f'writeFile("{escaped}")',
            script,
        )
        return script
