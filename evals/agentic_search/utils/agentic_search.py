"""Helpers for the agentic-search benchmark reproduction cookbook.

Dataset samples, grader prompts, and a lightweight transcript renderer.
The agentic loop itself lives in the notebook so it stays editable.
"""

import re
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Sample questions
#
# Three illustrative questions written for this cookbook to span single-fact,
# set-answer, and multi-item shapes. They are NOT drawn from DeepSearchQA-900;
# see the Datasets section of the notebook for the real benchmark.
# ---------------------------------------------------------------------------

SAMPLE_QUESTIONS: list[dict[str, str]] = [
    {
        "example_id": "demo-0",
        "problem": (
            "Among the chief executives of the four largest US banks by "
            "total assets as of Q1 2024, which one had held their CEO "
            "position the longest?"
        ),
        "answer": "Jamie Dimon",
        "answer_type": "Single Answer",
    },
    {
        "example_id": "demo-1",
        "problem": (
            "Which three countries had the largest installed offshore wind "
            "capacity at the end of 2023?"
        ),
        "answer": "China, United Kingdom, Germany",
        "answer_type": "Set Answer",
    },
    {
        "example_id": "demo-2",
        "problem": (
            "List the films that won the Palme d'Or at the Cannes Film "
            "Festival in 2021, 2022, and 2023, and name the director of each."
        ),
        "answer": (
            "Titane (Julia Ducournau), Triangle of Sadness (Ruben Östlund), "
            "Anatomy of a Fall (Justine Triet)"
        ),
        "answer_type": "Set Answer",
    },
]


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

USER_PROMPT_TEMPLATE = """\
I want you to answer the following question.

<question>{question}</question>

First plan out your response. This part can be as long as needed. \
You may need to run many searches, this is totally fine.

Then provide a short and concise answer in <result> tags. \
For questions expecting multiple answers, separate them with commas."""


GRADER_PROMPT_TEMPLATE = """\
Your task is to evaluate whether a given response arrived at the correct answer.

Question:
<question>{question}</question>

Correct answer (type: {answer_type}):
<correct_answer>{answer}</correct_answer>

Response to evaluate:
<response>{response}</response>

For each expected answer item, indicate whether it appears in the response. \
Then list any answers in the response that are NOT in the correct-answer list. \
Wording does not need to match exactly.

Reply in this exact XML format:
<evaluation>
  <explanation>one sentence</explanation>
  <correctness_details>
    <item answer="expected_item_1" correct="true|false"/>
  </correctness_details>
  <excessive_answers>
    <item>extra_item_if_any</item>
  </excessive_answers>
</evaluation>"""


_RESULT_TAG_RE = re.compile(r"<result>(.*?)</result>", re.DOTALL | re.IGNORECASE)


def extract_result_tag(text: str) -> str | None:
    """Return the contents of the last <result>...</result> in `text`, or None."""
    matches = _RESULT_TAG_RE.findall(text)
    return matches[-1].strip() if matches else None


def _first_text(msg: anthropic.types.Message) -> str:
    """Return the first text block's content (skips thinking/tool blocks)."""
    return next(b.text for b in msg.content if isinstance(b, anthropic.types.TextBlock))


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------


def grade_response(
    client: anthropic.Anthropic,
    grader_model: str,
    question: dict[str, str],
    response_text: str,
) -> dict[str, Any]:
    """Score a single response with the F1 grader. Returns precision/recall/F1."""
    extracted = extract_result_tag(response_text) or response_text
    prompt = GRADER_PROMPT_TEMPLATE.format(
        question=question["problem"],
        answer=question["answer"],
        answer_type=question["answer_type"],
        response=extracted,
    )
    grader_msg = client.messages.create(
        model=grader_model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    grader_text = _first_text(grader_msg)

    items = re.findall(
        r'<item\s+answer="([^"]+)"\s+correct="(true|false)"\s*/?>', grader_text
    )
    ex_block = re.search(
        r"<excessive_answers>(.*?)</excessive_answers>", grader_text, re.DOTALL
    )
    excessive = re.findall(r"<item>([^<]+)</item>", ex_block.group(1)) if ex_block else []

    n_truth = len(items)
    n_correct = sum(1 for _, c in items if c == "true")
    n_excess = len(excessive)
    submitted = n_correct + n_excess

    precision = n_correct / submitted if submitted else 0.0
    recall = n_correct / n_truth if n_truth else (1.0 if submitted == 0 else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "example_id": question["example_id"],
        "extracted_answer": extracted,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "grader_text": grader_text,
    }


# ---------------------------------------------------------------------------
# BrowseComp grading (single-answer match: A=correct, B=wrong, C=abstain)
# ---------------------------------------------------------------------------

BROWSECOMP_GRADER_PROMPT = """\
I'm going to show you a question, a ground-truth answer, and a sample answer. \
Tell me whether the sample answer is correct relative to the ground truth. \
The wording need not match exactly.

<question>{question}</question>
<sample_answer>{sample_answer}</sample_answer>
<ground_truth>{ground_truth}</ground_truth>

Consider these statements about the sample answer:
 (A) It matches the ground-truth answer.
 (B) It does not match the ground-truth answer.
 (C) It says something like "I'm not sure" or "I don't know".

Respond with exactly one letter (A, B, or C) and nothing else."""


def grade_browsecomp(
    client: anthropic.Anthropic,
    grader_model: str,
    question: dict[str, str],
    response_text: str,
) -> dict[str, Any]:
    """Score a BrowseComp response: accuracy = 1 iff the grader returns 'A'."""
    extracted = extract_result_tag(response_text) or response_text
    msg = client.messages.create(
        model=grader_model,
        max_tokens=8,
        messages=[
            {
                "role": "user",
                "content": BROWSECOMP_GRADER_PROMPT.format(
                    question=question["problem"],
                    sample_answer=extracted,
                    ground_truth=question["answer"],
                ),
            }
        ],
    )
    letter_match = re.search(r"\b([ABC])\b", _first_text(msg))
    letter = letter_match.group(1) if letter_match else None
    return {
        "example_id": question["example_id"],
        "extracted_answer": extracted,
        "grader_letter": letter,
        "accuracy": 1.0 if letter == "A" else 0.0,
    }


# ---------------------------------------------------------------------------
# Transcript rendering
# ---------------------------------------------------------------------------


def summarize_response(response: anthropic.types.Message) -> str:
    """One-line-per-block summary of a Messages API response, for transcript display."""
    lines: list[str] = []
    for block in response.content:
        btype = getattr(block, "type", "?")
        if btype == "thinking":
            lines.append(f"  [thinking]  {len(block.thinking)} chars")
        elif btype == "text":
            preview = block.text.replace("\n", " ")[:100]
            lines.append(f"  [text]      {preview}")
        elif btype == "server_tool_use":
            lines.append(f"  [tool_use]  {block.name}")
        elif btype == "compaction":
            lines.append("  [compaction]")
        else:
            lines.append(f"  [{btype}]")
    u = response.usage
    lines.append(
        f"  usage: in={u.input_tokens:,} out={u.output_tokens:,} "
        f"cache_read={getattr(u, 'cache_read_input_tokens', 0) or 0:,} "
        f"stop={response.stop_reason}"
    )
    return "\n".join(lines)
