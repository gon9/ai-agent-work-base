from typing import Any, List
from ..core.workflow import BaseWorkflow

class SequentialWorkflow(BaseWorkflow):
    """
    登録されたツールを順番に実行するシンプルなワークフロー
    前のツールの出力を次のツールの入力とする
    """
    
    def __init__(self, tools=None):
        super().__init__(tools)
        # 実行順序を保持するためのリスト（辞書だと順序保証がPythonバージョン依存かつ意図が不明確になるため明示的に管理）
        self.execution_order: List[str] = [t.name for t in tools] if tools else []

    def add_step(self, tool_name: str):
        """
        実行ステップを追加する
        
        Args:
            tool_name (str): 追加するツールの名前（登録済みであること）
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' is not registered.")
        self.execution_order.append(tool_name)

    def run(self, initial_input: Any) -> Any:
        """
        ワークフローを実行する
        
        Args:
            initial_input (Any): 最初の入力
            
        Returns:
            Any: 最終的な実行結果
        """
        current_data = initial_input
        
        for tool_name in self.execution_order:
            tool = self.tools[tool_name]
            # シンプルにするため、前の出力を最初の引数として渡す想定
            # 実際には引数名などをマッピングする仕組みが必要になる場合がある
            if isinstance(current_data, dict):
                 current_data = tool.execute(**current_data)
            else:
                # 辞書でない場合は、executeのシグネチャに合わせて可変長引数か、
                # あるいは単一引数として渡す実装が必要。
                # ここでは簡易的に、各ツールが第一引数でデータを受け取れると仮定するか、
                # キーワード引数 'text' や 'message' にマッピングするロジックを入れる。
                # BasicToolの実装に合わせて調整。
                # 今回はツール側が execute(arg, **kwargs) の形にはなっていないので
                # ツール個別の引数名に合わせる必要があるが、
                # 汎用性を高めるため、ここでは簡易的なマッピングを行う。
                
                if tool.name == "echo_tool":
                    current_data = tool.execute(message=current_data)
                elif tool.name == "reverse_tool":
                    current_data = tool.execute(text=current_data)
                else:
                    # その他のツール用（仮）
                    current_data = tool.execute(current_data)
                    
        return current_data
