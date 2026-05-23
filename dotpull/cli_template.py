"""CLI commands for template rendering and variable inspection."""

import click
import sys
from pathlib import Path

from dotpull.config import load_config, validate_config
from dotpull.profile import Profile
from dotpull.template import render_file, collect_variables, TemplateError


def _load(config_path: str):
    config = load_config(config_path)
    issues = validate_config(config)
    if issues:
        for issue in issues:
            click.echo(f"Config error: {issue}", err=True)
        sys.exit(1)
    return config


@click.group(name="template")
def template_group():
    """Inspect and render dotfile templates."""


@template_group.command("render")
@click.argument("file", type=click.Path(exists=True))
@click.option("--profile", "-p", default="default", show_default=True, help="Profile name to use for variables.")
@click.option("--config", "-c", default="dotpull.toml", show_default=True)
@click.option("--strict", is_flag=True, default=False, help="Fail on undefined variables.")
@click.option("--output", "-o", default=None, help="Write output to file instead of stdout.")
def cmd_render(file, profile, config, strict, output):
    """Render a template file using profile variables."""
    cfg = _load(config)
    profiles_raw = cfg.get("profiles", {})
    try:
        prof = Profile(profile, profiles_raw)
        variables = prof.variables()
    except KeyError:
        click.echo(f"Profile '{profile}' not found.", err=True)
        sys.exit(1)

    try:
        rendered = render_file(Path(file), variables, strict=strict)
    except TemplateError as e:
        click.echo(f"Template error: {e}", err=True)
        sys.exit(1)

    if output:
        Path(output).write_text(rendered)
        click.echo(f"Rendered output written to {output}")
    else:
        click.echo(rendered, nl=False)


@template_group.command("vars")
@click.argument("file", type=click.Path(exists=True))
def cmd_vars(file):
    """List all template variables referenced in a file."""
    variables = collect_variables(Path(file))
    if not variables:
        click.echo("No template variables found.")
    else:
        click.echo(f"Variables in {file}:")
        for var in sorted(variables):
            click.echo(f"  - {var}")
