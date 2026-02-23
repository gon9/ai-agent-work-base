"""
ワークフロー可視化ツール

YAMLワークフローをMermaid図に変換して表示・出力します。

使い方:
    uv run python -m ai_agent_work_base.tools.visualize workflows/deep_research.yaml
    uv run python -m ai_agent_work_base.tools.visualize workflows/  # ディレクトリ指定で一覧
"""
import sys
from pathlib import Path
from typing import Optional

from ..engine.loader import WorkflowLoader
from ..schemas.workflow import NodeDefinition, WorkflowDefinition

# ノードタイプ別のMermaidスタイル
_NODE_STYLES = {
    "llm":       ("([{label}])", "fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f"),
    "skill":     ("[{label}]",   "fill:#dcfce7,stroke:#22c55e,color:#14532d"),
    "foreach":   ("[/{label}/]", "fill:#fef9c3,stroke:#eab308,color:#713f12"),
    "condition": ("{{{label}}}", "fill:#fce7f3,stroke:#ec4899,color:#831843"),
    "end":       ("([{label}])", "fill:#f1f5f9,stroke:#94a3b8,color:#334155"),
}

_TYPE_LABELS = {
    "llm":       "LLM",
    "skill":     "Skill",
    "foreach":   "foreach",
    "condition": "condition",
    "end":       "End",
}


def _node_shape(node: NodeDefinition) -> str:
    """ノードのMermaid形状文字列を返す。"""
    ntype = node.type
    type_label = _TYPE_LABELS.get(ntype, ntype)

    if ntype == "llm":
        model_hint = f" {node.model}" if node.model else ""
        label = f"{node.id} [{type_label}{model_hint}]"
        return f'{node.id}(["{label}"])'
    elif ntype == "skill":
        label = f"{node.id} [Skill: {node.skill or '?'}]"
        return f'{node.id}["{label}"]'
    elif ntype == "foreach":
        label = f"{node.id} [foreach]"
        return f'{node.id}[/"{label}"/]'
    elif ntype == "condition":
        label = f"{node.id} [condition]"
        return f'{node.id}{{"{label}"}}'
    else:
        label = f"{node.id} [{type_label}]"
        return f'{node.id}["{label}"]'


def workflow_to_mermaid(workflow: WorkflowDefinition) -> str:
    """WorkflowDefinitionをMermaid flowchart文字列に変換する。"""
    lines = ["flowchart TD"]

    # inputs ノード
    if workflow.inputs:
        input_labels = ", ".join(f"{i.name}:{i.type}" for i in workflow.inputs)
        lines.append(f'    START(["Inputs\\n{input_labels}"])')
        if workflow.nodes:
            lines.append(f'    START --> {workflow.nodes[0].id}')

    node_map = {n.id: n for n in workflow.nodes}

    for node in workflow.nodes:
        shape = _node_shape(node)
        lines.append(f"    {shape}")

        # foreach の子ノードを表示
        if node.type == "foreach" and node.node:
            child_id = f"{node.id}__child"
            child_type = node.node.type
            if child_type == "skill":
                child_label = f"skill:{node.node.skill or '?'}"
                lines.append(f'    {child_id}["{child_label}"]')
            else:
                model_hint = f" {node.node.model}" if node.node.model else ""
                child_label = f"LLM{model_hint}"
                lines.append(f'    {child_id}(["{child_label}"])')
            lines.append(f"    {node.id} -->|each item| {child_id}")
            lines.append(f"    {child_id} -.->|results| {node.id}")

        # next エッジ
        if node.next:
            if node.next == "end":
                lines.append(f'    END(["End"])')
                lines.append(f"    {node.id} --> END")
            elif node.next in node_map:
                lines.append(f"    {node.id} --> {node.next}")

    # スタイル定義
    lines.append("")
    lines.append("    %% Styles")
    lines.append('    style START fill:#f0fdf4,stroke:#86efac,color:#166534')
    lines.append('    style END fill:#f1f5f9,stroke:#94a3b8,color:#334155')

    for node in workflow.nodes:
        _, style = _NODE_STYLES.get(node.type, ("", ""))
        if style:
            lines.append(f"    style {node.id} {style}")
        if node.type == "foreach" and node.node:
            child_id = f"{node.id}__child"
            child_type = node.node.type
            _, child_style = _NODE_STYLES.get(child_type, ("", ""))
            if child_style:
                lines.append(f"    style {child_id} {child_style}")

    return "\n".join(lines)


def print_workflow_info(workflow: WorkflowDefinition, mermaid: str) -> None:
    """ワークフロー情報とMermaid図をターミナルに表示する。"""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.syntax import Syntax

        console = Console()
        console.print(Panel(
            f"[bold]{workflow.name}[/bold]\n{workflow.description or ''}",
            title="📋 Workflow",
            border_style="blue"
        ))

        if workflow.inputs:
            table = Table(title="Inputs", show_header=True)
            table.add_column("name", style="cyan")
            table.add_column("type", style="green")
            table.add_column("description")
            for inp in workflow.inputs:
                table.add_row(inp.name, inp.type, inp.description or "")
            console.print(table)

        node_table = Table(title="Nodes", show_header=True)
        node_table.add_column("id", style="cyan")
        node_table.add_column("type", style="magenta")
        node_table.add_column("detail")
        node_table.add_column("next", style="dim")
        for node in workflow.nodes:
            if node.type == "llm":
                detail = f"model={node.model or 'default'}, format={node.output_format}"
            elif node.type == "skill":
                detail = f"skill={node.skill}"
            elif node.type == "foreach":
                child = node.node
                detail = f"items={node.items}, child={child.type if child else '?'}"
            else:
                detail = ""
            node_table.add_row(node.id, node.type, detail, node.next or "-")
        console.print(node_table)

        console.print(Panel(
            Syntax(mermaid, "text", theme="monokai"),
            title="🧜 Mermaid図（https://mermaid.live に貼り付けて確認）",
            border_style="yellow"
        ))
    except ImportError:
        print(f"\n=== {workflow.name} ===")
        print(mermaid)


def visualize_file(path: Path) -> None:
    """単一のYAMLファイルを可視化する。"""
    workflow = WorkflowLoader.load(path)
    mermaid = workflow_to_mermaid(workflow)
    print_workflow_info(workflow, mermaid)


def visualize_directory(directory: Path) -> None:
    """ディレクトリ内の全YAMLを一覧表示する。"""
    yamls = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))
    if not yamls:
        print(f"YAMLファイルが見つかりません: {directory}")
        return
    for path in yamls:
        try:
            visualize_file(path)
            print()
        except Exception as e:
            print(f"[ERROR] {path.name}: {e}")


def main() -> None:
    """CLIエントリーポイント。"""
    if len(sys.argv) < 2:
        print("使い方: uv run python -m ai_agent_work_base.tools.visualize <workflow.yaml|workflows/>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if target.is_dir():
        visualize_directory(target)
    elif target.is_file():
        visualize_file(target)
    else:
        print(f"ファイルまたはディレクトリが見つかりません: {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()
