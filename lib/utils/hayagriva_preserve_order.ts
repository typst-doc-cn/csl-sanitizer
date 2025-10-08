import fs from "fs-extra";
import { XMLBuilder, XMLParser } from "fast-xml-parser";

const parser = new XMLParser({
  ignoreAttributes: false,
  preserveOrder: true,
  commentPropName: "#comment",
  trimValues: false,
});

const builder = new XMLBuilder({
  // Sync with parser options
  ignoreAttributes: false,
  preserveOrder: true,
  commentPropName: "#comment",
  // Don't set `format: true`, because we have set `trimValues: false` when parsing

  // Follow CSL conventions
  suppressEmptyNode: true,
});

type WithAttrs<T> = T & { ":@": Record<`@_${string}`, string> };

const xmlStr = fs.readFileSync("src/原子核物理评论/原子核物理评论.csl", {
  encoding: "utf-8",
});
const csl = parser.parse(xmlStr);
const style = csl[1].style as (
  | WithAttrs<{ (tag: string): any[] }>
  | { "#text": string }
  | { "#comment": any }
)[];

console.log(style);

fs.writeFileSync("tmp/b.csl", builder.build(csl), { encoding: "utf-8" });
