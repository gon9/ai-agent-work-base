from typing import Any
from ..core.tool import BaseTool

class EchoTool(BaseTool):
    """
    入力をそのまま返すシンプルなツール
    """
    
    @property
    def name(self) -> str:
        return "echo_tool"

    @property
    def description(self) -> str:
        return "入力されたメッセージをそのまま返します。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo back."
                }
            },
            "required": ["message"]
        }

    def execute(self, message: str, **kwargs) -> str:
        """
        メッセージをそのまま返す
        
        Args:
            message (str): 入力メッセージ
            
        Returns:
            str: 入力メッセージ
        """
        return message

class ReverseTool(BaseTool):
    """
    入力文字列を反転させるツール
    """
    
    @property
    def name(self) -> str:
        return "reverse_tool"

    @property
    def description(self) -> str:
        return "入力された文字列を反転して返します。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to reverse."
                }
            },
            "required": ["text"]
        }

    def execute(self, text: str, **kwargs) -> str:
        """
        文字列を反転する
        
        Args:
            text (str): 反転させる文字列
            
        Returns:
            str: 反転された文字列
        """
        return text[::-1]
