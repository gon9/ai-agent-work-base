import os
import sys
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from dotenv import load_dotenv

from ai_agent_work_base.core.llm import LLMClient
from ai_agent_work_base.core.agent import Agent
from ai_agent_work_base.planning.agent import PlanningAgent
from ai_agent_work_base.core.tool import BaseTool
from ai_agent_work_base.tools.basic_tools import EchoTool, ReverseTool
from ai_agent_work_base.tools.file_tools import FileWriteTool, FileReadTool
from ai_agent_work_base.tools.math_tools import CalculatorTool

# Load environment variables
load_dotenv()

console = Console()

def get_tools() -> List[BaseTool]:
    """使用するツールを初期化して返す"""
    return [
        EchoTool(),
        ReverseTool(),
        FileWriteTool(),
        FileReadTool(),
        CalculatorTool(),
    ]

def main():
    console.clear()
    console.print(Panel.fit("🤖 AI Agent Platform CLI (Planning Mode)", style="bold blue"))
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable is not set.")
        console.print("Please set it in .env file or environment variables.")
        sys.exit(1)

    # Initialize components
    try:
        llm_client = LLMClient()
        tools = get_tools()
        # PlanningAgentを使用
        agent = PlanningAgent(
            llm_client=llm_client, 
            tools=tools
        )
    except Exception as e:
        console.print(f"[bold red]Initialization Error:[/bold red] {str(e)}")
        sys.exit(1)

    console.print("[green]System initialized. Type 'exit', 'quit', or 'q' to leave.[/green]")
    console.print(f"[dim]Loaded tools: {', '.join([t.name for t in tools])}[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold yellow]You[/bold yellow]")
            
            if user_input.lower() in ('exit', 'quit', 'q'):
                console.print("[blue]Goodbye![/blue]")
                break
            
            if not user_input.strip():
                continue

            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                response = agent.run(user_input)

            console.print(Panel(Markdown(response), title="[bold cyan]Agent[/bold cyan]", expand=False))
            console.print("")

        except KeyboardInterrupt:
            console.print("\n[blue]Goodbye![/blue]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()
