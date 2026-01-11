"""Create HTML and JSON indices of CSL styles.

The `index` variables have to be sorted before passing to this module.
"""

import json
from collections.abc import Callable, Iterable
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
    """Path to the original CSL file, relative to `styles_dir`."""
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


def build_original_mapper() -> Callable[[Path], str]:
    """Build a mapper that maps paths to original CSL files to their downloadable URLs.

    Paths should be relative to `styles_dir`.
    """
    status = run(
        ["git", "submodule", "status"], text=True, capture_output=True, check=True
    ).stdout
    submodules: dict[Path, str] = {}

    for line in status.splitlines():
        (commit, path, *_ref) = line.strip().split()
        assert path == "styles/chinese", "Only styles/chinese is supported at present."
        submodules[Path("chinese")] = (
            f"https://github.com/zotero-chinese/styles/raw/{commit[:7]}/"
        )

    def mapper(original: Path) -> str:
        assert not original.is_absolute()
        for submodule_path, base_url in submodules.items():
            try:
                relative_path = original.relative_to(submodule_path)
                return base_url + relative_path.as_posix()
            except ValueError:
                continue
        raise ValueError(f"Cannot map original path: {original}")

    return mapper


def make_json_index(index: Iterable[IndexEntry], dist_dir: Path) -> str:
    original_to_url = build_original_mapper()
    return json.dumps(
        {
            entry.info.id: {
                "title": entry.info.title,
                "updated": entry.info.updated,
                "original_url": original_to_url(entry.original),
                "sanitized_url": f"./{entry.sanitized.relative_to(dist_dir).as_posix()}",
                "diff_url": f"./{entry.diff.relative_to(dist_dir).as_posix()}",
                "changes": list(entry.changes),
            }
            for entry in index
        },
        ensure_ascii=False,
        indent=2,
    )
