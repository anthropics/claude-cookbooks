"""Offline regression tests for the retrieval assertion's result contract."""

import ast

import pytest

from capabilities.retrieval_augmented_generation.evaluation.eval_retrieval import get_assert


@pytest.mark.parametrize(
    ("output", "correct_chunks", "error_type"),
    [
        (["a"], "not a Python literal", SyntaxError),
        ([["a"]], "['a']", TypeError),
        (None, "['a']", TypeError),
    ],
    ids=["malformed-expected-data", "unhashable-retrieved-item", "noniterable-output"],
)
def test_invalid_retrieval_returns_failed_assertion(output, correct_chunks, error_type):
    # Capture the underlying diagnostic without depending on Python's error wording.
    with pytest.raises(error_type) as error:
        expected = ast.literal_eval(correct_chunks)
        set(output) & set(expected)

    result = get_assert(output, {"vars": {"correct_chunks": correct_chunks}})

    reason = f"Unexpected error: {error.value}"
    assert result["pass"] is False
    assert result["score"] == 0
    assert result["reason"] == reason
    assert result["componentResults"] == [
        {"pass": False, "score": 0, "reason": reason, "named_scores": {name: 0}}
        for name in ("MRR", "Precision", "Recall", "F1")
    ]


@pytest.mark.parametrize(
    ("output", "correct_chunks", "passed", "precision", "recall", "mrr", "f1"),
    [
        (["a"], "['a']", True, 1, 1, 1, 1),
        (["x", "a"], "['a', 'b']", True, 0.5, 0.5, 0.5, 0.5),
        (["a"], "['a', 'b', 'c', 'd', 'e', 'f']", False, 1, 1 / 6, 1, 2 / 7),
        (["x"], "['a']", False, 0, 0, 0, 0),
        ([], "['a']", False, 0, 0, 0, 0),
        (["a"], "[]", False, 0, 0, 0, 0),
    ],
    ids=["perfect", "partial", "below-threshold", "no-match", "empty-output", "empty-expected"],
)
def test_valid_retrieval_preserves_scoring(
    output, correct_chunks, passed, precision, recall, mrr, f1
):
    result = get_assert(output, {"vars": {"correct_chunks": correct_chunks}})

    assert result["pass"] is passed
    assert result["score"] == pytest.approx(f1)
    assert result["reason"].startswith("Precision:")
    components = result["componentResults"]
    assert len(components) == 4
    for component, (name, score) in zip(
        components,
        (("MRR", mrr), ("Precision", precision), ("Recall", recall), ("F1", f1)),
        strict=True,
    ):
        assert component["pass"] is True
        assert component["score"] == pytest.approx(score)
        assert component["named_scores"] == {name: pytest.approx(score)}
        assert component["reason"] == f"{name} is {component['score']}"
