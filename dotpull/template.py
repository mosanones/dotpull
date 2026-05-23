"""Template rendering for dotfiles with variable substitution."""

import re
from pathlib import Path
from typing import Dict, Optional


VARIABLE_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""
    pass


def render_template(content: str, variables: Dict[str, str], strict: bool = True) -> str:
    """Render a template string by substituting {{ variable }} placeholders.

    Args:
        content: The template string to render.
        variables: A mapping of variable names to their values.
        strict: If True, raise TemplateError for undefined variables.

    Returns:
        The rendered string with all variables substituted.

    Raises:
        TemplateError: If strict=True and an undefined variable is encountered.
    """
    def replace_match(match: re.Match) -> str:
        key = match.group(1)
        if key not in variables:
            if strict:
                raise TemplateError(
                    f"Undefined variable '{{key}}' in template. "
                    f"Available variables: {sorted(variables.keys())}"
                )
            return match.group(0)  # leave placeholder intact
        return variables[key]

    return VARIABLE_PATTERN.sub(replace_match, content)


def render_file(source: Path, variables: Dict[str, str], strict: bool = True) -> str:
    """Read a file and render it as a template.

    Args:
        source: Path to the source template file.
        variables: A mapping of variable names to their values.
        strict: If True, raise TemplateError for undefined variables.

    Returns:
        The rendered file content as a string.

    Raises:
        FileNotFoundError: If the source file does not exist.
        TemplateError: If strict=True and an undefined variable is encountered.
    """
    if not source.exists():
        raise FileNotFoundError(f"Template file not found: {source}")

    content = source.read_text(encoding="utf-8")
    return render_template(content, variables, strict=strict)


def collect_variables(template: str) -> list[str]:
    """Return a sorted list of unique variable names found in a template string."""
    return sorted(set(VARIABLE_PATTERN.findall(template)))
