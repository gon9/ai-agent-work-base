import json
from typing import List, Dict, Any, Optional
from .llm import LLMClient
from .tool import BaseTool

class Agent:
    """
    LLMとツールを使用してタスクを実行するエージェント
    """
    def __init__(self, llm_client: LLMClient, tools: List[BaseTool], system_prompt: str = "You are a helpful AI assistant."):
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """ツール定義をOpenAI形式に変換して返す"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools.values()
        ]

    def run(self, user_input: str) -> str:
        """
        ユーザー入力を受け取り、タスクを実行して回答を返す
        Function Callingのループ処理を行う
        
        Args:
            user_input (str): ユーザーからの入力
            
        Returns:
            str: 最終的な回答
        """
        self.messages.append({"role": "user", "content": user_input})
        tool_definitions = self._get_tool_definitions()

        while True:
            # LLM呼び出し
            response = self.llm.chat_completion(
                messages=self.messages,
                tools=tool_definitions if tool_definitions else None
            )
            
            message = response.choices[0].message
            self.messages.append(message) # 履歴に追加

            # ツール呼び出し要求があるかチェック
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments_str = tool_call.function.arguments
                    
                    try:
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        result = "Error: Invalid JSON arguments."
                    else:
                        if function_name in self.tools:
                            tool = self.tools[function_name]
                            try:
                                # ツール実行
                                result = tool.execute(**arguments)
                            except Exception as e:
                                result = f"Error executing tool {function_name}: {str(e)}"
                        else:
                            result = f"Error: Tool {function_name} not found."

                    # ツール実行結果をメッセージ履歴に追加
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
            else:
                # ツール呼び出しがなければ、それが最終回答
                return message.content
