"""
トリガー定義のスキーマ。

triggers/配下のYAMLファイルを読み込むためのPydanticモデル。
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class CronTriggerConfig(BaseModel):
    """cronスケジュールトリガーの設定。"""

    type: Literal["cron"]
    schedule: str = Field(..., description="cron式 (例: '0 7 * * *' = 毎朝7時)")


class SlackTriggerConfig(BaseModel):
    """Slackメッセージトリガーの設定。"""

    type: Literal["slack"]
    keyword: Optional[str] = Field(None, description="トリガーするキーワード（省略時は全メッセージ）")
    channel: Optional[str] = Field(None, description="監視するチャンネルID（省略時は全チャンネル）")


class WebhookTriggerConfig(BaseModel):
    """HTTPウェブフックトリガーの設定。"""

    type: Literal["webhook"]
    path: str = Field(..., description="ウェブフックのパス (例: /triggers/news)")


TriggerConfig = CronTriggerConfig | SlackTriggerConfig | WebhookTriggerConfig


class TriggerDefinition(BaseModel):
    """
    トリガー定義。triggers/配下のYAMLファイルに対応する。

    Example YAML:
        name: "Morning News"
        workflow: "daily_news"
        trigger:
          type: "cron"
          schedule: "0 7 * * *"
        inputs:
          topic: "今日のテクノロジーニュース"
    """

    name: str = Field(..., description="トリガーの名前")
    workflow: str = Field(..., description="実行するワークフロー名（workflows/配下のファイル名）")
    trigger: Dict[str, Any] = Field(..., description="トリガー設定")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="ワークフローに渡す入力値")
    enabled: bool = Field(default=True, description="トリガーの有効/無効")
