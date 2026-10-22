"""
Interactive Rich Terminal Interface for PyMaster.
"""

import sys
import os
import argparse
from typing import Dict, Any

# Ensure UTF-8 output on Windows consoles to prevent cp1252 charmap encoding crashes
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from pymaster.agent.core import PyMasterAgent
from pymaster.llm.client import LocalLLMClient
from pymaster.tools.base import registry

console = Console(safe_box=True)


def print_banner(model: str, endpoint: str, healthy: bool):
    status_color = "green" if healthy else "red"
    status_text = "ONLINE" if healthy else "OFFLINE (Start Ollama/LM Studio or standalone runner)"

    banner_text = f"""[bold cyan]
  ██████╗ ██╗   ██╗███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ 
  ██╔══██╗╚██╗ ██╔╝████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
  ██████╔╝ ╚████╔╝ ██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝
  ██╔═══╝   ╚██╔╝  ██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗
  ██║        ██║   ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║
  ╚═╝        ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
[/bold cyan]
[dim]Autonomous Local Python Coding & Engineering Agent[/dim]
[bold]Model:[/bold] {model} | [bold]Endpoint:[/bold] {endpoint} | [bold {status_color}]Status: {status_text}[/bold {status_color}]
[dim]Type [bold white]/help[/bold white] for commands, [bold white]/exit[/bold white] to quit. Describe what you want to build![/dim]
"""
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def display_tools_table():
    table = Table(title="PyMaster Registered Tools", border_style="cyan")
    table.add_column("Tool Name", style="bold green")
    table.add_column("Description", style="white")
    table.add_column("Parameters", style="dim cyan")

    for tool in registry.list_tools():
        props = list(tool.parameters.get("properties", {}).keys())
        table.add_row(tool.name, tool.description, ", ".join(props))

    console.print(table)


def on_tool_start(name: str, args: Dict[str, Any]):
    console.print(f"\n[bold yellow]>> [Tool Call][/bold yellow] [bold cyan]{name}[/bold cyan]")
    if "content" in args and len(args["content"]) > 100:
        # Don't flood the terminal if writing a large file
        preview_args = dict(args)
        preview_args["content"] = f"<Text block: {len(args['content'])} characters>"
        console.print(f"   [dim]{preview_args}[/dim]")
    else:
        console.print(f"   [dim]{args}[/dim]")


def on_tool_result(name: str, result: Any):
    res_str = str(result)
    if "Error" in res_str or "FAILED" in res_str or "SYNTAX ERROR" in res_str:
        color = "red"
        icon = "[FAIL]"
    else:
        color = "green"
        icon = "[OK]"

    preview = res_str[:400] + ("..." if len(res_str) > 400 else "")
    console.print(f"   [bold {color}]{icon} [{name} Result]:[/bold {color}] {preview}\n")


def interactive_repl(agent: PyMasterAgent, model: str, endpoint: str):
    healthy = agent.llm.check_health()
    print_banner(model, endpoint, healthy)

    while True:
        try:
            user_input = console.input("[bold cyan]PyMaster > [/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Exiting PyMaster. Happy coding![/dim]")
            break

        if not user_input:
            continue

        # Command handling
        if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input.lower() == "/help":
            console.print(Panel("""[bold white]PyMaster Commands:[/bold white]
  [cyan]/model <name>[/cyan] - Switch active model (e.g. /model qwen2.5-coder:3b)
  [cyan]/models[/cyan]       - List all models found on the local server
  [cyan]/tools[/cyan]        - List all available inspection, editing, and execution tools
  [cyan]/reset[/cyan]        - Clear conversation context and start fresh
  [cyan]/exit[/cyan]         - Exit PyMaster
  [cyan]<anything else>[/cyan] - Natural language request to architect, build, or debug Python code!
""", border_style="blue"))
            continue

        if user_input.lower().startswith("/model"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                new_model = parts[1].strip()
                agent.llm.model = new_model
                console.print(f"[bold green]✔ Switched active model to:[/bold green] [bold cyan]{new_model}[/bold cyan]")
            else:
                models = agent.llm.list_local_models()
                console.print(f"[bold yellow]Current model:[/bold yellow] {agent.llm.model}")
                if models:
                    console.print(f"[bold green]Available models to switch to:[/bold green] {', '.join(models)}")
                    console.print("[dim]Usage: /model <name> (e.g. /model qwen2.5-coder:3b)[/dim]")
            continue

        if user_input.lower() == "/tools":
            display_tools_table()
            continue

        if user_input.lower() == "/models":
            models = agent.llm.list_local_models()
            if models:
                console.print(f"[bold green]Models available on {endpoint}:[/bold green]\n" + "\n".join(f"  - {m}" for m in models))
            else:
                console.print(f"[bold yellow]No models returned from {endpoint}. Is the server running?[/bold yellow]")
            continue

        if user_input.lower() == "/reset":
            agent.reset_conversation()
            console.print("[bold green]Conversation context reset.[/bold green]")
            continue

        # Clean input if user accidentally pasted command-line syntax into the REPL
        cleaned_input = user_input.strip()
        if "--prompt" in cleaned_input:
            import re
            match = re.search(r'--prompt\s+["\']?([^"\']+)["\']?', cleaned_input)
            if match:
                cleaned_input = match.group(1).strip()
        elif cleaned_input.startswith("python -m pymaster.cli"):
            cleaned_input = cleaned_input.replace("python -m pymaster.cli", "").strip().strip('"\'')

        # Agent execution
        console.print("[dim]Thinking & Architecting...[/dim]")
        try:
            agent.run_turn(
                user_input=cleaned_input,
                token_callback=lambda token: console.print(token, end="", style="bright_white"),
                tool_start_callback=on_tool_start,
                tool_result_callback=on_tool_result,
            )
        except Exception as e:
            console.print(Panel(f"[bold red]Execution Error:[/bold red] {e}", border_style="red"))
        console.print("\n")


def main():
    parser = argparse.ArgumentParser(description="PyMaster: Autonomous Local Python Coding Agent")
    parser.add_argument("--model", type=str, default="", help="Model name (e.g. qwen3.5:4b, qwen2.5-coder:1.5b)")
    parser.add_argument("--url", type=str, default="http://localhost:11434/v1", help="Local endpoint URL")
    parser.add_argument("--prompt", type=str, default="", help="Single prompt execution mode")
    parser.add_argument("--max-turns", type=int, default=15, help="Maximum agent autonomous turns")
    args = parser.parse_args()

    client = LocalLLMClient(base_url=args.url, model=args.model or "qwen2.5-coder:1.5b")
    
    # Auto-detect available model if not explicitly specified
    available_models = client.list_local_models()
    if not args.model:
        if available_models:
            # Prefer 3b for maximum speed on consumer GPUs, then 7b, then others
            if "qwen2.5-coder:3b" in available_models:
                client.model = "qwen2.5-coder:3b"
            elif "qwen2.5-coder:7b" in available_models:
                client.model = "qwen2.5-coder:7b"
            else:
                coder_models = [m for m in available_models if "code" in m.lower()]
                client.model = coder_models[0] if coder_models else available_models[0]
        else:
            client.model = "qwen2.5-coder:3b"
    else:
        client.model = args.model

    agent = PyMasterAgent(llm_client=client, max_turns=args.max_turns)

    if args.prompt:
        console.print(f"[bold cyan]Running task:[/bold cyan] {args.prompt} (Model: [green]{client.model}[/green])")
        try:
            agent.run_turn(
                user_input=args.prompt,
                token_callback=lambda token: console.print(token, end="", style="white"),
                tool_start_callback=on_tool_start,
                tool_result_callback=on_tool_result,
            )
        except Exception as e:
            console.print(Panel(f"[bold red]Execution Error:[/bold red] {e}", border_style="red"))
    else:
        interactive_repl(agent, client.model, args.url)


if __name__ == "__main__":
    main()
