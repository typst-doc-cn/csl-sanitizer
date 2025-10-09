# CSL sanitizer for hayagriva——可用于 hayagriva 的 CSL 样式

Sanitize [Citation Style Language (CSL)](https://citationstyles.org) files for [hayagriva](https://github.com/typst/hayagriva).

将 [Citation Style Language (CSL)](https://citationstyles.org) 样式处理成 [hayagriva](https://github.com/typst/hayagriva) 可用的文件。

**语言版本：[English](./README.en.md)** | **[中文（当前文件）](./README.md)**

<!-- included by main.py: start -->

- 删除 hayagriva 尚不支持的特性
- 替换非标准语法为等价或近似内容
- 尽量避免多余更改以保持清晰易懂

## 初心

由于实现方式纷繁复杂，**许多 CSL 样式超出了 [CSL 规范](https://docs.citationstyles.org/en/stable/specification.html)**，有些甚至还超出了 [CSL-M 扩展](https://citeproc-js.readthedocs.io/en/latest/csl-m/)。在 300+ [中文 CSL 样式](https://zotero-chinese.com/styles/)中，约 74% 会被 hayagriva（[Typst](https://typst.app/home) 所用实现）判为 malformed，但它们都能被 [citeproc-js](https://citeproc-js.readthedocs.io/en/latest/)（[Zotero](https://www.zotero.org/) 所用实现）接受。

然而很不幸，**[hayagriva 提供的错误信息一般并不清晰](https://github.com/typst/hayagriva/issues/405)**，导致调试异常困难。即使您[理解 hayagriva 报了什么错](https://typst-doc-cn.github.io/guide/FAQ/bib-csl.html)，通常也需删除各个`<macro>`并反复重新编译，一番二分法后，才能定位问题。

> - Failed to load CSL style (duplicate field `layout`)
> - Failed to load CSL style (data did not match any variant of untagged enum Term)
> - …

本项目希望能免除这些繁重工作，**让 CSL 样式能被 hayagriva 接受**。

不过请注意，这并不保证能完全正确地著录参考文献——[Typst 在中文支持方面还有不小差距，必要时请结合其它方案使用。](https://typst-doc-cn.github.io/clreq/#x7-bibliography)

<!-- included by main.py: end -->
