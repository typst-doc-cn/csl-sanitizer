# CSL sanitizer

Sanitize [Citation Style Language (CSL)](https://citationstyles.org) files for [hayagriva](https://github.com/typst/hayagriva).

- Remove features that are not supported by hayagriva yet
- Replace non-standard syntaxes with equivalent or approximate ones
- Keep the change minimal and understandable

## Motivation

Due to the diversity of implementations, **many CSL files go beyond the [CSL specification](https://docs.citationstyles.org/en/stable/specification.html)**, and some even go beyond the [CSL-M extension](https://citeproc-js.readthedocs.io/en/latest/csl-m/).
Among 300+ [Chinese CSL styles](https://zotero-chinese.com/styles/), about 74% are considered _malformed_ by hayagriva (the engine behind [Typst](https://typst.app/home)), but all of them are accepted by [citeproc-js](https://citeproc-js.readthedocs.io/en/latest/) (the engine behind [Zotero](https://www.zotero.org/)).

Unfortunately, **[hayagriva hardly provides clear error messages](https://github.com/typst/hayagriva/issues/405)**, making it very difficult to debug.
It's likely that you will have to comment out `<macro>`s and recompile bisectionally in order to locate the problem, even if you understand [what hayagriva is complaining](https://typst-doc-cn.github.io/guide/FAQ/bib-csl.html).

> - Failed to load CSL style (duplicate field `layout`)
> - Failed to load CSL style (data did not match any variant of untagged enum Term)
> - …

This project attempts to help you with these heavy work.

## Usage

```shell
git submodule update --init --recursive

# Test all CSL files
uv run main.py
```

```shell
$ DEBUG=1 uv run main.py styles/chinese/src/GB-T-7714—2025（征求意见稿，顺序编码，双语）/GB-T-7714—2025（征求意见稿，顺序编码，双语）.csl
Removed the localized (en) layout for bibliography. [Discard CSL-M extension]
Removed the institution in names of a macro (author). [Discard CSL-M extension]
Removed the institution in names of a macro (secondary-contributors). [Discard CSL-M extension]
Removed the institution in names of a macro (container-contributors). [Discard CSL-M extension]
Removed the term citation-range-delimiter (-). [Discard citeproc-js extension]
✅ styles/chinese/src/GB-T-7714—2025（征求意见稿，顺序编码，双语）/GB-T-7714—2025（征求意见稿，顺序编码，双语）.csl
$ diff original.csl tmp/a.csl 
```
