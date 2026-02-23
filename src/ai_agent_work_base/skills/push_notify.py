"""
LINE Messaging APIを使用してLINEにメッセージをプッシュ送信するスキル。

必要な環境変数:
    LINE_CHANNEL_ACCESS_TOKEN: LINE Messaging APIのチャンネルアクセストークン
    LINE_USER_ID: 送信先のユーザーID（Uで始まる文字列）またはグループID

セットアップ:
    1. LINE Developers (https://developers.line.biz) でチャンネルを作成
    2. Messaging API チャンネルのチャンネルアクセストークンを発行
    3. 送信先ユーザーIDはLINE Official Account Managerまたは
       Webhookのuserイベントから取得
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .base import BaseSkill

_LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"


class PushNotifySkill(BaseSkill):
    """
    LINE Messaging APIのBroadcast APIを使用してLINEに通知を送信するスキル。

    Botと友達になっている全ユーザーに送信する（無料プラン対応）。
    LINE_CHANNEL_ACCESS_TOKEN環境変数のみ必要。
    テキストメッセージとして送信する。5000文字を超える場合は自動分割。
    """

    def __init__(self) -> None:
        """LINE認証情報を初期化する。"""
        self._token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

    @property
    def name(self) -> str:
        return "push_notify"

    @property
    def description(self) -> str:
        return (
            "LINE Messaging APIのBroadcast APIを使用してLINEに通知を送信します。"
            "LINE_CHANNEL_ACCESS_TOKEN環境変数が必要です（無料プラン対応）。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "送信するメッセージ本文",
                },
                "title": {
                    "type": "string",
                    "description": "メッセージの先頭に付けるタイトル（省略可）",
                },
            },
            "required": ["message"],
        }

    def execute(
        self,
        message: str,
        title: str = "",
        **kwargs: Any,
    ) -> str:
        """
        LINE Messaging APIのbroadcastエンドポイントにメッセージを送信する。

        Args:
            message: 送信するメッセージ本文
            title: 先頭に付けるタイトル（省略可）

        Returns:
            送信結果メッセージ
        """
        if not self._token:
            raise RuntimeError(
                "LINE_CHANNEL_ACCESS_TOKEN が設定されていません。.envファイルに追加してください。"
            )

        # タイトルがある場合は先頭に付与
        full_text = f"【{title}】\n{message}" if title else message

        # LINEのテキストメッセージは5000文字制限のため分割
        chunks = [full_text[i:i + 4900] for i in range(0, len(full_text), 4900)]
        messages = [{"type": "text", "text": chunk} for chunk in chunks[:5]]  # 最大5件/リクエスト

        payload = {
            "messages": messages,
        }

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            _LINE_BROADCAST_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._token}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            raise RuntimeError(f"LINE送信に失敗しました。status={e.code}, body={body}") from e

        if status == 200:
            return f"LINEへの送信が完了しました。{'タイトル: ' + title if title else 'メッセージ: ' + message[:30]}"
        else:
            raise RuntimeError(f"LINE送信に失敗しました。status={status}, body={body}")
