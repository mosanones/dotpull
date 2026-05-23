"""Tests for dotpull.template module."""

import pytest
from pathlib import Path

from dotpull.template import (
    render_template,
    render_file,
    collect_variables,
    TemplateError,
)


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------

def test_render_template_substitutes_variables():
    result = render_template("Hello, {{ name }}!", {"name": "Alice"})
    assert result == "Hello, Alice!"


def test_render_template_multiple_variables():
    template = "[user]\nname = {{ username }}\nemail = {{ email }}"
    variables = {"username": "bob", "email": "bob@example.com"}
    result = render_template(template, variables)
    assert result == "[user]\nname = bob\nemail = bob@example.com"


def test_render_template_whitespace_in_placeholder():
    result = render_template("{{  home  }}", {"home": "/home/user"})
    assert result == "/home/user"


def test_render_template_strict_raises_on_undefined():
    with pytest.raises(TemplateError, match="Undefined variable 'missing'"):
        render_template("value = {{ missing }}", {}, strict=True)


def test_render_template_non_strict_leaves_placeholder():
    result = render_template("value = {{ missing }}", {}, strict=False)
    assert result == "value = {{ missing }}"


def test_render_template_no_placeholders():
    content = "plain text without any placeholders"
    assert render_template(content, {}) == content


# ---------------------------------------------------------------------------
# render_file
# ---------------------------------------------------------------------------

def test_render_file_substitutes_variables(tmp_path: Path):
    template_file = tmp_path / "gitconfig.tmpl"
    template_file.write_text("[user]\n\tname = {{ name }}\n\temail = {{ email }}\n")

    result = render_file(template_file, {"name": "Carol", "email": "carol@example.com"})
    assert "Carol" in result
    assert "carol@example.com" in result


def test_render_file_raises_when_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        render_file(tmp_path / "nonexistent.tmpl", {})


# ---------------------------------------------------------------------------
# collect_variables
# ---------------------------------------------------------------------------

def test_collect_variables_returns_sorted_unique_names():
    template = "{{ b }} and {{ a }} and {{ b }} again"
    assert collect_variables(template) == ["a", "b"]


def test_collect_variables_empty_when_no_placeholders():
    assert collect_variables("no placeholders here") == []
