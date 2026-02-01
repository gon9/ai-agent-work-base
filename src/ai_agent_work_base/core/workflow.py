from abc import ABC, abstractmethod
from typing import Any, List, Dict
from .tool import BaseTool

class BaseWorkflow(ABC):
    """
    ワークフローの基底クラス
    """
    
    def __init__(self, tools: List[BaseTool] = None):
        """
        Args:
            tools (List[BaseTool], optional): ワークフローで使用するツールのリスト
        """
        self.tools: Dict[str, BaseTool] = {t.name: t for t in tools} if tools else {}

    def register_tool(self, tool: BaseTool) -> None:
        """
        ツールを登録する
        
        Args:
            tool (BaseTool): 登録するツール
        """
        self.tools[tool.name] = tool

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """
        ワークフローを実行する
        
        Args:
            input_data (Any): 入力データ
            
        Returns:
            Any: 実行結果
        """
        pass
