import os
from typing import Any
from ..core.tool import BaseTool

class FileWriteTool(BaseTool):
    """
    ファイルにテキストを書き込むツール
    """
    
    @property
    def name(self) -> str:
        return "file_write_tool"

    @property
    def description(self) -> str:
        return "指定されたファイルにテキストを書き込みます。ファイルが存在する場合は上書きされます。"

    @property
    def parameters(self) -> dict:
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
            # セキュリティのため、特定のディレクトリ以下に限定するなどの対策が必要だが、
            # 今回はプロトタイプとして任意のパスを許可（ただし絶対パス推奨）
            # ディレクトリがない場合は作成
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"

class FileReadTool(BaseTool):
    """
    ファイルの内容を読み込むツール
    """
    
    @property
    def name(self) -> str:
        return "file_read_tool"

    @property
    def description(self) -> str:
        return "指定されたファイルの内容を読み込みます。"

    @property
    def parameters(self) -> dict:
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
