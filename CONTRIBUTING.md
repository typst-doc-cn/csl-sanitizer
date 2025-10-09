# Contributing guide

First, install [hayagriva](https://github.com/typst/hayagriva) ([dev version](https://github.com/typst-community/dev-builds/)) and [pandoc](https://pandoc.org).

```shell
git submodule update --init --recursive

# Test all CSL files
uv run main.py

# Open the index
python -m http.server -d dist
```

```shell
$ DEBUG=1 uv run main.py styles/chinese/src/GB-T-7714—2025（征求意见稿，顺序编码，双语）/GB-T-7714—2025（征求意见稿，顺序编码，双语）.csl
Removed the localized (en) layout for bibliography. [Discard CSL-M extension]
Removed the institution in names of a macro (author). [Discard CSL-M extension]
Removed the institution in names of a macro (secondary-contributors). [Discard CSL-M extension]
Removed the institution in names of a macro (container-contributors). [Discard CSL-M extension]
Removed the term citation-range-delimiter (-). [Discard citeproc-js extension]
✅ styles/chinese/src/GB-T-7714—2025（征求意见稿，顺序编码，双语）/GB-T-7714—2025（征求意见稿，顺序编码，双语）.csl
```
