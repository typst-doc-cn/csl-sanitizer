# CSL sanitizer for Hayagriva——可用于 Hayagriva 的 CSL 样式

Sanitize [Citation Style Language (CSL)](https://citationstyles.org) files for [Hayagriva](https://github.com/typst/hayagriva).

将 [Citation Style Language (CSL)](https://citationstyles.org) 样式处理成 [Hayagriva](https://github.com/typst/hayagriva) 可用的文件。
[![Check](https://github.com/typst-doc-cn/csl-sanitizer/actions/workflows/check.yaml/badge.svg)](https://github.com/typst-doc-cn/csl-sanitizer/actions/workflows/check.yaml)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Ftypst-doc-cn.github.io%2Fcsl-sanitizer%2F&label=Website)](https://typst-doc-cn.github.io/csl-sanitizer/)

**Languages: [English (current)](./README.en.md)** | **[中文](./README.md)**

<!-- included by indexing.typ: start -->

- Remove features that are not supported by Hayagriva yet
- Replace non-standard syntaxes with equivalent or approximate ones
- Keep the change minimal and understandable

The targeted Hayagriva version: [2025-12-27 `a137441`](https://github.com/typst/hayagriva/tree/a137441), expected to be shipped with Typst v0.15.0.

Usage: [Go to the CSL file list](https://typst-doc-cn.github.io/csl-sanitizer/#style-list), or [install the browser user script](https://typst-doc-cn.github.io/csl-sanitizer/main.user.js) and view at [Zotero Chinese community’s CSL styles page](https://zotero-chinese.com/styles/).

## Motivation

Due to the diversity of implementations, **many CSL files go beyond the [CSL specification](https://docs.citationstyles.org/en/stable/specification.html)**, and some even go beyond the [CSL-M extension](https://citeproc-js.readthedocs.io/en/latest/csl-m/) (because [Zotero allows arbitrary extra CSL variables](https://github.com/zotero-chinese/styles/discussions/598#discussioncomment-15125308)).
Among 300+ [Chinese CSL styles](https://zotero-chinese.com/styles/), about 74% are considered _malformed_ by Hayagriva (the engine behind [Typst](https://typst.app/home)), but all of them are accepted by [citeproc-js](https://citeproc-js.readthedocs.io/en/latest/) (the engine behind [Zotero](https://www.zotero.org/)).

Unfortunately, **[Hayagriva hardly provides clear error messages](https://github.com/typst/hayagriva/issues/405)**, making it very difficult to debug.
It's likely that you will have to comment out `<macro>`s and recompile bisectionally in order to locate the problem, even if you [understand what Hayagriva is complaining about](https://typst-doc-cn.github.io/guide/FAQ/bib-csl.html).

> - Failed to load CSL style (duplicate field `layout`)
> - Failed to load CSL style (data did not match any variant of untagged enum Term)
> - …

This project attempts to help you with these heavy work, **letting CSL styles be accepted by Hayagriva**.

However, please note that this does not mean the bibliography format will be strictly correct. Details on that can be found in [Hayagriva’s support for GB/T 7714—2015](https://ydx-2147483647.github.io/hayagriva-gb-tracking/) (not available in English at present). In general, [Typst still has a considerable gap in Chinese support. Please combine this with other workarounds when necessary.](https://typst-doc-cn.github.io/clreq/#x7-bibliography)

<!-- included by indexing.typ: end -->
