"""Create HTML and JSON indices of CSL styles.

The `index` variables have to be sorted before passing to this module.
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from subprocess import run
from typing import Literal

from .csl import CslInfo


@dataclass
class IndexEntry:
    info: CslInfo
    sanitized: Path
    original: Path
    diff: Path
    """Path to side by side comparison with change highlights."""
    changes: Iterable[str]
    """Brief descriptions of the changes."""


def make_human_index(*, root: Path, json_index: Path, lang: Literal["zh", "en"]) -> str:
    return run(
        [
            "typst",
            "compile",
            Path(__file__).with_suffix(".typ"),
            "-",
            "--format=html",
            "--features=html",
            *("--root", root),
            *("--input", f"json-index=/{json_index.relative_to(root).as_posix()}"),
            *("--input", f"lang={lang}"),
        ],
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def make_json_index(index: Iterable[IndexEntry], dist_dir: Path) -> str:
    return json.dumps(
        {
            entry.info.id: {
                "title": entry.info.title,
                "updated": entry.info.updated,
                "sanitized_url": f"./{entry.sanitized.relative_to(dist_dir).as_posix()}",
                "diff_url": f"./{entry.diff.relative_to(dist_dir).as_posix()}",
                "changes": list(entry.changes),
            }
            for entry in index
        },
        ensure_ascii=False,
        indent=2,
    )
