# Copyright 2022 Amethyst Reese
# Licensed under the MIT license

import logging
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import click
from moreorless.click import echo_color_precomputed_diff

from .__version__ import __version__
from .core import Result, ufmt_paths
from .types import Options


def init_logging(*, debug: Optional[bool] = None) -> None:
    format = "%(message)s" if not debug else "%(levelname)s %(name)s %(message)s"
    level = (
        logging.DEBUG if debug else (logging.INFO if debug is None else logging.ERROR)
    )
    logging.basicConfig(stream=sys.stderr, level=level, format=format)
    logging.getLogger("blib2to3").setLevel(logging.WARNING)


def echo_results(
    results: Iterable[Result], diff: bool = False, quiet: bool = False
) -> Tuple[int, int]:
    empty = True
    error = 0
    changed = 0
    written = 0
    clean = 0

    for result in results:
        empty = False

        if result.error is not None:
            msg = str(result.error)
            lines = msg.splitlines()
            msg = lines[0]
            click.secho(f"Error formatting {result.path}: {msg}", fg="yellow", err=True)
            error += 1

        elif result.skipped:
            reason = f": {result.skipped}" if isinstance(result.skipped, str) else ""
            if not quiet:
                click.secho(f"Skipped {result.path}{reason}", err=True)

        elif result.changed:
            if result.written:
                written += 1
                if not quiet:
                    click.secho(f"Formatted {result.path}", err=True)
            else:
                changed += 1
                click.secho(f"Would format {result.path}", err=True)
            if diff and result.diff:
                echo_color_precomputed_diff(result.diff)

        else:
            clean += 1

    if empty:
        click.secho("No files found", fg="yellow", err=True)
        error += 1

    if not quiet:

        def f(v: int) -> str:
            return "file" if v == 1 else "files"

        reports = []
        if error:
            reports += [click.style(f"{error} errors", fg="yellow", bold=True)]
        if changed:
            reports += [
                click.style(f"{changed} {f(changed)} would be formatted", bold=True)
            ]
        if written:
            reports += [click.style(f"{written} {f(written)} formatted")]
        if clean:
            reports += [click.style(f"{clean} {f(clean)} already formatted")]

        message = ", ".join(reports)
        click.secho(f"✨ {message} ✨", err=True)

    return (changed + written), error


@click.group()
@click.pass_context
@click.version_option(__version__, "--version", "-V")
@click.option(
    "--debug/--quiet",
    "-v/-q",
    is_flag=True,
    default=None,
    help="Enable debug/verbose output",
)
def main(ctx: click.Context, debug: Optional[bool]):
    init_logging(debug=debug)
    ctx.obj = Options(
        debug=debug is True,
        quiet=debug is False,
    )


@main.command()
@click.pass_context
@click.argument(
    "names", type=click.Path(allow_dash=True), nargs=-1, metavar="[PATH] ..."
)
def check(ctx: click.Context, names: List[str]):
    """Check formatting of one or more paths"""
    options: Options = ctx.obj
    paths = [Path(name) for name in names] if names else [Path(".")]
    results = ufmt_paths(paths, dry_run=True)
    changed, error = echo_results(results, quiet=options.quiet)
    if changed or error:
        ctx.exit(1)


@main.command()
@click.pass_context
@click.argument(
    "names", type=click.Path(allow_dash=True), nargs=-1, metavar="[PATH] ..."
)
def diff(ctx: click.Context, names: List[str]):
    """Generate diffs for any files that need formatting"""
    options: Options = ctx.obj
    paths = [Path(name) for name in names] if names else [Path(".")]
    results = ufmt_paths(paths, dry_run=True, diff=True)
    changed, error = echo_results(results, diff=True, quiet=options.quiet)
    if changed or error:
        ctx.exit(1)


@main.command()
@click.pass_context
@click.argument(
    "names", type=click.Path(allow_dash=True), nargs=-1, metavar="[PATH] ..."
)
def format(ctx: click.Context, names: List[str]):
    """Format one or more paths in place"""
    options: Options = ctx.obj
    paths = [Path(name) for name in names] if names else [Path(".")]
    results = ufmt_paths(paths)
    _, error = echo_results(results, quiet=options.quiet)
    if error:
        ctx.exit(1)
