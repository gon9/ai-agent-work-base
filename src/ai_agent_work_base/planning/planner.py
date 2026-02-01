import json
from typing import List
from ..core.llm import LLMClient
from ..core.tool import BaseTool
from .models import WorkflowPlan

class Planner:
    """
    ゴールに基づいてワークフロー計画を立案するクラス
    """
    def __init__(self, llm_client: LLMClient, tools: List[BaseTool]):
        self.llm = llm_client
        self.tools = {t.name: t for t in tools}

    def _create_system_prompt(self) -> str:
        tool_descriptions = "\n".join([
            f"- {name}: {tool.description} (Params: {json.dumps(tool.parameters, ensure_ascii=False)})"
            for name, tool in self.tools.items()
        ])
        
        return f"""
あなたは優秀なワークフロープランナーです。あなたの目標は、ユーザーの要求を利用可能なツールを使って実行可能なステップに分解することです。

利用可能なツール:
{tool_descriptions}

出力フォーマット:
以下の構造を持つ有効なJSONオブジェクトのみを出力してください (WorkflowPlan):
{{
  "goal": "目標の要約（日本語）",
  "steps": [
    {{
      "step_id": 1,
      "description": "ステップ1の説明（日本語）",
      "tool_name": "使用するツール名",
      "arguments": {{ "arg_name": "value" }},
      "dependencies": []
    }},
    ...
  ]
}}

ルール:
1. 上記のリストにあるツールのみを使用してください。
2. ステップが前のステップの結果に依存する場合、引数の中で "{{step_N_result}}" のようなプレースホルダー文字列を使用できます（Nはstep_id）。
3. ステップは論理的な順序で並べてください。
4. Markdownのフォーマットや解説は含めず、純粋なJSONオブジェクトのみを返してください。
"""

    def create_plan(self, user_request: str) -> WorkflowPlan:
        """
        ユーザーのリクエストから実行計画を作成する
        """
        messages = [
            {"role": "system", "content": self._create_system_prompt()},
            {"role": "user", "content": user_request}
        ]
        
        # JSONモードを強制したいが、モデルによってはサポート状況が異なる。
        # ここではプロンプトで指示し、レスポンスをパースする。
        # gpt-4o 等であれば response_format={"type": "json_object"} が使える。
        
        params = {
            "messages": messages,
        }
        
        # response_format パラメータのサポート確認 (OpenAIクライアントの仕様依存)
        # 今回は一旦テキストで受け取ってパースする安全策をとるか、あるいはパラメータを追加してみる。
        # LLMClientの実装を見ると **params を渡しているので追加可能。
        
        try:
            params["response_format"] = {"type": "json_object"}
        except:
            pass # サポートされていない場合は無視されるかエラーになる可能性があるが、OpenAIなら基本OK
            
        response = self.llm.chat_completion(**params)
        content = response.choices[0].message.content
        
        try:
            plan_dict = json.loads(content)
            return WorkflowPlan(**plan_dict)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse plan JSON: {content}")
        except Exception as e:
            raise ValueError(f"Invalid plan structure: {e}")
