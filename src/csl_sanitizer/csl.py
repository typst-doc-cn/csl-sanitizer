"""Basic operations for CSL files.

A CSL style will be represented as a `CslStyle`, which is an alias for `ET.Element`, where `ET` is `xml.etree.ElementTree`.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from hayagriva import check_csl as _check_csl

from .util import ns

CslStyle = ET.Element


def read_csl(path: Path) -> CslStyle:
    tree = ET.parse(
        path, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    )
    style = tree.getroot()
    return style


def load_csl(xml: str) -> CslStyle:
    return ET.fromstring(
        xml, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    )


def dump_csl(style: CslStyle) -> str:
    """Dump a CSL style as a string.

    To make sure the dumped XML does not contain `ns0:` prefixes, you have to register the default namespace globally first.

        from .util import ns
        ET.register_namespace("", ns["cs"])
    """
    dumped: str = ET.tostring(style, encoding="unicode", xml_declaration=True)
    return dumped.replace(" />", "/>")


def write_csl(style: CslStyle, path: Path) -> None:
    """Save a CSL style as a file.

    To make sure the saved XML does not contain `ns0:` prefixes, you have to register the default namespace globally first.

        from .util import ns
        ET.register_namespace("", ns["cs"])
    """
    path.write_text(dump_csl(style), encoding="utf-8")


def check_csl(style: str | CslStyle) -> str | None:
    """Checks if a CSL style is considered malformed by hayagriva.

    Returns the error message if considered malformed, and returns `None` otherwise.
    """
    if isinstance(style, str):
        csl = style
    else:
        csl = dump_csl(style)
    return _check_csl(csl)


@dataclass
class CslInfo:
    title: str
    id: str
    updated: str

    @classmethod
    def from_style(cls, style: CslStyle) -> Self:
        info = style.find("cs:info", ns)
        assert info is not None

        title = info.find("cs:title", ns)
        assert title is not None and title.text is not None

        id_ = info.find("cs:id", ns)
        assert id_ is not None and id_.text is not None

        updated = info.find("cs:updated", ns)
        assert updated is not None and updated.text is not None

        return cls(title=title.text, id=id_.text, updated=updated.text)
