from typing import List, Dict, Any
from ..core.llm import LLMClient
from ..core.tool import BaseTool
from .planner import Planner
from .executor import PlanExecutor

class PlanningAgent:
    """
    計画立案と実行を行うエージェント
    """
    def __init__(self, llm_client: LLMClient, tools: List[BaseTool]):
        self.llm = llm_client
        self.planner = Planner(llm_client, tools)
        self.executor = PlanExecutor(tools)

    def run(self, user_input: str) -> str:
        """
        ユーザー入力を受け取り、計画立案・実行・結果要約を行う
        """
        # 1. 計画立案
        try:
            plan = self.planner.create_plan(user_input)
        except Exception as e:
            return f"計画の作成に失敗しました: {str(e)}"

        # 計画の内容を文字列化して（デバッグ/確認用にもなるが）保持
        plan_summary = f"目標: {plan.goal}\n"
        for step in plan.steps:
            plan_summary += f"- Step {step.step_id}: {step.description} (Tool: {step.tool_name})\n"

        # 2. 計画実行
        try:
            results = self.executor.execute(plan)
        except Exception as e:
            return f"計画の実行中にエラーが発生しました:\n{plan_summary}\nError: {str(e)}"

        # 3. 結果の集約と回答生成
        # 実行結果をコンテキストとしてLLMに渡し、最終回答を生成させる
        return self._generate_final_response(user_input, plan_summary, results)

    def _generate_final_response(self, user_input: str, plan_summary: str, results: Dict[int, Any]) -> str:
        
        results_str = "\n".join([f"Step {sid}: {res}" for sid, res in results.items()])
        
        system_prompt = """
あなたはAIアシスタントです。
ユーザーの依頼に対して実行された計画と、その実行結果が提供されます。
これらを元に、ユーザーに対する最終的な回答を日本語で生成してください。
"""
        user_message = f"""
## ユーザーの依頼
{user_input}

## 実行された計画
{plan_summary}

## 実行結果
{results_str}

## 回答
"""
        response = self.llm.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        return response.choices[0].message.content
