import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TextIO

import click

from .csl import dump_csl, load_csl, write_csl
from .normalize import normalize_csl
from .util import ns

ET.register_namespace("", ns["cs"])  # Required by `dump_csl`


@click.command()
@click.argument("input", type=click.File("r", encoding="utf-8"))
@click.argument(
    "output",
    type=click.Path(dir_okay=False, allow_dash=True, path_type=Path),
    required=False,
)
def cli(input: TextIO, output: Path | None) -> None:
    """Sanitize the CSL file INPUT and write the result to OUTPUT.

    If OUTPUT is omitted, then it defaults to the INPUT path with a `.sanitized.csl` suffix.

    Use `-` as INPUT to read from stdin, or as OUTPUT to write to stdout. Note that OUTPUT cannot be omitted when reading from stdin.

    To sanitize in place, specify the same path for INPUT and OUTPUT.
    """
    if output is None:
        if input.name == "<stdin>":
            raise click.UsageError(
                "Missing the argument OUTPUT. It is required when INPUT is `-` (stdin)."
            )
        input_path = Path(input.name)
        output = input_path.with_suffix(f".sanitized{input_path.suffix}")

    style = load_csl(input.read())

    changed = False
    for message in normalize_csl(style):
        changed = True
        click.echo(message, err=True)

    if str(output) == "-":
        click.echo(dump_csl(style))
        output_name = "`-` (stdout)"
    else:
        write_csl(style, output)
        output_name = f"`{output}`"

    if changed:
        click.echo(f"✅ Written to {output_name}.", err=True)
    else:
        click.echo(
            f"⚠️ Written to {output_name}, but no changes were made. This style may be usable in Hayagriva as is.",
            err=True,
        )


if __name__ == "__main__":
    cli()
