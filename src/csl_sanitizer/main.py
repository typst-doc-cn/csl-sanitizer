import json
import re
import xml.etree.ElementTree as ET
from collections import deque
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from difflib import HtmlDiff
from locale import LC_COLLATE, setlocale, strxfrm
from os import getenv
from pathlib import Path
from subprocess import run
from sys import argv
from typing import Final, Self

ns: Final = {"cs": "http://purl.org/net/xbiblio/csl"}
"""The XML namespace"""

ET.register_namespace("", ns["cs"])

setlocale(LC_COLLATE, "zh_CN.UTF-8")  # Required by `sort_by_csl_title`

Message = str


ROOT_DIR = Path(__file__).parent.parent.parent


def normalize_csl(style: ET.Element) -> Generator[Message, None, None]:
    """Normalize `<style>` in a CSL in place."""
    # For common to uncommon

    yield from remove_duplicate_layouts(style)

    yield from replace_nonstandard_original_variables(style)

    yield from remove_institution_in_names(style)

    yield from remove_citation_range_delimiter_terms(style)
    yield from replace_space_et_al_terms(style)
    yield from replace_localized_et_al_terms(style)
    yield from remove_large_long_ordinal_terms(style)

    yield from drop_empty_else_branches(style)
    yield from drop_empty_groups(style)
    yield from fill_empty_layouts(style)

    yield from drop_empty_text_case_attrs(style)
    yield from fix_deprecated_term_unpublished(style)
    yield from lowercase_locator_attrs(style)


def remove_duplicate_layouts(style: ET.Element) -> Generator[Message, None, None]:
    """Remove additional `<layout>` elements in `<bibliography>` and `<citation>`.

    They are specified in the CSL-M extension.
    https://citeproc-js.readthedocs.io/en/latest/csl-m/index.html#cs-layout-extension
    """
    for tag in ["bibliography", "citation"]:
        elem = style.find(f"cs:{tag}", ns)
        assert elem is not None
        for layout in elem.findall("cs:layout", ns):
            if (lang := layout.get("locale")) is not None:
                elem.remove(layout)
                yield f"Removed the localized ({lang}) layout for {tag}. [Discard CSL-M extension]"
        assert len(elem.findall("cs:layout", ns)) == 1


def remove_citation_range_delimiter_terms(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Remove `<term name="citation-range-delimiter">`.

    This is an undocumented feature of citeproc-js.
    https://github.com/zotero-chinese/styles/discussions/439
    """
    for locale in style.findall(
        ".//cs:term[@name='citation-range-delimiter']/../..", ns
    ):
        terms = locale.find("cs:terms", ns)
        assert terms is not None
        # There is at most one such `<term>`, so we use `find` instead of `findall`.
        term = terms.find("cs:term[@name='citation-range-delimiter']", ns)
        assert term is not None

        terms.remove(term)
        if len(terms) == 0:
            locale.remove(terms)
            # For simplicity, keep the `<locale>` even if it might become empty now.
            yield f"Removed the term citation-range-delimiter ({term.text}) and its wrapping tag. [Discard citeproc-js extension]"
        else:
            yield f"Removed the term citation-range-delimiter ({term.text}). [Discard citeproc-js extension]"


def remove_large_long_ordinal_terms(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Remove `<term name="long-ordinal-{n}">` where n > 10.

    This might be an undocumented feature of citeproc-js.
    https://docs.citationstyles.org/en/stable/specification.html#long-ordinals
    """
    for locale in style.findall(".//cs:term[@name]/../..", ns):
        terms = locale.find("cs:terms", ns)
        assert terms is not None

        for term in terms.findall("./cs:term[@name]", ns):
            if (name := term.get("name")) in ["long-ordinal-11", "long-ordinal-12"]:
                terms.remove(term)
                if len(terms) == 0:
                    locale.remove(terms)
                    # For simplicity, keep the `<locale>` even if it might become empty now.
                    yield f"Removed the term {name} ({term.text}) and its wrapping tag."
                else:
                    yield f"Removed the term {name} ({term.text})."


def _replace_et_al(
    matches: list[str], repl: str
) -> Callable[[ET.Element], Generator[Message, None, None]]:
    def impl(style: ET.Element) -> Generator[Message, None, None]:
        for term in style.findall(".//cs:term[@name]", ns):
            if (name := term.get("name")) in matches:
                term.set("name", repl)
                yield f"Replaced the term name `{name}` with `{repl}` ({term.text})."

        for et_al in style.findall(".//cs:et-al[@term]", ns):
            if (term := et_al.get("term")) in matches:
                et_al.set("term", repl)
                yield f"Replaced the term `{term}` referenced by `<et-al>` with `{repl}`."

    return impl


replace_space_et_al_terms = _replace_et_al(["space-et-al"], "et-al")
"""Replace the term `space-et-al` with `et-al`.

This might be undocumented features of citeproc-js.
"""

replace_localized_et_al_terms = _replace_et_al(
    ["en-et-al", "zh-et-al", "et-al-zh"], "et-al"
)
"""Replace the localized term `{en,zh}-et-al`/`et-al-zh` with `et-al`.

This might be undocumented features of citeproc-js.
https://github.com/zotero-chinese/styles/pull/518
"""


def remove_institution_in_names(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Remove `<institution>` in `<names>`.

    This is specified in the CSL-M extension.
    https://citeproc-js.readthedocs.io/en/latest/csl-m/index.html#cs-institution-and-friends-extension
    """
    for macro in style.findall("cs:macro", ns):
        for names in macro.findall(".//cs:institution/..", ns):
            institution = names.find("./cs:institution", ns)
            assert institution is not None

            names.remove(institution)
            yield f"Removed the institution in names of a macro ({macro.get('name')}). [Discard CSL-M extension]"


def replace_nonstandard_original_variables(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Replace non-standard `original-*` variables like `original-container-title` with un-original ones.

    They might be undocumented features of citeproc-js.
    https://github.com/zotero-chinese/styles/pull/518
    """
    for macro in style.findall("cs:macro", ns):
        for ref in macro.findall(".//*[@variable]", ns):
            raw = ref.get("variable")
            assert raw is not None

            # `<if variable="…" match="…">` might contain multiple variables
            variables = raw.split()
            for i in range(len(variables)):
                v = variables[i]
                if v in [
                    "original-container-title",
                    "original-container-title-short",
                    "original-genre",
                    "original-event-title",
                    "original-event-place",
                    "original-editor",
                    "original-status",
                    "original-issue",
                    "original-jurisdiction",
                ]:
                    repl = v.removeprefix("original-")
                    variables[i] = repl
                    yield f"Replaced the variable `{v}` with `{repl}` in a macro ({macro.get('name')})."
            ref.set("variable", " ".join(variables))


def fix_deprecated_term_unpublished(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Fix the deprecated term `unpublished` with the value `Unpublished`.

    This is specified in the CSL-M extension, but deprecated.
    https://citeproc-js.readthedocs.io/en/latest/csl-m/index.html#unpublished-extension
    """
    for macro in style.findall("cs:macro", ns):
        for text in macro.findall(".//cs:text[@term='unpublished']", ns):
            del text.attrib["term"]
            text.set("value", "Unpublished")

            yield f"Fix the deprecated term `unpublished` with the value `Unpublished` in a macro ({macro.get('name')}). [Fix CSL-M deprecated extension]"


def drop_empty_text_case_attrs(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Drop empty `text-case` attributes.

    Follow the CSL specification strictly.
    https://docs.citationstyles.org/en/stable/specification.html#text-case
    """
    for macro in style.findall("cs:macro", ns):
        for elem in macro.findall(".//*[@text-case='']", ns):
            del elem.attrib["text-case"]

            yield f"Dropped the empty text-case attribute in a macro ({macro.get('name')}). [Follow CSL spec]"


def drop_empty_else_branches(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Drop empty `<else>` branches.

    Follow the CSL specification strictly.
    > As an empty `cs:else` element would be superfluous, `cs:else` must contain at least one rendering element.
    https://docs.citationstyles.org/en/stable/specification.html#choose
    """
    for macro in style.findall("cs:macro", ns):
        for choose in macro.findall(".//cs:else/..", ns):
            for else_branch in choose.findall("cs:else", ns):
                if all(child.tag is ET.Comment for child in else_branch):
                    # If it has no child or has only comments
                    choose.remove(else_branch)
                    yield f"Dropped the empty `<else>` branch in a macro ({macro.get('name')}). [Follow CSL spec]"


def drop_empty_groups(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Drop empty `<group>` elements.

    Follow the CSL specification strictly.
    > The `cs:group` rendering element must contain one or more rendering elements (with the exception of `cs:layout`).
    https://docs.citationstyles.org/en/stable/specification.html#choose
    """
    for macro in style.findall("cs:macro", ns):
        for parent in macro.findall(".//cs:group/..", ns):
            for group in parent.findall("cs:group", ns):
                if all(child.tag is ET.Comment for child in group):
                    # If it has no child or has only comments
                    parent.remove(group)
                    yield f"Dropped an empty `<group>` in a macro ({macro.get('name')}). [Follow CSL spec]"


def fill_empty_layouts(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Fill empty `<layout>` elements with empty `<text>` elements.

    Follow the CSL specification strictly.
    > The `cs:layout` rendering element is a required child element of `cs:citation` and `cs:bibliography`.
    > It must contain one or more of the other rendering elements described below…
    https://docs.citationstyles.org/en/stable/specification.html#layout-1
    """
    for tag in ["bibliography", "citation"]:
        elem = style.find(f"cs:{tag}", ns)
        assert elem is not None
        for layout in elem.findall("cs:layout", ns):
            if len(layout) == 0:
                ET.SubElement(layout, "text", {"value": ""})
                yield f"Fill the empty `<layout>` with an empty `<text>` for {tag}. [Follow CSL spec]"


def lowercase_locator_attrs(
    style: ET.Element,
) -> Generator[Message, None, None]:
    """Convert locator attributes to lowercase.

    Follow the CSL specification strictly.
    https://docs.citationstyles.org/en/stable/specification.html#locators
    """
    for macro in style.findall("cs:macro", ns):
        for elem in macro.findall(".//*[@locator]", ns):
            if (locator := elem.get("locator")) and locator != locator.lower():
                elem.set("locator", locator.lower())

                yield f"Lowercased the locator attribute ({locator} -> {locator.lower()}) in a macro ({macro.get('name')}). [Follow CSL spec]"


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
                "chinese/src/华东理工大学-社会与公共管理学院/华东理工大学-社会与公共管理学院.csl",  # variable `nationality`
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


@dataclass
class CslInfo:
    title: str
    id: str
    updated: str

    @classmethod
    def from_style(cls, style: ET.Element) -> Self:
        info = style.find("cs:info", ns)
        assert info is not None

        title = info.find("cs:title", ns)
        assert title is not None and title.text is not None

        id_ = info.find("cs:id", ns)
        assert id_ is not None and id_.text is not None

        updated = info.find("cs:updated", ns)
        assert updated is not None and updated.text is not None

        return cls(title=title.text, id=id_.text, updated=updated.text)


@dataclass
class IndexEntry:
    info: CslInfo
    sanitized: Path
    original: Path
    diff: Path
    """Path to side by side comparison with change highlights."""
    changes: Iterable[str]
    """Brief descriptions of the changes."""


def make_human_index(index: Iterable[IndexEntry], dist_dir: Path) -> str:
    readme_full = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    readme = readme_full[
        slice(
            readme_full.find("<!-- included by main.py: start -->"),
            readme_full.find("<!-- included by main.py: end -->"),
        )
    ]

    lines = deque(
        [
            """---
title: 可用于 hayagriva 的 CSL 样式
lang: zh
header-includes: |
    <style>
    a, a:visited {
        color: rgb(52, 81, 178);
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    code {
        margin-inline: 0.25em;
    }
    p {
        line-height: 1.5em;
    }
    li > p {
        margin-block: 0.5em;
    }
    li {
        margin-block: 1.5em;
    }
    li li {
        margin-block: 0.5em;
    }

    /* Special style for the README */
    ul:first-of-type > li {
        margin-block: 0.5em;
    }
    </style>
---""",
            "将 [Citation Style Language (CSL)](https://citationstyles.org) 样式处理成 [hayagriva](https://github.com/typst/hayagriva) 可用的文件。",
            readme,
            "## 为 hayagriva 修改过的[中文 CSL 样式](https://zotero-chinese.com/styles/) {#style-list}",
        ]
    )

    for entry in index:
        lines.extend(
            [
                f"- **[{entry.info.title}]({entry.info.id.replace('http://', 'https://')})**",
                "  【"
                f"[下载修改版本](./{entry.sanitized.relative_to(dist_dir).as_posix()}) · "
                f"[查看详细更改](./{entry.diff.relative_to(dist_dir).as_posix()})"
                "】",
                "  <details><summary>简要更改内容</summary>\n\n"
                f"{'\n'.join(f'  - {change}' for change in entry.changes)}\n\n"
                "  </details>"
                if entry.changes
                else "  （无需更改，直接可用）",
            ]
        )

    return run(
        [
            "pandoc",
            "--from=gfm+attributes",
            "--to=html",
            "--standalone",
        ],
        text=True,
        capture_output=True,
        check=True,
        input="\n\n".join(lines),
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

    debug = bool(getenv("DEBUG"))
    files = parse_args(argv[1:], debug, styles_dir)

    index: deque[IndexEntry] = deque()
    success = True
    for csl in files:
        csl_relative = csl.resolve().relative_to(styles_dir)

        # 1. Normalize

        tree = ET.parse(
            csl, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        )
        style = tree.getroot()

        changes: deque[Message] = deque()
        for message in normalize_csl(style):
            changes.append(message)
            if debug:
                print(message)

        # 2. Save

        save_csl = dist_dir / csl_relative
        save_dir = save_csl.parent
        save_dir.mkdir(exist_ok=True, parents=True)

        # Save sanitized CSL
        dumped: bytes = ET.tostring(style, encoding="utf-8", xml_declaration=True)
        save_csl.write_bytes(dumped.replace(b" />", b"/>"))

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

        result = run(
            ["hayagriva", ROOT_DIR / "good.yaml", "reference", "--csl", save_csl],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"✅ {csl_relative}")
        else:
            print(f"💥 {csl_relative}", result.stderr, sep="")
            success = False

    # Sort and save indices
    index_sorted = sorted(index, key=sort_by_csl_title)
    (dist_dir / "index.html").write_text(
        make_human_index(index_sorted, dist_dir), encoding="utf-8"
    )
    (dist_dir / "index.json").write_text(
        make_json_index(index_sorted, dist_dir), encoding="utf-8"
    )

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
