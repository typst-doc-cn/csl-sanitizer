"""Create HTML and JSON indices of CSL styles.

The `index` variables have to be sorted before passing to this module.
"""

import json
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from subprocess import run

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


def make_human_index(index: Iterable[IndexEntry], dist_dir: Path, readme: Path) -> str:
    readme_full = readme.read_text(encoding="utf-8")
    readme_included = readme_full[
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
            readme_included,
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
