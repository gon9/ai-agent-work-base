import os
from typing import Any, Dict
from dotenv import load_dotenv
from .base import BaseSkill

load_dotenv()


class SlackNotifySkill(BaseSkill):
    """
    Slack Incoming Webhookを使用してメッセージを送信するスキル。
    SLACK_WEBHOOK_URL環境変数が必要。
    """

    def __init__(self):
        """Slack Webhook URLを初期化する。"""
        self._webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    @property
    def name(self) -> str:
        return "slack_notify"

    @property
    def description(self) -> str:
        return "指定されたメッセージをSlackチャンネルに送信します。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "送信するメッセージ本文"
                },
                "title": {
                    "type": "string",
                    "description": "メッセージのタイトル（省略可）"
                },
                "channel": {
                    "type": "string",
                    "description": "送信先チャンネル（省略時はWebhookのデフォルトチャンネル）"
                }
            },
            "required": ["message"]
        }

    def execute(self, message: str, title: str = "", channel: str = "", **kwargs) -> str:
        """SlackにメッセージをPOSTし、結果を返す。"""
        if not self._webhook_url:
            raise RuntimeError(
                "SLACK_WEBHOOK_URL が設定されていません。.envファイルに追加してください。"
            )

        import urllib.request
        import json

        blocks = []
        if title:
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": title}
            })
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": message}
        })

        payload: Dict[str, Any] = {"blocks": blocks}
        if channel:
            payload["channel"] = channel

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")

        if status == 200 and body == "ok":
            return f"Slackへの送信が完了しました。{'タイトル: ' + title if title else ''}"
        else:
            raise RuntimeError(f"Slack送信に失敗しました。status={status}, body={body}")
