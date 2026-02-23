from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field

class InputDefinition(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class InlineNodeDefinition(BaseModel):
    """foreachノード内で使用するインラインノード定義（idなし）"""
    type: Literal["llm", "skill"]
    prompt: Optional[str] = None
    model: Optional[str] = None
    skill: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class NodeDefinition(BaseModel):
    id: str
    type: Literal["llm", "skill", "condition", "foreach", "end"]
    name: Optional[str] = None
    next: Optional[str] = None
    
    # LLM Node specific
    prompt: Optional[str] = None
    model: Optional[str] = None
    output_format: Optional[Literal["text", "json"]] = "text"
    
    # Skill Node specific
    skill: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    
    # Condition Node specific
    branches: Optional[Dict[str, str]] = None # value -> next_node_id

    # foreach Node specific
    items: Optional[str] = None              # リストを参照するテンプレート変数 e.g. "{{plan.output.queries}}"
    node: Optional[InlineNodeDefinition] = None  # 各要素に対して実行するノード定義

class WorkflowDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    inputs: List[InputDefinition] = Field(default_factory=list)
    nodes: List[NodeDefinition]
