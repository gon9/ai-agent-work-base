import os
from typing import Any, List, Optional, Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMClient:
    """
    OpenAI APIクライアントのラッパークラス
    """
    def __init__(self, model: Optional[str] = None):
        """
        Args:
            model (str, optional): 使用するモデル名。指定がない場合は環境変数 OPENAI_MODEL または "gpt-4o" を使用
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            # 警告を出すか、エラーにするか。ここでは実際にコールするまでエラーにしないでおくが、
            # ログを出しておくのが親切。
            print("Warning: OPENAI_API_KEY is not set.")
            
        self.client = OpenAI(api_key=self.api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None
    ) -> Any:
        """
        Chat Completion APIを呼び出す
        
        Args:
            messages (List[Dict[str, str]]): メッセージ履歴
            tools (List[Dict[str, Any]], optional): Function Calling用のツール定義
            tool_choice (Any, optional): ツールの選択設定
            
        Returns:
            Any: APIレスポンス (ChatCompletion)
        """
        params = {
            "model": self.model,
            "messages": messages,
        }
        
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
            
        return self.client.chat.completions.create(**params)
