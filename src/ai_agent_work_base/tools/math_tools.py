from typing import Any
from ..core.tool import BaseTool

class CalculatorTool(BaseTool):
    """
    基本的な数学計算を行うツール
    """
    
    @property
    def name(self) -> str:
        return "calculator_tool"

    @property
    def description(self) -> str:
        return "数式の計算を行います。Pythonのevalを使用するため、単純な数式に限ります。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')."
                }
            },
            "required": ["expression"]
        }

    def execute(self, expression: str, **kwargs) -> str:
        try:
            # 安全のため、許可される文字を制限する簡易的なバリデーション
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                 return "Error: Invalid characters in expression. Only numbers and basic operators are allowed."
            
            # evalの使用はセキュリティリスクがあるが、ここではプロトタイプとして使用
            # 実際にはnumexprなどを使用すべき
            result = eval(expression, {"__builtins__": {}})
            return str(result)
        except Exception as e:
            return f"Error calculating expression: {str(e)}"
