"""
Warren — CLI entry point.
No business logic here. All logic lives in agents/orchestrator.py.
"""
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from agents.orchestrator import run

console = Console()


def main() -> None:
    console.print("\n[bold green]Warren 2.0[/bold green] — Personal Investment Research Agent")
    console.print("Type your question and press Enter. Type [bold]exit[/bold] to quit.\n")

    history: list[dict] = []

    while True:
        try:
            question = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if question.strip().lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            break

        if not question.strip():
            continue

        console.print("\n[bold yellow]Warren[/bold yellow] is thinking...\n")

        try:
            answer = run(question=question, history=history)
            console.print(Markdown(answer))
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

        console.print()


if __name__ == "__main__":
    main()
