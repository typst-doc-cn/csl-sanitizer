import xml.etree.ElementTree as ET
from collections.abc import Callable, Generator
from os import getenv
from pathlib import Path
from subprocess import run
from sys import argv
from typing import Final

ns: Final = {"cs": "http://purl.org/net/xbiblio/csl"}
"""The XML namespace"""

ET.register_namespace("", ns["cs"])

Message = str


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

    yield from fix_deprecated_term_unpublished(style)


def remove_duplicate_layouts(style: ET.Element) -> Generator[Message, None, None]:
    """Remove additional `<layout>` elements in `<bibliography>` and `<citation>`.

    They are specified in the CSL-M extension.
    https://citeproc-js.readthedocs.io/en/latest/csl-m/index.html#cs-layout-extension
    """
    bib = style.find("cs:bibliography", ns)
    assert bib is not None
    for layout in bib.findall("cs:layout", ns):
        if (lang := layout.get("locale")) is not None:
            bib.remove(layout)
            yield f"Removed the localized ({lang}) layout for bibliography. [Discard CSL-M extension]"
    assert len(bib.findall("cs:layout", ns)) == 1

    cite = style.find("cs:citation", ns)
    # Some styles are bibliography-only.
    if cite is not None:
        for layout in cite.findall("cs:layout", ns):
            if (lang := layout.get("locale")) is not None:
                cite.remove(layout)
                yield f"Removed the localized ({lang}) layout for citation. [Discard CSL-M extension]"
        assert len(cite.findall("cs:layout", ns)) == 1


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
        terms = locale.find("./cs:terms", ns)
        assert terms is not None
        term = terms.find("./cs:term[@name='citation-range-delimiter']", ns)
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
        terms = locale.find("./cs:terms", ns)
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
                yield f"Replaced the term `{term}` referenced by `<et-al>` with `{repl}` ({et_al.text})."

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


def main() -> None:
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)

    debug = bool(getenv("DEBUG"))

    if argv[1:]:
        files = argv[1:]
        skipped = {}
    else:
        skipped = {
            Path(x)
            for x in {
                # Self-invented terms and variables—They should be implemented as macros
                "src/化学进展/化学进展.csl",  # term `thesis-en`
                "src/环境昆虫学报/环境昆虫学报.csl",  # term `in-en`
                "src/四川大学-外国语学院（本科）/四川大学-外国语学院（本科）.csl",  # term `no-date`, variable `locale`
                "src/华东理工大学-社会与公共管理学院/华东理工大学-社会与公共管理学院.csl",  # variable `nationality`
                "src/数量经济技术经济研究/数量经济技术经济研究.csl",  # variable `container-title-zh`
                # The nonstandard type `monograph`
                "src/扬州大学/扬州大学.csl",
                "src/贵州大学/贵州大学.csl",
                "src/山东农业大学/山东农业大学.csl",
                # Other situations
                "src/人民出版社学术著作引证注释格式（修正版）/人民出版社学术著作引证注释格式（修正版） .csl",  # `<name name-as-sort-order="last">`
                "src/国际政治研究/国际政治研究.csl",  # `<date>` in `<terms>`
            }
        }
        if debug:
            files = [
                "src/历史研究/历史研究.csl",
                "src/中国政法大学/中国政法大学.csl",
                "src/GB-T-7714—2015（顺序编码，双语，姓名不大写，无URL、DOI）/GB-T-7714—2015（顺序编码，双语，姓名不大写，无URL、DOI）.csl",
                "src/GB-T-7714—2005（著者-出版年，双语，姓名不大写，无URL）/GB-T-7714—2005（著者-出版年，双语，姓名不大写，无URL）.csl",
                "src/food-materials-research/food-materials-research.csl",
                "src/GB-T-7714—2015（注释，双语，全角标点）/GB-T-7714—2015（注释，双语，全角标点）.csl",
                "src/中国人民大学/中国人民大学.csl",
                "src/原子核物理评论/原子核物理评论.csl",
                "src/信息安全学报/信息安全学报.csl",
                # "src/导出刊名/导出刊名.csl",
            ]
        else:
            files = Path("src").glob("**/*.csl")

    for csl in files:
        if csl in skipped:
            continue

        tree = ET.parse(
            Path(csl), parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        )
        style = tree.getroot()

        for message in normalize_csl(style):
            if debug:
                print(message)

        dumped: bytes = ET.tostring(style, encoding="utf-8", xml_declaration=True)
        (tmp_dir / "a.csl").write_bytes(dumped.replace(b" />", b"/>"))

        result = run(
            ["hayagriva", "good.yaml", "reference", "--csl", (tmp_dir / "a.csl")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"✅ {csl}")
        else:
            print(f"💥 {csl}", result.stderr, sep="")


if __name__ == "__main__":
    main()
