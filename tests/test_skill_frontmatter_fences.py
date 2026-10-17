import pytest

from skills.skill_utils import validate_skill_directory


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_delimiter_inside_metadata_does_not_close_frontmatter(tmp_path, newline):
    content = newline.join(
        ["---", "name: example---detail", "description: A useful example", "---", "Body"]
    )
    (tmp_path / "SKILL.md").write_bytes(content.encode("utf-8"))
    result = validate_skill_directory(str(tmp_path))
    assert result["valid"] is True
    assert result["errors"] == []


@pytest.mark.parametrize(
    "text",
    [
        "---oops\nname: example\ndescription: Example\n---\nBody",
        "---\nname: example\ndescription: Example --- body",
    ],
)
def test_inline_or_malformed_fences_are_rejected(tmp_path, text):
    (tmp_path / "SKILL.md").write_text(text, encoding="utf-8")
    assert validate_skill_directory(str(tmp_path))["valid"] is False


def test_required_fields_are_still_checked(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: example\n---\nBody", encoding="utf-8")
    result = validate_skill_directory(str(tmp_path))
    assert result["valid"] is False
    assert "YAML frontmatter must include 'description' field" in result["errors"]
