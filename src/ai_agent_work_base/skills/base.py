from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSkill(ABC):
    """
    全てのスキルの基底クラス
    BaseToolと同様だが、概念に合わせて名称変更
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """スキルの名前 (ワークフロー定義で使用)"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """スキルの説明"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """パラメータ定義 (JSON Schema)"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """スキルの実行"""
        pass
