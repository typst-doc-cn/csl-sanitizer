# Contributing guide

First, install [uv](https://docs.astral.sh/uv/#installation) and [typst](https://typst.app/open-source/#download).

```shell
git submodule update --init --recursive
export UV_FROZEN=1

# Test all CSL files
uv run csl-sanitizer

# Open the index
python -m http.server -d dist
```

> [!NOTE]
>
> **Why [`UV_FROZEN=1`](https://docs.astral.sh/uv/reference/environment/#uv_frozen)?**
>
> This project uses [hayagriva pre-compiled as a Python package](https://github.com/YDX-2147483647/hayagriva-gb-tracking/releases). At present, the binaries are published only to GitHub Releases, and GitHub sets `cache-control: no-cache`. Therefore, `uv run` without frozen always spends several seconds fetching the URLs to check if `uv.lock` needs to be updated.
>
> By setting `UV_FROZEN=1` (or running `uv run --frozen`), we skip this time-consuming yet unnecessary check.

```shell
$ DEBUG=3 uv run csl-sanitizer styles/chinese/src/GB-T-7714—2025（顺序编码，双语）/GB-T-7714—2025（顺序编码，双语）.csl
Removed the term citation-range-delimiter (-). [Discard citeproc-js extension]
Removed a reference to the variable `CSTR` in a macro (entry-type-id). [Discard zotero-chinese convention]
Removed a reference to the variable `CSTR` in a macro (publisher). [Discard zotero-chinese convention]
Removed a reference to the variable `CSTR` and its wrapping tags in a macro (access). [Discard zotero-chinese convention]
Removed a reference to the variable `CSTR` in a macro (entry-layout). [Discard zotero-chinese convention]
Removed the localized (en) layout for bibliography. [Discard CSL-M extension]
✅ chinese/src/GB-T-7714—2025（顺序编码，双语）/GB-T-7714—2025（顺序编码，双语）.csl
```

You can also set `DEBUG=4` to check the style after each edit, or set `DEBUG=0` to skip all checks. See [`DebugLevel` in `main.py`](./src/csl_sanitizer/main.py) for details.
