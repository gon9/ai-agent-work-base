from typing import Dict, Any, List
from ..core.tool import BaseTool
from .models import WorkflowPlan, TaskStep

class PlanExecutor:
    """
    WorkflowPlanを実行するクラス
    """
    def __init__(self, tools: List[BaseTool]):
        self.tools = {t.name: t for t in tools}
        self.results: Dict[int, Any] = {}

    def _resolve_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        引数内のプレースホルダー ({step_N_result}) を実際の値に置換する
        """
        resolved_args = {}
        for k, v in arguments.items():
            if isinstance(v, str):
                # シンプルな置換ロジック
                # "{step_1_result}" のような文字列を探して置換
                for step_id, result in self.results.items():
                    placeholder = f"{{step_{step_id}_result}}"
                    if placeholder in v:
                        # 文字列全体がプレースホルダーなら型を維持して置換
                        if v == placeholder:
                            v = result
                        else:
                            # 部分一致なら文字列として置換
                            v = v.replace(placeholder, str(result))
            resolved_args[k] = v
        return resolved_args

    def execute(self, plan: WorkflowPlan) -> Dict[int, Any]:
        """
        計画を実行する
        """
        print(f"Executing Plan: {plan.goal}")
        self.results = {}
        
        # 簡易的な順次実行 (ステップID順)
        # 依存関係トポロジカルソートは今回は省略し、ID順で問題ないと仮定
        sorted_steps = sorted(plan.steps, key=lambda s: s.step_id)
        
        for step in sorted_steps:
            print(f"  Step {step.step_id}: {step.description} (Tool: {step.tool_name})")
            
            if step.tool_name not in self.tools:
                error_msg = f"Tool {step.tool_name} not found."
                print(f"    Error: {error_msg}")
                self.results[step.step_id] = error_msg
                continue
                
            tool = self.tools[step.tool_name]
            
            try:
                # 引数の解決
                args = self._resolve_arguments(step.arguments)
                
                # ツール実行
                result = tool.execute(**args)
                self.results[step.step_id] = result
                print(f"    Result: {str(result)[:100]}...") # ログは短く
                
            except Exception as e:
                error_msg = f"Execution failed: {str(e)}"
                print(f"    Error: {error_msg}")
                self.results[step.step_id] = error_msg
                
        return self.results
