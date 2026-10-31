"""Tests for the brand-guidelines font validator (issue #941).

`validate_fonts` used to search the whole `font-family` declaration for any
approved font substring, so an approved fallback hid an unapproved first choice
and `NotSegoe UI` matched `Segoe UI`.
"""

from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

import pytest

VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "custom_skills"
    / "applying-brand-guidelines"
    / "validate_brand.py"
)


@pytest.fixture(scope="module")
def validator() -> Any:
    """A BrandValidator built on the shipped Acme guidelines."""
    module = runpy.run_path(str(VALIDATOR_PATH))
    guidelines_factory = module["get_acme_corporation_guidelines"]
    return module["BrandValidator"](guidelines_factory())


@pytest.mark.parametrize(
    ("declaration", "approved"),
    [
        # approved control: every family in the stack is allowed
        ("font-family: Segoe UI, sans-serif;", True),
        ("font-family: system-ui;", True),
        ("font-family: -apple-system;", True),
        # rejected control
        ("font-family: Comic Sans MS;", False),
        # an approved fallback must not hide an unapproved first choice
        ("font-family: Comic Sans MS, sans-serif;", False),
        ("font-family: Papyrus, system-ui;", False),
        # a family name is matched whole, not as a substring of an approved one
        ("font-family: NotSegoe UI;", False),
    ],
)
def test_font_stack_is_checked_family_by_family(
    validator: Any, declaration: str, approved: bool
) -> None:
    """Each family in a stack is validated on its own (issue #941)."""
    assert validator.validate(declaration).passed is approved


def test_prohibited_family_is_named_in_the_violation(validator: Any) -> None:
    """The violation names the family that failed, not the whole stack."""
    result = validator.validate("font-family: Comic Sans MS, sans-serif;")

    assert result.violations == ["Unapproved font used: Comic Sans MS"]
