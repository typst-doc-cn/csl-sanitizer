import re
import xml.etree.ElementTree as ET
from collections import deque
from collections.abc import Generator
from difflib import HtmlDiff
from enum import IntEnum
from locale import LC_COLLATE, setlocale, strxfrm
from pathlib import Path
from sys import argv

from .csl import CslInfo, check_csl, read_csl, write_csl
from .indexing import IndexEntry, make_human_index, make_json_index
from .normalize import normalize_csl
from .util import Message, get_int_env, ns

ET.register_namespace("", ns["cs"])  # Required by `write_csl`

setlocale(LC_COLLATE, "zh_CN.UTF-8")  # Required by `sort_by_csl_title`

ROOT_DIR = Path(__file__).parent.parent.parent


class DebugLevel(IntEnum):
    NO_CHECK = 0
    """Skip all checks."""
    CHECK_MIN_RESULT = 1
    """Check all styles but only show results of failed styles."""
    CHECK_FULL_RESULT = 2
    """Check all styles and show all results."""
    CHECK_VERBOSE = 3
    """Check all styles and show all changes and results."""
    BACKTRACE = 4
    """Check each style after each edit."""


def parse_args(args: list[str], styles_dir: Path) -> Generator[Path, None, None]:
    """Determine CSL files to be sanitized."""
    if "all" in args or not args:
        skipped = {
            styles_dir / x
            for x in {
                # This is a set of styles that are either unfixable (e.g., using self-invented terms rather than using macros) or not worth fixing (e.g., using a feature that is not used by any other style).
                # At present, the set is empty.
            }
        }
        for f in styles_dir.glob("**/*.csl"):
            if f not in skipped:
                yield f
    else:
        yield from (Path(x) for x in args)


def sort_by_csl_title(x: IndexEntry) -> tuple[int | str, ...]:
    # An approximate implementation of zotero-chinese ordering.
    # https://github.com/zotero-chinese/website/blob/44aa0926f43fe5607b5d135fcad31449f9c5ed3a/src/.vitepress/data/styles.data.ts#L17-L29

    if x.info.title.startswith("GB/T 7714—"):
        year = int(x.info.title.removeprefix("GB/T 7714—")[:4])
        text = x.info.title.removeprefix("GB/T 7714—")[4:]
        return (0, -year, strxfrm(text))
    elif not re.match(r"[A-Z]", x.info.title[0]):
        return (1, strxfrm(x.info.title))
    else:
        return (2, strxfrm(x.info.title))


def main() -> None:
    styles_dir = ROOT_DIR / "styles"
    assert styles_dir.exists()

    dist_dir = ROOT_DIR / "dist"
    dist_dir.mkdir(exist_ok=True)

    debug_level = DebugLevel(get_int_env("DEBUG", default=DebugLevel.CHECK_FULL_RESULT))
    files = parse_args(argv[1:], styles_dir)

    index: deque[IndexEntry] = deque()
    success = True
    for csl in files:
        csl_relative = csl.resolve().relative_to(styles_dir)
        save_csl = dist_dir / csl_relative
        save_dir = save_csl.parent
        save_dir.mkdir(exist_ok=True, parents=True)

        # 1. Normalize
        style = read_csl(csl)

        if debug_level >= DebugLevel.BACKTRACE:
            if failed := check_csl(style):
                print(f"💥 {failed}")

        changes: deque[Message] = deque()
        for message in normalize_csl(style):
            changes.append(message)

            if debug_level >= DebugLevel.BACKTRACE:
                print(f"📝 {message}")
                if failed := check_csl(style):
                    print(f"💥 {failed}")
            elif debug_level >= DebugLevel.CHECK_VERBOSE:
                print(message)

        # 2. Check
        if debug_level > DebugLevel.NO_CHECK:
            failed = check_csl(style)
            if not failed:
                if debug_level >= DebugLevel.CHECK_FULL_RESULT:
                    print(f"✅ {csl_relative.as_posix()}")
            else:
                print(f"💥 {csl_relative.as_posix()}\n    {failed}")
                success = False
            if debug_level >= DebugLevel.BACKTRACE:
                # There are many lines above in backtrace mode.
                # It is helpful to add a blank line after each style.
                print("")

        # 3. Save

        # Save sanitized CSL
        write_csl(style, save_csl)

        # Save diff
        diff = HtmlDiff(wrapcolumn=50).make_file(
            csl.read_text(encoding="utf-8").splitlines(keepends=True),
            save_csl.read_text(encoding="utf-8").splitlines(keepends=True),
            "Original",
            "Sanitized",
            context=True,
        )
        (save_dir / "diff.html").write_text(diff, encoding="utf-8")

        # Create index entry
        index.append(
            IndexEntry(
                info=CslInfo.from_style(style),
                changes=changes,
                original=csl_relative,
                sanitized=save_csl,
                diff=save_dir / "diff.html",
            )
        )

    # Sort and save indices
    index_sorted = sorted(index, key=sort_by_csl_title)

    json_index = dist_dir / "index.json"
    json_index.write_text(make_json_index(index_sorted, dist_dir), encoding="utf-8")

    (dist_dir / "index.html").write_text(
        make_human_index(lang="zh", root=ROOT_DIR, json_index=json_index),
        encoding="utf-8",
    )
    (dist_dir / "index.en.html").write_text(
        make_human_index(lang="en", root=ROOT_DIR, json_index=json_index),
        encoding="utf-8",
    )

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
