# Contributing guide

First, install [hayagriva](https://github.com/typst/hayagriva) ([dev version](https://github.com/typst-community/dev-builds/)) and [pandoc](https://pandoc.org).

```shell
git submodule update --init --recursive

# Test all CSL files
uv run csl-sanitizer

# Open the index
python -m http.server -d dist
```

```shell
$ DEBUG=1 uv run csl-sanitizer styles/chinese/src/GB-T-7714—2025（征求意见稿，顺序编码，双语）/GB-T-7714—2025（征求意见稿，顺序编码，双语）.csl
Removed the localized (en) layout for bibliography. [Discard CSL-M extension]
Removed the institution in names of a macro (author). [Discard CSL-M extension]
Removed the institution in names of a macro (secondary-contributors). [Discard CSL-M extension]
Removed the institution in names of a macro (container-contributors). [Discard CSL-M extension]
Removed the term citation-range-delimiter (-). [Discard citeproc-js extension]
✅ styles/chinese/src/GB-T-7714—2025（征求意见稿，顺序编码，双语）/GB-T-7714—2025（征求意见稿，顺序编码，双语）.csl
```

You can also set `CSL_BACKTRACE=1` to check the style after each edit (and get 3× slower), or set `NO_CHECK=1` to skip all checks (and get 3× faster).
