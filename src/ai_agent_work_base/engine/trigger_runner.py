"""
トリガーランナー。

triggers/配下のYAMLを読み込み、cronスケジュールやSlack/Webhookイベントに
応じてワークフローを自動実行する。
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from ..schemas.trigger import TriggerDefinition
from .loader import WorkflowLoader
from .executor import GraphExecutor

logger = logging.getLogger(__name__)


class TriggerRunner:
    """
    トリガー定義を読み込み、スケジュール実行・イベント駆動実行を管理するクラス。

    使用例:
        runner = TriggerRunner(
            triggers_dir=Path("triggers"),
            workflows_dir=Path("workflows"),
            llm_client=llm_client,
            skills=skills,
        )
        runner.start()  # バックグラウンドでcronを開始
    """

    def __init__(
        self,
        triggers_dir: Path,
        workflows_dir: Path,
        llm_client: Any,
        skills: List[Any],
        on_workflow_start: Optional[Callable[[str, str], None]] = None,
        on_workflow_end: Optional[Callable[[str, str, Any], None]] = None,
    ) -> None:
        """
        Args:
            triggers_dir: triggers/ディレクトリのパス
            workflows_dir: workflows/ディレクトリのパス
            llm_client: LLMクライアントインスタンス
            skills: 利用可能なスキルのリスト
            on_workflow_start: ワークフロー開始時コールバック(trigger_name, workflow_name)
            on_workflow_end: ワークフロー終了時コールバック(trigger_name, workflow_name, result)
        """
        self._triggers_dir = triggers_dir
        self._workflows_dir = workflows_dir
        self._llm_client = llm_client
        self._skills = skills
        self._on_workflow_start = on_workflow_start
        self._on_workflow_end = on_workflow_end
        self._cron_threads: List[threading.Timer] = []
        self._running = False

    def load_triggers(self) -> List[TriggerDefinition]:
        """triggers/配下の全YAMLファイルを読み込む。"""
        triggers = []
        if not self._triggers_dir.exists():
            return triggers
        for path in sorted(self._triggers_dir.glob("*.yaml")):
            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                trigger = TriggerDefinition(**data)
                if trigger.enabled:
                    triggers.append(trigger)
                    logger.info(f"トリガー読み込み: {trigger.name} ({path.name})")
            except Exception as e:
                logger.error(f"トリガー読み込みエラー {path.name}: {e}")
        return triggers

    def run_workflow(self, trigger: TriggerDefinition) -> Any:
        """
        指定トリガーのワークフローを同期実行する。

        Args:
            trigger: 実行するトリガー定義

        Returns:
            ワークフロー実行結果
        """
        workflow_path = self._workflows_dir / f"{trigger.workflow}.yaml"
        if not workflow_path.exists():
            raise FileNotFoundError(f"ワークフローが見つかりません: {workflow_path}")

        workflow = WorkflowLoader.load(workflow_path)

        if self._on_workflow_start:
            self._on_workflow_start(trigger.name, trigger.workflow)

        executor = GraphExecutor(workflow, self._skills, self._llm_client)
        result = executor.execute(trigger.inputs)

        if self._on_workflow_end:
            self._on_workflow_end(trigger.name, trigger.workflow, result)

        return result

    def start_cron(self) -> None:
        """
        cronトリガーをバックグラウンドスレッドで開始する。
        apschedulerが利用可能な場合はそれを使用し、なければ警告を出す。
        """
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger as APCronTrigger
        except ImportError:
            logger.warning(
                "apschedulerがインストールされていません。"
                "cronトリガーを使用するには: uv add apscheduler"
            )
            return

        triggers = self.load_triggers()
        cron_triggers = [t for t in triggers if t.trigger.get("type") == "cron"]

        if not cron_triggers:
            logger.info("cronトリガーが定義されていません。")
            return

        scheduler = BackgroundScheduler()
        for trigger in cron_triggers:
            schedule = trigger.trigger.get("schedule")
            if not schedule:
                continue
            # cron式をパース（分 時 日 月 曜日）
            parts = schedule.split()
            if len(parts) != 5:
                logger.error(f"無効なcron式: {schedule} (トリガー: {trigger.name})")
                continue

            minute, hour, day, month, day_of_week = parts
            scheduler.add_job(
                func=self.run_workflow,
                trigger=APCronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                ),
                args=[trigger],
                id=trigger.name,
                name=trigger.name,
                replace_existing=True,
            )
            logger.info(f"cronスケジュール登録: {trigger.name} ({schedule})")

        scheduler.start()
        self._running = True
        logger.info(f"{len(cron_triggers)}件のcronトリガーを開始しました。")
        return scheduler

    def run_once(self, trigger_name: str) -> Any:
        """
        指定名のトリガーを即時1回実行する（テスト・手動実行用）。

        Args:
            trigger_name: 実行するトリガー名

        Returns:
            ワークフロー実行結果
        """
        triggers = self.load_triggers()
        for trigger in triggers:
            if trigger.name == trigger_name:
                logger.info(f"手動実行: {trigger_name}")
                return self.run_workflow(trigger)
        raise ValueError(f"トリガーが見つかりません: {trigger_name}")
