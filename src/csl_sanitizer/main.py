import re
import xml.etree.ElementTree as ET
from collections import deque
from collections.abc import Generator
from difflib import HtmlDiff
from locale import LC_COLLATE, setlocale, strxfrm
from pathlib import Path
from sys import argv

from .csl import check_csl, read_csl, write_csl
from .indexing import CslInfo, IndexEntry, make_human_index, make_json_index
from .normalize import normalize_csl
from .util import Message, get_bool_env, ns

ET.register_namespace("", ns["cs"])  # Required by `write_csl`

setlocale(LC_COLLATE, "zh_CN.UTF-8")  # Required by `sort_by_csl_title`

ROOT_DIR = Path(__file__).parent.parent.parent


def parse_args(
    args: list[str], debug: bool, styles_dir: Path
) -> Generator[Path, None, None]:
    """Determine CSL files to be sanitized."""
    if "all" in args or (not args and not debug):
        skipped = {
            styles_dir / x
            for x in {
                # Self-invented terms and variables—They should be implemented as macros
                "chinese/src/化学进展/化学进展.csl",  # term `thesis-en`
                "chinese/src/环境昆虫学报/环境昆虫学报.csl",  # term `in-en`
                "chinese/src/四川大学-外国语学院（本科）/四川大学-外国语学院（本科）.csl",  # term `no-date`, variable `locale`
                "chinese/src/数量经济技术经济研究/数量经济技术经济研究.csl",  # variable `container-title-zh`
                # The nonstandard type `monograph`
                "chinese/src/扬州大学/扬州大学.csl",
                "chinese/src/贵州大学/贵州大学.csl",
                "chinese/src/山东农业大学/山东农业大学.csl",
                # Other situations
                "chinese/src/人民出版社学术著作引证注释格式（修正版）/人民出版社学术著作引证注释格式（修正版） .csl",  # `<name name-as-sort-order="last">`
                "chinese/src/国际政治研究/国际政治研究.csl",  # `<date>` in `<terms>`
            }
        }
        for f in styles_dir.glob("**/*.csl"):
            if f not in skipped:
                yield f
    else:
        if args:
            yield from (Path(x) for x in args)
        else:
            yield from (
                styles_dir / x
                for x in [
                    "chinese/src/历史研究/历史研究.csl",
                    "chinese/src/中国政法大学/中国政法大学.csl",
                    "chinese/src/GB-T-7714—2015（顺序编码，双语，姓名不大写，无URL、DOI）/GB-T-7714—2015（顺序编码，双语，姓名不大写，无URL、DOI）.csl",
                    "chinese/src/GB-T-7714—2005（著者-出版年，双语，姓名不大写，无URL）/GB-T-7714—2005（著者-出版年，双语，姓名不大写，无URL）.csl",
                    "chinese/src/food-materials-research/food-materials-research.csl",
                    "chinese/src/GB-T-7714—2015（注释，双语，全角标点）/GB-T-7714—2015（注释，双语，全角标点）.csl",
                    "chinese/src/中国人民大学/中国人民大学.csl",
                    "chinese/src/原子核物理评论/原子核物理评论.csl",
                    "chinese/src/信息安全学报/信息安全学报.csl",
                    "chinese/src/导出刊名/导出刊名.csl",
                ]
            )


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

    debug = get_bool_env("DEBUG")
    csl_backtrace = get_bool_env("CSL_BACKTRACE")
    no_check = get_bool_env("NO_CHECK")
    assert not (csl_backtrace and no_check), (
        "CSL_BACKTRACE and NO_CHECK cannot be enabled at the same time"
    )

    files = parse_args(argv[1:], debug, styles_dir)

    index: deque[IndexEntry] = deque()
    success = True
    for csl in files:
        csl_relative = csl.resolve().relative_to(styles_dir)
        save_csl = dist_dir / csl_relative
        save_dir = save_csl.parent
        save_dir.mkdir(exist_ok=True, parents=True)

        # 1. Normalize
        style = read_csl(csl)

        if csl_backtrace:
            if failed := check_csl(csl):
                print(f"💥 {failed}")

        changes: deque[Message] = deque()
        for message in normalize_csl(style):
            changes.append(message)

            if csl_backtrace:
                print(f"📝 {message}")
                write_csl(style, save_csl)
                if failed := check_csl(save_csl):
                    print(f"💥 {failed}")
            elif debug:
                print(message)

        # 2. Save

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
                original=csl,
                sanitized=save_csl,
                diff=save_dir / "diff.html",
            )
        )

        # 3. Check
        if not no_check:
            failed = check_csl(save_csl)
            if not failed:
                print(f"✅ {csl_relative}")
            else:
                print(f"💥 {csl_relative}\n    {failed}")
                success = False
            if csl_backtrace:
                # There are many lines above in backtrace mode.
                # It is helpful to add a blank line after each style.
                print("")

    # Sort and save indices
    index_sorted = sorted(index, key=sort_by_csl_title)
    (dist_dir / "index.html").write_text(
        make_human_index(index_sorted, dist_dir, ROOT_DIR / "README.md"),
        encoding="utf-8",
    )
    (dist_dir / "index.json").write_text(
        make_json_index(index_sorted, dist_dir), encoding="utf-8"
    )

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
