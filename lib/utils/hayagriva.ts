// import {} from '@citation-js/plugin-hayagriva'
// Could not find a declaration file for module '@citation-js/plugin-hayagriva'.

import { parse, stringify } from "@libs/xml";
import fs from "fs-extra";
import assert from "node:assert";
import { execFileSync } from "node:child_process";

type Message = string;

function normalize_style(cslFilePath: string, savePath: string): Message[] {
  const messages: Message[] = [];

  const csl = parse(fs.readFileSync(cslFilePath, { encoding: "utf-8" }));

  // https://citeproc-js.readthedocs.io/en/latest/csl-m/index.html#cs-layout-extension
  const bib_layouts = (csl.style as any).bibliography.layout as any[];
  if (bib_layouts.length > 1) {
    assert(bib_layouts.length === 2);
    assert(["en", "zh"].includes(bib_layouts[0]["@locale"]));
    bib_layouts.shift();
    messages.push(
      "Removed the localized layout for bibliography. (Discard CSL-M extension)"
    );
  }
  const cite_layouts = (csl.style as any).citation.layout as any[];
  if (cite_layouts.length > 1) {
    assert(cite_layouts.length === 2);
    assert(["en", "zh"].includes(cite_layouts[0]["@locale"]));
    cite_layouts.shift();
    messages.push(
      "Removed the localized layout for citation. (Discard CSL-M extension)"
    );
  }

  fs.writeFileSync(savePath, stringify(csl), { encoding: "utf-8" });

  return messages;
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

  const items = "good.yaml";

  const messages = normalize_style(cslFilePath, tmp_csl);

  make_bibliography(items, tmp_csl);
  return messages;
}

for (const csl of [
  "src/历史研究/历史研究.csl",
  "src/GB-T-7714—2005（著者-出版年，双语，姓名不大写，无URL）/GB-T-7714—2005（著者-出版年，双语，姓名不大写，无URL）.csl",
]) {
  try {
    test_hayagriva(csl);
  } catch (err) {
    console.error(csl, err.stderr);
  }
}
