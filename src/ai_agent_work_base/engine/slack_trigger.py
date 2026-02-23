"""
Slack Boltを使用したSlackトリガー。

Slackのメッセージイベントを受信してワークフローを起動する。
Socket Modeで動作するため、パブリックなURLは不要。

必要な環境変数:
    SLACK_BOT_TOKEN: xoxb- で始まるBotトークン
    SLACK_APP_TOKEN: xapp- で始まるApp-Level Token（Socket Mode用）

Slack App設定:
    - Socket Mode: 有効
    - Event Subscriptions: message.channels または message.im を購読
    - Bot Token Scopes: chat:write, channels:history, im:history
"""

from __future__ import annotations

import logging
import os
import re
import threading
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class SlackTriggerApp:
    """
    Slack Boltを使用してSlackメッセージからワークフローを起動するアプリ。

    メッセージ形式:
        /run <ワークフロー名> [入力値...]
        例: /run daily_news topic=AIニュース
        例: /run presentation topic=量子コンピュータ num_slides=8

    使用例:
        app = SlackTriggerApp(
            workflows_dir=Path("workflows"),
            llm_client=llm_client,
            skills=skills,
        )
        app.start()  # ブロッキング実行
    """

    def __init__(
        self,
        workflows_dir: Path,
        llm_client: Any,
        skills: List[Any],
        bot_token: Optional[str] = None,
        app_token: Optional[str] = None,
    ) -> None:
        """
        Args:
            workflows_dir: workflows/ディレクトリのパス
            llm_client: LLMクライアントインスタンス
            skills: 利用可能なスキルのリスト
            bot_token: Slack Bot Token（省略時は環境変数SLACK_BOT_TOKENを使用）
            app_token: Slack App Token（省略時は環境変数SLACK_APP_TOKENを使用）
        """
        self._workflows_dir = workflows_dir
        self._llm_client = llm_client
        self._skills = skills
        self._bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self._app_token = app_token or os.getenv("SLACK_APP_TOKEN")

    def _build_app(self) -> Any:
        """Slack Boltアプリを構築する。"""
        try:
            from slack_bolt import App
            from slack_bolt.adapter.socket_mode import SocketModeHandler
        except ImportError:
            raise RuntimeError(
                "slack-boltがインストールされていません。: uv add slack-bolt"
            )

        if not self._bot_token:
            raise RuntimeError(
                "SLACK_BOT_TOKEN が設定されていません。.envファイルに追加してください。"
            )
        if not self._app_token:
            raise RuntimeError(
                "SLACK_APP_TOKEN が設定されていません。.envファイルに追加してください。"
            )

        app = App(token=self._bot_token)

        @app.message(re.compile(r"^/run\s+(\S+)(.*)$"))
        def handle_run_command(message: dict, say: Any, context: Any) -> None:
            """
            /run <workflow> [key=value ...] 形式のメッセージを処理する。
            """
            matches = context["matches"]
            workflow_name = matches[0].strip()
            args_str = matches[1].strip() if len(matches) > 1 else ""

            # key=value 形式の引数をパース
            inputs: dict[str, str] = {}
            for pair in re.findall(r"(\w+)=([^\s]+)", args_str):
                inputs[pair[0]] = pair[1]

            say(f"⏳ ワークフロー `{workflow_name}` を実行中... 入力: {inputs or '(なし)'}")

            def run_in_thread() -> None:
                try:
                    from .loader import WorkflowLoader
                    from .executor import GraphExecutor

                    workflow_path = self._workflows_dir / f"{workflow_name}.yaml"
                    if not workflow_path.exists():
                        say(f"❌ ワークフロー `{workflow_name}` が見つかりません。")
                        return

                    workflow = WorkflowLoader.load(workflow_path)
                    executor = GraphExecutor(workflow, self._skills, self._llm_client)
                    result = executor.execute(inputs)

                    # 最終ノードの出力を取得して返信
                    last_output = ""
                    for node in reversed(workflow.nodes):
                        val = result.get(node.id, {}).get("output")
                        if val:
                            last_output = str(val)[:500]
                            break

                    say(f"✅ `{workflow_name}` 完了！\n```\n{last_output}\n```")

                except Exception as e:
                    logger.exception(f"ワークフロー実行エラー: {e}")
                    say(f"❌ 実行エラー: {e}")

            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()

        @app.message(re.compile(r"^/workflows$"))
        def handle_list_workflows(message: dict, say: Any) -> None:
            """利用可能なワークフロー一覧を返す。"""
            from .loader import WorkflowLoader

            lines = ["📋 *利用可能なワークフロー:*"]
            for path in sorted(self._workflows_dir.glob("*.yaml")):
                try:
                    wf = WorkflowLoader.load(path)
                    inputs_str = ", ".join(
                        i.name for i in (wf.inputs or [])
                    )
                    lines.append(f"• `{path.stem}` — {wf.description or wf.name} (入力: {inputs_str or 'なし'})")
                except Exception:
                    lines.append(f"• `{path.stem}` (読み込みエラー)")
            say("\n".join(lines))

        return app, SocketModeHandler

    def start(self) -> None:
        """
        Socket ModeでSlack Boltアプリを起動する（ブロッキング）。
        """
        app, SocketModeHandler = self._build_app()
        handler = SocketModeHandler(app, self._app_token)
        logger.info("Slack Triggerアプリを起動しました。Ctrl+C で停止。")
        handler.start()
