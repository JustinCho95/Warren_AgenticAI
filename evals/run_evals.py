"""
Run Warren against all test cases and print a pass/fail report.
Usage: python -m evals.run_evals
"""
import json
import os
from rich.console import Console
from rich.table import Table
from agents.orchestrator import run
from agents.evaluator import evaluate_answer

console = Console()

TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.json")


def run_evals() -> None:
    with open(TEST_CASES_PATH) as f:
        test_cases = json.load(f)

    results = []
    table = Table(title="Warren Eval Results", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Category")
    table.add_column("Question", max_width=40)
    table.add_column("Score", justify="center")
    table.add_column("Pass", justify="center")
    table.add_column("Feedback", max_width=50)

    passed = 0
    for tc in test_cases:
        console.print(f"[dim]Running {tc['id']}: {tc['question'][:60]}...[/dim]")
        try:
            answer = run(question=tc["question"])
            eval_result = evaluate_answer(
                question=tc["question"],
                answer=answer,
                expected=", ".join(tc.get("expected_contains", [])),
            )
        except Exception as e:
            eval_result = {"score": 0, "pass": False, "feedback": str(e)}

        if eval_result["pass"]:
            passed += 1

        table.add_row(
            tc["id"],
            tc.get("category", "-"),
            tc["question"][:60],
            str(eval_result["score"]),
            "[green]✓[/green]" if eval_result["pass"] else "[red]✗[/red]",
            eval_result.get("feedback", "")[:100],
        )
        results.append({**tc, "eval": eval_result})

    console.print(table)
    console.print(f"\n[bold]Result: {passed}/{len(test_cases)} passed[/bold]")

    # Save results
    output_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    console.print(f"[dim]Full results saved to {output_path}[/dim]")


if __name__ == "__main__":
    run_evals()
