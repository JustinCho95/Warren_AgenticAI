import anthropic
from config.settings import ANTHROPIC_API_KEY, EVAL_MODEL


def evaluate_answer(question: str, answer: str, expected: str | None = None) -> dict:
    """
    Use Claude Haiku as a judge to score Warren's answer.
    Returns a dict with score (0-100), pass/fail, and feedback.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    expected_section = (
        f"\nExpected answer (ground truth):\n{expected}\n" if expected else ""
    )

    prompt = f"""You are an evaluator for an AI investment research assistant called Warren.
Score the following answer on a scale of 0-100.

Question: {question}
{expected_section}
Warren's answer:
{answer}

Evaluate on these criteria:
1. Accuracy — are the facts correct and sourced? (40 points)
2. Completeness — does it address the question fully? (30 points)
3. Reasoning — is the logic sound and well-explained? (20 points)
4. Actionability — does it give a clear, useful conclusion? (10 points)

Respond in this exact format:
SCORE: <number>
PASS: <yes/no> (pass = score >= 70)
FEEDBACK: <one paragraph of specific feedback>
"""

    response = client.messages.create(
        model=EVAL_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    lines = text.strip().split("\n")

    score = 0
    passed = False
    feedback = ""

    for line in lines:
        if line.startswith("SCORE:"):
            try:
                score = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("PASS:"):
            passed = "yes" in line.lower()
        elif line.startswith("FEEDBACK:"):
            feedback = line.split(":", 1)[1].strip()

    return {
        "score": score,
        "pass": passed,
        "feedback": feedback,
        "model": EVAL_MODEL,
    }
