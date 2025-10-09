// ==UserScript==
// @name        可用于 hayagriva 的中文 CSL 样式
// @namespace   Violentmonkey Scripts
// @version     0.1.1
// @description 向 Zotero 中文社区 CSL 样式页面添加可用于 hayagriva 的 CSL 文件。
// @author      Y.D.X.
// @match       https://zotero-chinese.com/styles/*
// @grant       none
// ==/UserScript==

(async function () {
  "use strict";

  function with_base(path) {
    return new URL(path, "https://typst-doc-cn.github.io/csl-sanitizer/").href;
  }
  const NEW_ISSUE = "https://github.com/typst-doc-cn/csl-sanitizer/issues/new";

  /** @type {Record<string, { title: string, updated: string, sanitized_url: string, diff_url: string, changes: string[] }>} */
  const index = await fetch(with_base("./index.json")).then((r) => r.json());

  function annotate_info() {
    if (
      !window.location.pathname.match(/\/styles\/.+\//) ||
      document.querySelector("h3#hayagriva-version") !== null
    ) {
      // If not a style page or already annotated, skip.
      return;
    }

    const csl_id = document.querySelector(
      ".el-descriptions__table > tbody > tr:nth-child(1) > td:nth-child(2)",
    ).textContent;
    const entry = index[csl_id];

    /** @type {Element[]} */
    const elements = [document.createElement("h3")];
    elements[0].id = "hayagriva-version";
    elements[0].textContent = "可用于 typst/hayagriva 的版本";

    if (entry) {
      const p = document.createElement("p");
      p.innerHTML = [
        `<a href="${with_base(entry.sanitized_url)}">下载修改版本</a>`,
        `<a href="${with_base(entry.diff_url)}">查看详细更改</a>`,
      ].join(" · ");
      elements.push(p);

      if (entry.changes) {
        const details = document.createElement("details");
        details.innerHTML = "<summary>简要更改内容</summary><ul></ul>";
        const ul = details.querySelector("ul");
        for (const message of entry.changes) {
          const li = document.createElement("li");
          li.textContent = message; // 其中内容需要转义，故不可用`innerHTML`
          ul.appendChild(li);
        }
        elements.push(details);
      } else {
        const p = document.createElement("p");
        p.textContent = "（无需更改，直接可用）";
        elements.push(p);
      }
    } else {
      const p = document.createElement("p");
      p.innerHTML = `尚不支持此样式，可<a href="${NEW_ISSUE}">联系更新</a>。`;
    }

    for (const el of elements) {
      document.querySelector("h2#样式预览").insertAdjacentElement(
        "beforebegin",
        el,
      );
    }
  }

  function watch_page_change(fn) {
    const old_pushState = history.pushState;
    history.pushState = function (...args) {
      old_pushState.apply(history, args);
      setTimeout(() => fn(), 100);
    };

    const old_replaceState = history.replaceState;
    history.replaceState = function (...args) {
      old_replaceState.apply(history, args);
      setTimeout(() => fn(), 100);
    };

    window.addEventListener("popstate", () => {
      setTimeout(() => fn(), 100);
    });
  }

  annotate_info();
  watch_page_change(annotate_info);
})();
