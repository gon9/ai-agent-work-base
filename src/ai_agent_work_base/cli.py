import argparse
import os
import sys
from pathlib import Path
from typing import Any, List, Dict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from dotenv import load_dotenv

from ai_agent_work_base.core.llm import LLMClient
from ai_agent_work_base.engine.loader import WorkflowLoader
from ai_agent_work_base.engine.executor import GraphExecutor
from ai_agent_work_base.skills import load_all_skills
from ai_agent_work_base.schemas.workflow import NodeDefinition, WorkflowDefinition

# Load environment variables
load_dotenv()

console = Console()
WORKFLOW_DIR = Path("workflows")

def get_available_workflows() -> List[Dict[str, Any]]:
    """workflowsディレクトリ内のYAMLファイルを取得"""
    files = list(WORKFLOW_DIR.glob("*.yaml")) + list(WORKFLOW_DIR.glob("*.yml"))
    workflows = []
    for f in files:
        try:
            wf = WorkflowLoader.load(f)
            workflows.append({"name": wf.name, "path": f, "obj": wf})
        except Exception as e:
            console.print(f"[red]Error loading {f}: {e}[/red]")
    return workflows

def select_workflow(workflows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """ワークフローを選択する"""
    table = Table(title="Available Workflows")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="green")

    for i, w in enumerate(workflows):
        wf_obj: WorkflowDefinition = w["obj"]
        table.add_row(str(i + 1), wf_obj.name, wf_obj.description or "")

    console.print(table)
    
    while True:
        choice = Prompt.ask("Select workflow ID", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(workflows):
                return workflows[idx]
        except ValueError:
            pass
        console.print("[red]Invalid selection.[/red]")

def collect_inputs(workflow: WorkflowDefinition) -> Dict[str, Any]:
    """ワークフローの入力を収集する"""
    inputs = {}
    if not workflow.inputs:
        return inputs
        
    console.print("\n[bold]Please provide inputs:[/bold]")
    for inp in workflow.inputs:
        desc = f" ({inp.description})" if inp.description else ""
        val = Prompt.ask(f"[yellow]{inp.name}[/yellow]{desc}")
        inputs[inp.name] = val
    return inputs

def list_skills() -> None:
    """登録済みスキルの一覧をテーブル形式で表示する"""
    skills = load_all_skills()

    table = Table(title="Available Skills", show_lines=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_column("Required Parameters", style="yellow")

    for skill in skills:
        params = skill.parameters.get("properties", {})
        required = skill.parameters.get("required", [])
        param_parts = []
        for param_name, param_def in params.items():
            req_mark = "*" if param_name in required else ""
            param_type = param_def.get("type", "any")
            param_parts.append(f"{param_name}{req_mark} ({param_type})")
        params_str = "\n".join(param_parts) if param_parts else "-"

        table.add_row(skill.name, skill.description, params_str)

    console.print(table)
    console.print("[dim]* = required[/dim]")


def run_workflow() -> None:
    """ワークフローを選択して実行する"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable is not set.")
        console.print("Please set it in .env file or environment variables.")
        sys.exit(1)

    workflows = get_available_workflows()
    if not workflows:
        console.print("[yellow]No workflow files found in workflows/ directory.[/yellow]")
        return

    selected = select_workflow(workflows)
    workflow: WorkflowDefinition = selected["obj"]

    console.print(f"\nSelected: [bold green]{workflow.name}[/bold green]")
    inputs = collect_inputs(workflow)

    try:
        llm_client = LLMClient()
        skills = load_all_skills()

        def on_node_start(node: NodeDefinition):
            console.print(f"▶️  Step: [bold cyan]{node.id}[/bold cyan] ({node.type}) executing...")

        def on_node_end(node: NodeDefinition, output: Any):
            out_str = str(output)
            if len(out_str) > 200:
                out_str = out_str[:200] + "..."
            console.print(f"✅ Step: [bold cyan]{node.id}[/bold cyan] Finished. Result: {out_str}")

        executor = GraphExecutor(
            workflow,
            skills,
            llm_client,
            on_node_start=on_node_start,
            on_node_end=on_node_end
        )

        console.print("\n[bold]Executing Workflow...[/bold]")
        with console.status("[bold green]Running...[/bold green]", spinner="dots"):
            results = executor.execute(inputs)

        console.print("\n[bold green]🎉 Workflow Completed![/bold green]")

        if Prompt.ask("Show full results?", choices=["y", "n"], default="n") == "y":
            console.print(results)

    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AI Agent Platform CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("skills", help="登録済みスキルの一覧を表示する")
    subparsers.add_parser("run", help="ワークフローを選択して実行する")

    args = parser.parse_args()

    console.clear()
    console.print(Panel.fit("🤖 AI Agent Platform CLI", style="bold blue"))

    if args.command == "skills":
        list_skills()
    elif args.command == "run" or args.command is None:
        run_workflow()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
