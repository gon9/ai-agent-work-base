from typing import Any, Dict
from .base import BaseSkill

class EchoSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "入力されたメッセージをそのまま返します。"

    @property
    def parameters(self) -> Dict[str, Any]:
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
        return message

class ReverseSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "reverse"

    @property
    def description(self) -> str:
        return "入力された文字列を反転して返します。"

    @property
    def parameters(self) -> Dict[str, Any]:
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
        return text[::-1]
