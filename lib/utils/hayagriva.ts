// import {} from '@citation-js/plugin-hayagriva'
// Could not find a declaration file for module '@citation-js/plugin-hayagriva'.

import { parse, stringify, type xml_document } from "@libs/xml";
import fs from "fs-extra";
import assert from "node:assert";
import { execFileSync } from "node:child_process";

type Message = string;
type OneOrMany<T> = T[] | T;

function normalize_csl(cslFilePath: string, savePath: string): Message[] {
  const csl = parse(fs.readFileSync(cslFilePath, { encoding: "utf-8" }));

  const messages = [
    ...remove_duplicate_layouts(csl),
    ...replace_space_et_al_terms(csl),
  ];

  fs.writeFileSync(savePath, stringify(csl), { encoding: "utf-8" });

  return messages;
}

/**
 * Remove additional `<layout>` elements in `<bibliography>` and `<citation>`.
 *
 * They are specified in the CSL-M extension.
 * https://citeproc-js.readthedocs.io/en/latest/csl-m/index.html#cs-layout-extension
 */
function* remove_duplicate_layouts(
  csl: xml_document
): Generator<Message, void, void> {
  const bib_layouts = (csl.style as any).bibliography.layout as any[];
  if (bib_layouts.length > 1) {
    assert(bib_layouts.length === 2);
    assert(["en", "zh"].includes(bib_layouts[0]["@locale"]));
    bib_layouts.shift();
    yield "Removed the localized layout for bibliography. (Discard CSL-M extension)";
  }

  const cite_layouts = (csl.style as any).citation.layout as any[];
  if (cite_layouts.length > 1) {
    assert(cite_layouts.length === 2);
    assert(["en", "zh"].includes(cite_layouts[0]["@locale"]));
    cite_layouts.shift();
    yield "Removed the localized layout for citation. (Discard CSL-M extension)";
  }
}

/**
 * Replace the term `space-et-al` with `et-al`.
 *
 * This might be undocumented features of citeproc-js.
 */
function* replace_space_et_al_terms(
  csl: xml_document
): Generator<Message, void, void> {
  const locales = (csl.style as any).locale as OneOrMany<{
    terms: { term: OneOrMany<{ "@name": string }> };
  }>;

  // Replace `<term name="space-et-al">`
  for (const locale of Array.isArray(locales) ? locales : [locales]) {
    if (locale.terms) {
      const terms = Array.isArray(locale.terms.term)
        ? locale.terms.term
        : [locale.terms.term];
      for (const term of terms) {
        if (term["@name"] === "space-et-al") {
          term["@name"] = "et-al";
          yield "Replaced the term name `space-et-al` with `et-al`.";
        }
      }
    }
  }

  // Replace `<et-al term="space-et-al"/>`
  const macros = (csl.style as any).macro as Record<string, any>[];
  for (const macro of macros) {
    if (macro.names?.["et-al"]?.["@term"] === "space-et-al") {
      macro.names["et-al"]["@term"] = "et-al";
      yield "Replaced the term `space-et-al` referenced by `<et-al>` with `et-al`.";
    }
  }
}

function make_bibliography(
  itemsYamlFilePath: string,
  cslFilePath: string
): string {
  const stdout = execFileSync(
    "hayagriva",
    [itemsYamlFilePath, "reference", "--csl", cslFilePath],
    {
      // Capture stdout and stderr from child process. Overrides the
      // default behavior of streaming child stderr to the parent stderr
      stdio: "pipe",

      // Use utf8 encoding for stdio pipes
      encoding: "utf8",
    }
  );

  return stdout;
}

export function test_hayagriva(cslFilePath: string): Message[] {
  const TMP_DIR = "tmp";
  const tmp_csl = `${TMP_DIR}/a.csl`;

  fs.mkdirSync(TMP_DIR, { recursive: true });

  const items = "good.yaml";

  const messages = normalize_csl(cslFilePath, tmp_csl);

  make_bibliography(items, tmp_csl);
  return messages;
}

for (const csl of [
  "src/历史研究/历史研究.csl",
  "src/GB-T-7714—2005（著者-出版年，双语，姓名不大写，无URL）/GB-T-7714—2005（著者-出版年，双语，姓名不大写，无URL）.csl",
  // "src/food-materials-research/food-materials-research.csl",
  // "src/GB-T-7714—2015（注释，双语，全角标点）/GB-T-7714—2015（注释，双语，全角标点）.csl",
]) {
  try {
    test_hayagriva(csl);
  } catch (err) {
    console.error(csl, err.stderr ?? err);
    assert(err.stderr);
  }
}
