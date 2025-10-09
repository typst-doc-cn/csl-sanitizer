# CSL sanitizer for hayagriva——可用于 hayagriva 的 CSL 样式

Sanitize [Citation Style Language (CSL)](https://citationstyles.org) files for [hayagriva](https://github.com/typst/hayagriva).

将 [Citation Style Language (CSL)](https://citationstyles.org) 样式处理成 [hayagriva](https://github.com/typst/hayagriva) 可用的文件。

**Languages: [English (current)](./README.en.md)** | **[中文](./README.md)**

- Remove features that are not supported by hayagriva yet
- Replace non-standard syntaxes with equivalent or approximate ones
- Keep the change minimal and understandable

The targeted hayagriva version: [2025-09-26 `799cfdc`](https://github.com/typst/hayagriva/tree/799cfdc) ([download](https://github.com/typst-community/dev-builds/releases/tag/hayagriva-main.2025-09-26.799cfdc)).

## Motivation

Due to the diversity of implementations, **many CSL files go beyond the [CSL specification](https://docs.citationstyles.org/en/stable/specification.html)**, and some even go beyond the [CSL-M extension](https://citeproc-js.readthedocs.io/en/latest/csl-m/).
Among 300+ [Chinese CSL styles](https://zotero-chinese.com/styles/), about 74% are considered _malformed_ by hayagriva (the engine behind [Typst](https://typst.app/home)), but all of them are accepted by [citeproc-js](https://citeproc-js.readthedocs.io/en/latest/) (the engine behind [Zotero](https://www.zotero.org/)).

Unfortunately, **[hayagriva hardly provides clear error messages](https://github.com/typst/hayagriva/issues/405)**, making it very difficult to debug.
It's likely that you will have to comment out `<macro>`s and recompile bisectionally in order to locate the problem, even if you [understand what hayagriva is complaining about](https://typst-doc-cn.github.io/guide/FAQ/bib-csl.html).

> - Failed to load CSL style (duplicate field `layout`)
> - Failed to load CSL style (data did not match any variant of untagged enum Term)
> - …

This project attempts to help you with these heavy work, **letting CSL styles be accepted by hayagriva**.

However, please note that this does not mean the bibliography format will be strictly correct — [Typst still has a considerable gap in Chinese support. Please combine this with other workarounds when necessary.](https://typst-doc-cn.github.io/clreq/#x7-bibliography)
