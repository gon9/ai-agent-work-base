from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    """
    全てのツールの基底クラス
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """ツールの名前を返す"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """ツールの説明を返す"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        OpenAI Function Calling形式のパラメータ定義を返す
        
        Returns:
            dict: JSON Schema parameters
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        ツールを実行する
        
        Args:
            **kwargs: ツール実行に必要な引数
            
        Returns:
            Any: 実行結果
        """
        pass
