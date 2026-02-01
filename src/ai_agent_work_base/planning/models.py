from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TaskStep(BaseModel):
    step_id: int = Field(..., description="ステップのID (1から始まる連番)")
    description: str = Field(..., description="このステップで実行する内容の説明")
    tool_name: str = Field(..., description="使用するツールの名前")
    arguments: Dict[str, Any] = Field(..., description="ツールに渡す引数")
    dependencies: List[int] = Field(default_factory=list, description="このステップが依存するステップIDのリスト")

class WorkflowPlan(BaseModel):
    goal: str = Field(..., description="達成すべきゴール")
    steps: List[TaskStep] = Field(..., description="実行するステップのリスト")
