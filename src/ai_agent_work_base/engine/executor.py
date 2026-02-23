import json
import logging
from typing import Dict, Any, List, Optional, Callable
from ..schemas.workflow import WorkflowDefinition, NodeDefinition, InlineNodeDefinition
from .context import WorkflowContext
from ..skills.base import BaseSkill
from ..core.llm import LLMClient

logger = logging.getLogger(__name__)

class GraphExecutor:
    """
    ワークフローグラフを実行するエンジン
    """
    def __init__(
        self, 
        workflow: WorkflowDefinition, 
        skills: List[BaseSkill], 
        llm_client: LLMClient,
        on_node_start: Optional[Callable[[NodeDefinition], None]] = None,
        on_node_end: Optional[Callable[[NodeDefinition, Any], None]] = None,
        on_foreach_item_start: Optional[Callable[[NodeDefinition, int, int, Any], None]] = None,
        on_foreach_item_end: Optional[Callable[[NodeDefinition, int, int, Any, Any], None]] = None
    ):
        self.workflow = workflow
        self.skills = {s.name: s for s in skills}
        self.llm = llm_client
        self.node_map = {n.id: n for n in workflow.nodes}
        self.on_node_start = on_node_start
        self.on_node_end = on_node_end
        self.on_foreach_item_start = on_foreach_item_start
        self.on_foreach_item_end = on_foreach_item_end

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        ワークフローを実行する
        """
        context = WorkflowContext(inputs)
        
        # 開始ノードを見つける (現在はリストの最初のノードを開始とする)
        # 将来的には start_node 指定などに対応
        if not self.workflow.nodes:
            return {}
            
        current_node_id = self.workflow.nodes[0].id
        
        while current_node_id:
            if current_node_id == "end":
                break

            logger.info(f"Executing node: {current_node_id}")
            node = self.node_map.get(current_node_id)
            if not node:
                raise ValueError(f"Node {current_node_id} not found")
            
            # コールバック: 開始
            if self.on_node_start:
                self.on_node_start(node)

            # ノード実行
            output = self._execute_node(node, context)
            
            # コールバック: 終了
            if self.on_node_end:
                self.on_node_end(node, output)

            # 結果をコンテキストに保存
            context.set_step_output(node.id, output)
            
            # 次のノード決定
            if node.type == "end":
                break
                
            if node.type == "condition":
                # sourceパラメータで指定したノードの出力をブランチキーとして使用
                source_key = (node.params or {}).get("source")
                if source_key:
                    branch_value = str(context.get(f"{source_key}.output") or "").strip()
                else:
                    branch_value = str(output or "").strip()
                next_id = node.branches.get(branch_value)
                if next_id is None:
                    logger.warning(f"condition node '{node.id}': branch '{branch_value}' not found in {list(node.branches.keys())}")
                current_node_id = next_id
            else:
                # 通常遷移
                current_node_id = node.next
                
        # 最終的なコンテキストの状態を返す（あるいは特定の出力を返す）
        return context._data

    def _execute_node(self, node: NodeDefinition, context: WorkflowContext) -> Any:
        if node.type == "llm":
            return self._execute_llm_node(node, context)
        elif node.type == "skill":
            return self._execute_skill_node(node, context)
        elif node.type == "foreach":
            return self._execute_foreach_node(node, context)
        elif node.type == "end":
            return None
        elif node.type == "condition":
            # branches評価はexecute()側で行うためここでは何もしない
            return None
        else:
            raise ValueError(f"Unknown node type: {node.type}")

    def _execute_llm_node(self, node: NodeDefinition, context: WorkflowContext) -> Any:
        # プロンプト内の変数を解決
        prompt = context.resolve_template(node.prompt)
        
        # LLM実行（ノードでmodelが指定されていればそれを使用）
        kwargs = {"messages": [{"role": "user", "content": prompt}], "model": node.model}
        if node.output_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.llm.chat_completion(**kwargs)
        content = response.choices[0].message.content
        
        # JSON出力の場合はパースして返す
        if node.output_format == "json":
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"LLMのJSON出力のパースに失敗しました (node: {node.id}): {e}\n出力: {content}")
        
        return content

    def _execute_foreach_node(self, node: NodeDefinition, context: WorkflowContext) -> List[Any]:
        # itemsテンプレートを解決してリストを取得
        items = context.resolve_value(node.items)
        if not isinstance(items, list):
            raise ValueError(f"foreachノード '{node.id}' のitemsがリストではありません: {type(items).__name__}")
        
        if node.node is None:
            raise ValueError(f"foreachノード '{node.id}' にnodeが定義されていません")
        
        total = len(items)
        results = []
        for idx, item in enumerate(items):
            # コールバック: item開始
            if self.on_foreach_item_start:
                self.on_foreach_item_start(node, idx, total, item)

            # {{item}} を解決するための一時コンテキストを作成
            item_context = WorkflowContext()
            item_context._data = dict(context._data)  # 現在のコンテキストをコピー
            item_context._data["item"] = item
            
            result = self._execute_inline_node(node.node, item_context)
            results.append(result)

            # コールバック: item終了
            if self.on_foreach_item_end:
                self.on_foreach_item_end(node, idx, total, item, result)
        
        return results

    def _execute_inline_node(self, inline: InlineNodeDefinition, context: WorkflowContext) -> Any:
        """foreachの子ノードを実行する"""
        if inline.type == "skill":
            skill_name = inline.skill
            if skill_name not in self.skills:
                raise ValueError(f"Skill {skill_name} not found")
            skill = self.skills[skill_name]
            resolved_params = context.resolve_value(inline.params or {})
            return skill.execute(**resolved_params)
        elif inline.type == "llm":
            prompt = context.resolve_template(inline.prompt)
            response = self.llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=inline.model
            )
            return response.choices[0].message.content
        else:
            raise ValueError(f"インラインノードの未対応タイプ: {inline.type}")

    def _execute_skill_node(self, node: NodeDefinition, context: WorkflowContext) -> Any:
        skill_name = node.skill
        if skill_name not in self.skills:
            raise ValueError(f"Skill {skill_name} not found")
            
        skill = self.skills[skill_name]
        
        # パラメータの変数解決
        resolved_params = context.resolve_value(node.params or {})
        
        # スキル実行
        return skill.execute(**resolved_params)
