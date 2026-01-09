#import "@preview/cmarker:0.1.8": render

#let json-index = sys.inputs.at("json-index", default: "/dist/index.json")
#let lang = sys.inputs.at("lang", default: "zh")
#assert(("zh", "en").contains(lang))

#let readme-path = if lang == "zh" { "/README.md" } else { "/README.en.md" }

/// Reused strings
#let BABEL = (
  title: (
    zh: [可用于 Hayagriva 的 CSL 样式],
    en: [CSL sanitizer for Hayagriva],
  ),
  description: (
    zh: [
      将 #link("https://citationstyles.org")[Citation Style Language (CSL)]<new-tab>
      样式处理成 #link("https://github.com/typst/hayagriva")[Hayagriva]<new-tab>
      可用的文件。
    ],
    en: [
      Sanitize #link("https://citationstyles.org")[Citation Style Language (CSL)]<new-tab> files for #link("https://github.com/typst/hayagriva")[Hayagriva]<new-tab>.
    ],
  ),
)
/// One-off strings
#let babel(zh: [], en: []) = if lang == "zh" { zh } else { en }

#set document(
  title: if lang == "zh" [#BABEL.title.zh——#BABEL.title.en] else [#BABEL.title.en — #BABEL.title.zh],
  description: BABEL.description.at(lang),
)
#set text(lang: lang)

#html.style(read("indexing.css"))

// Open some links in new tabs
#show link.where(label: <new-tab>): it => html.a(href: it.dest, target: "_blank", it.body)

#show: html.main

#title({
  link("https://github.com/typst-doc-cn/csl-sanitizer/", BABEL.title.at(lang))
  html.br()
  html.small(if lang == "zh" { BABEL.title.en } else { BABEL.title.zh })
})

#babel(
  en: [*Languages: #link("./")[中文]* | *#link("./index.en.html")[English (current)]*],
  zh: [*语言版本：#link("./")[中文（当前页面）]* | *#link("./index.en.html")[English]*],
)

#html.div(id: "prelude")[
  #BABEL.description.at(lang)

  #{
    let readme-full = read(readme-path)

    let start-mark = "<!-- included by indexing.typ: start -->"
    let readme-included = readme-full.slice(
      readme-full.position(start-mark) + start-mark.len(),
      readme-full.position("<!-- included by indexing.typ: end -->"),
    )

    let base = "https://typst-doc-cn.github.io/csl-sanitizer/"

    render(readme-included, h1-level: 0, scope: (
      link: (dest, body) => if dest.starts-with(base + "#") {
        // Replace full URLs with in-page links
        link(label(dest.trim(base + "#", at: start)), body)
      } else if dest.starts-with(base) {
        link(dest, body)
      } else {
        [#link(dest, body)<new-tab>]
      },
    ))
  }
]

= #babel(
  zh: [为 Hayagriva 修改过的#html.a(href: "https://zotero-chinese.com/styles/", style: "white-space: nowrap;")[中文 CSL 样式]<new-tab>],
  en: [#html.a(href: "https://zotero-chinese.com/styles/", style: "white-space: nowrap;")[Chinese CSL styles]<new-tab> sanitized for Hayagriva],
) <style-list>

#for (id, entry) in json(json-index) {
  list.item[
    #link(id.replace("http://", "https://"))[*#entry.title*]<new-tab>

    #{
      [【]
      // Do not open sanitized_url in new tab, as Zotero may use it.
      link(entry.sanitized_url, babel(zh: [下载修改版本], en: [Download]))
      [ · ]
      [#link(entry.diff_url, babel(zh: [查看详细更改], en: [Compare]))<new-tab>]
      [】]
    }

    #if entry.changes.len() > 0 {
      html.details({
        html.summary(babel(zh: [简要更改内容], en: [Changes]))

        for change in entry.changes {
          show regex("\[[^\]]+\]"): it => html.elem("span", it, attrs: (
            data-normalize-kind: it.text.trim("[", at: start).trim("]", at: end),
          ))
          list.item(render(change))
        }
      })
    } else {
      babel(zh: [（无需更改，直接可用）], en: [(No changes required, ready to use)])
    }
  ]
}
