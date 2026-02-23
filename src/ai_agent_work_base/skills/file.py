import os
from typing import Any, Dict
from .base import BaseSkill

class FileWriteSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "指定されたファイルにテキストを書き込みます。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to write to."
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file."
                }
            },
            "required": ["file_path", "content"]
        }

    def execute(self, file_path: str, content: str, **kwargs) -> str:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"

class FileReadSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "指定されたファイルの内容を読み込みます。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read."
                }
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str, **kwargs) -> str:
        try:
            if not os.path.exists(file_path):
                return f"Error: File {file_path} does not exist."
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
