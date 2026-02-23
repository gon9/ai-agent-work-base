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
from ai_agent_work_base.engine.trigger_runner import TriggerRunner
from ai_agent_work_base.engine.slack_trigger import SlackTriggerApp
from ai_agent_work_base.skills import load_all_skills
from ai_agent_work_base.schemas.workflow import NodeDefinition, WorkflowDefinition

# Load environment variables
load_dotenv()

console = Console()
WORKFLOW_DIR = Path("workflows")
TRIGGER_DIR = Path("triggers")

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


def list_triggers() -> None:
    """登録済みトリガーの一覧をテーブル形式で表示する"""
    runner = TriggerRunner(
        triggers_dir=TRIGGER_DIR,
        workflows_dir=WORKFLOW_DIR,
        llm_client=None,
        skills=[],
    )
    triggers = runner.load_triggers()
    if not triggers:
        console.print("[yellow]triggers/ディレクトリにトリガーが定義されていません。[/yellow]")
        return

    table = Table(title="Registered Triggers")
    table.add_column("Name", style="cyan")
    table.add_column("Workflow", style="magenta")
    table.add_column("Trigger Type", style="green")
    table.add_column("Schedule/Config", style="yellow")
    table.add_column("Enabled", style="white")

    for t in triggers:
        ttype = t.trigger.get("type", "unknown")
        config = t.trigger.get("schedule") or t.trigger.get("keyword") or t.trigger.get("path") or "-"
        table.add_row(t.name, t.workflow, ttype, config, "✅" if t.enabled else "❌")

    console.print(table)


def run_trigger_once(trigger_name: str) -> None:
    """指定トリガーを即時1回実行する"""
    llm_client = LLMClient()
    skills = load_all_skills()

    runner = TriggerRunner(
        triggers_dir=TRIGGER_DIR,
        workflows_dir=WORKFLOW_DIR,
        llm_client=llm_client,
        skills=skills,
        on_workflow_start=lambda tn, wn: console.print(f"▶️  トリガー実行: [bold cyan]{tn}[/bold cyan] → ワークフロー: {wn}"),
        on_workflow_end=lambda tn, wn, r: console.print(f"✅ [bold green]{tn}[/bold green] 完了"),
    )
    try:
        runner.run_once(trigger_name)
    except (ValueError, FileNotFoundError) as e:
        console.print(f"[bold red]エラー:[/bold red] {e}")
        sys.exit(1)


def start_slack_trigger() -> None:
    """Slack BoltアプリをSocket Modeで起動する"""
    llm_client = LLMClient()
    skills = load_all_skills()

    app = SlackTriggerApp(
        workflows_dir=WORKFLOW_DIR,
        llm_client=llm_client,
        skills=skills,
    )
    console.print("[bold green]Slack Triggerアプリ起動中... Ctrl+C で停止[/bold green]")
    console.print("Slackで [cyan]/run <workflow>[/cyan] または [cyan]/workflows[/cyan] と入力してください。")
    try:
        app.start()
    except RuntimeError as e:
        console.print(f"[bold red]エラー:[/bold red] {e}")
        sys.exit(1)


def start_scheduler() -> None:
    """cronトリガーをバックグラウンドで起動し続ける"""
    import time
    llm_client = LLMClient()
    skills = load_all_skills()

    runner = TriggerRunner(
        triggers_dir=TRIGGER_DIR,
        workflows_dir=WORKFLOW_DIR,
        llm_client=llm_client,
        skills=skills,
        on_workflow_start=lambda tn, wn: console.print(f"▶️  [{tn}] {wn} 開始"),
        on_workflow_end=lambda tn, wn, r: console.print(f"✅ [{tn}] {wn} 完了"),
    )
    scheduler = runner.start_cron()
    if scheduler is None:
        return
    console.print("[bold green]スケジューラー起動中... Ctrl+C で停止[/bold green]")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        console.print("[yellow]スケジューラーを停止しました。[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="AI Agent Platform CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("skills", help="登録済みスキルの一覧を表示する")
    subparsers.add_parser("run", help="ワークフローを選択して実行する")

    trigger_parser = subparsers.add_parser("trigger", help="トリガー管理")
    trigger_sub = trigger_parser.add_subparsers(dest="trigger_command")
    trigger_sub.add_parser("list", help="登録済みトリガーの一覧を表示する")
    run_once_parser = trigger_sub.add_parser("run-once", help="指定トリガーを即時1回実行する")
    run_once_parser.add_argument("name", help="実行するトリガー名")
    trigger_sub.add_parser("start", help="cronスケジューラーを起動する")
    trigger_sub.add_parser("slack", help="Slack BoltアプリをSocket Modeで起動する")

    args = parser.parse_args()

    console.clear()
    console.print(Panel.fit("🤖 AI Agent Platform CLI", style="bold blue"))

    if args.command == "skills":
        list_skills()
    elif args.command == "trigger":
        if args.trigger_command == "list":
            list_triggers()
        elif args.trigger_command == "run-once":
            run_trigger_once(args.name)
        elif args.trigger_command == "start":
            start_scheduler()
        elif args.trigger_command == "slack":
            start_slack_trigger()
        else:
            trigger_parser.print_help()
    elif args.command == "run" or args.command is None:
        run_workflow()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
