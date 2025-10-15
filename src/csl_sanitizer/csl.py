"""Basic operations for CSL files.

A CSL style will be represented as a `CslStyle`, which is an alias for `ET.Element`, where `ET` is `xml.etree.ElementTree`.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from subprocess import run
from typing import Self

from .util import ns

CslStyle = ET.Element

_hayagriva_example = Path(__file__).parent / "hayagriva_example.yaml"


def read_csl(path: Path) -> CslStyle:
    tree = ET.parse(
        path, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    )
    style = tree.getroot()
    return style


def write_csl(style: CslStyle, path: Path) -> None:
    """Save a CSL style as a file.

    To make sure the saved XML does not contain `ns0:` prefixes, you have to register the default namespace globally first.

        from .util import Message, ns
        ET.register_namespace("", ns["cs"])
    """
    dumped: bytes = ET.tostring(style, encoding="utf-8", xml_declaration=True)
    path.write_bytes(dumped.replace(b" />", b"/>"))


def check_csl(csl: Path) -> str | None:
    """Checks if a CSL style is considered malformed by hayagriva.

    Returns the error message if considered malformed, and returns `None` otherwise.

    Due to the limitation of the hayagriva CLI, the CSL style has to be saved as a file (`write_csl`) first.
    """
    result = run(
        ["hayagriva", _hayagriva_example, "reference", "--csl", csl],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return None
    else:
        return result.stderr.strip().splitlines()[1]


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
