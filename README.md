# CSL sanitizer for hayagriva——可用于 hayagriva 的 CSL 样式

Sanitize [Citation Style Language (CSL)](https://citationstyles.org) files for [hayagriva](https://github.com/typst/hayagriva).

将 [Citation Style Language (CSL)](https://citationstyles.org) 样式处理成 [hayagriva](https://github.com/typst/hayagriva) 可用的文件。

[![Check](https://github.com/typst-doc-cn/csl-sanitizer/actions/workflows/check.yaml/badge.svg)](https://github.com/typst-doc-cn/csl-sanitizer/actions/workflows/check.yaml)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Ftypst-doc-cn.github.io%2Fcsl-sanitizer%2F&label=Website)](https://typst-doc-cn.github.io/csl-sanitizer/)

**语言版本：[English](./README.en.md)** | **[中文（当前文件）](./README.md)**

<!-- included by main.py: start -->

- 删除 hayagriva 尚不支持的特性
- 替换非标准语法为等价或近似内容
- 尽量避免多余更改以保持清晰易懂

针对的 hayagriva 版本：[2025-09-27 `v0.9.1`](https://github.com/typst/hayagriva/releases/tag/v0.9.1)（[下载](https://github.com/typst-community/dev-builds/releases/tag/hayagriva-v0.9.1)），对应 typst v0.14.0。

使用方法：[查看 CSL 文件列表](https://typst-doc-cn.github.io/csl-sanitizer/#style-list)，或[安装浏览器用户脚本](https://typst-doc-cn.github.io/csl-sanitizer/main.user.js)在 [Zotero 中文社区 CSL 样式页面](https://zotero-chinese.com/styles/)搜索查看。

## 初心

由于实现方式纷繁复杂，**许多 CSL 样式超出了 [CSL 规范](https://docs.citationstyles.org/en/stable/specification.html)**，有些甚至还超出了 [CSL-M 扩展](https://citeproc-js.readthedocs.io/en/latest/csl-m/)（因为 [Zotero 允许任意扩展 CSL 变量](https://github.com/zotero-chinese/styles/discussions/598#discussioncomment-15125308)）。在 300+ [中文 CSL 样式](https://zotero-chinese.com/styles/)中，约 74% 会被 hayagriva（[Typst](https://typst.app/home) 所用实现）判为 malformed，但它们都能被 [citeproc-js](https://citeproc-js.readthedocs.io/en/latest/)（[Zotero](https://www.zotero.org/) 所用实现）接受。

然而很不幸，**[hayagriva 提供的错误信息一般并不清晰](https://github.com/typst/hayagriva/issues/405)**，导致调试异常困难。即使您[理解 hayagriva 报了什么错](https://typst-doc-cn.github.io/guide/FAQ/bib-csl.html)，通常也需删除各个`<macro>`并反复重新编译，一番二分法后，才能定位问题。

> - Failed to load CSL style (duplicate field `layout`)
> - Failed to load CSL style (data did not match any variant of untagged enum Term)
> - …

本项目希望能免除这些繁重工作，**让 CSL 样式能被 hayagriva 接受**。

不过请注意，这并不保证能完全正确地著录参考文献——[Typst 在中文支持方面还有不小差距，必要时请结合其它方案使用。](https://typst-doc-cn.github.io/clreq/#x7-bibliography)

<!-- included by main.py: end -->
