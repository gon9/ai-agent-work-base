"""
SMTPを使用してメールを送信するスキル。

必要な環境変数:
    EMAIL_SMTP_HOST: SMTPサーバーホスト（例: smtp.gmail.com）
    EMAIL_SMTP_PORT: SMTPポート（例: 587）
    EMAIL_ADDRESS: 送信元メールアドレス
    EMAIL_PASSWORD: SMTPパスワードまたはアプリパスワード
"""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from .base import BaseSkill


class EmailSendSkill(BaseSkill):
    """
    SMTPを使用してメールを送信するスキル。

    Gmail利用時はアプリパスワードの設定が必要。
    EMAIL_SMTP_HOST / EMAIL_SMTP_PORT / EMAIL_ADDRESS / EMAIL_PASSWORD
    環境変数が必要。
    """

    def __init__(self) -> None:
        """SMTP接続情報を初期化する。"""
        self._host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        self._port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self._address = os.getenv("EMAIL_ADDRESS")
        self._password = os.getenv("EMAIL_PASSWORD")

    @property
    def name(self) -> str:
        return "email_send"

    @property
    def description(self) -> str:
        return (
            "SMTPを使用してメールを送信します。"
            "EMAIL_ADDRESS / EMAIL_PASSWORD / EMAIL_SMTP_HOST 環境変数が必要です。"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "送信先メールアドレス（複数の場合はカンマ区切り）",
                },
                "subject": {
                    "type": "string",
                    "description": "メール件名",
                },
                "body": {
                    "type": "string",
                    "description": "メール本文（Markdown可）",
                },
                "is_html": {
                    "type": "boolean",
                    "description": "本文をHTMLとして送信するか（デフォルト: false）",
                },
            },
            "required": ["to", "subject", "body"],
        }

    def execute(
        self,
        to: str,
        subject: str,
        body: str,
        is_html: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        SMTPサーバー経由でメールを送信する。

        Args:
            to: 送信先メールアドレス（カンマ区切りで複数指定可）
            subject: 件名
            body: 本文
            is_html: HTMLメールとして送信するか

        Returns:
            送信結果メッセージ
        """
        if not self._address:
            raise RuntimeError(
                "EMAIL_ADDRESS が設定されていません。.envファイルに追加してください。"
            )
        if not self._password:
            raise RuntimeError(
                "EMAIL_PASSWORD が設定されていません。.envファイルに追加してください。"
            )

        recipients = [addr.strip() for addr in to.split(",")]

        msg = MIMEMultipart("alternative")
        msg["From"] = self._address
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type, "utf-8"))

        with smtplib.SMTP(self._host, self._port) as server:
            server.ehlo()
            server.starttls()
            server.login(self._address, self._password)
            server.sendmail(self._address, recipients, msg.as_string())

        return f"メールを送信しました。宛先: {to} / 件名: {subject}"
