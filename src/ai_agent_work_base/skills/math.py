from typing import Any, Dict
from .base import BaseSkill

class CalculatorSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "数式の計算を行います。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate."
                }
            },
            "required": ["expression"]
        }

    def execute(self, expression: str, **kwargs) -> str:
        try:
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                 return "Error: Invalid characters."
            result = eval(expression, {"__builtins__": {}})
            return str(result)
        except Exception as e:
            return f"Error calculating expression: {str(e)}"
