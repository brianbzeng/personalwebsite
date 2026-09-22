import type { NoteBlock, NoteMark, NoteText } from "./notesData";

/**
 * Serialization between the typed note model and the contenteditable editor DOM.
 * The editor HTML is only ever produced here (escaped) or parsed here (typed);
 * no stored or received HTML is ever injected verbatim.
 */

const MARK_TAGS: Record<string, NoteMark> = {
  STRONG: "bold", B: "bold", EM: "italic", I: "italic",
  U: "underline", S: "strikethrough", STRIKE: "strikethrough", DEL: "strikethrough",
};
const MARK_HTML: Record<NoteMark, string> = {
  bold: "strong", italic: "em", underline: "u", strikethrough: "s",
};
const SAFE_SRC = /^(data:(image|application)\/[a-z0-9.+-]+;base64,|https:\/\/|\/)/i;

function escapeHtml(text: string) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
/** Mac-style check: a short rounded stroke centered well inside the filled circle. */
export const CHECK_MARK_SVG = '<svg viewBox="0 0 12 10" fill="none" aria-hidden="true" focusable="false"><path d="M2 5.4 4.8 8 10 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
export function safeNoteSrc(src: string) {
  return SAFE_SRC.test(src) ? src : "";
}
export function textToHtml(content: NoteText[]) {
  return content.map((part) => {
    const text = escapeHtml(part.text);
    return (part.marks ?? []).reduce((wrapped, mark) => `<${MARK_HTML[mark]}>${wrapped}</${MARK_HTML[mark]}>`, text);
  }).join("") || "<br>";
}

/** Model → editor HTML. Every text run is escaped; media sources are whitelisted. */
export function blocksToHtml(blocks: NoteBlock[]) {
  return blocks.map((block) => {
    if (block.type === "paragraph") return `<p>${textToHtml(block.content)}</p>`;
    if (block.type === "heading") return `<h2>${textToHtml(block.content)}</h2>`;
    if (block.type === "subheading") return `<h3>${textToHtml(block.content)}</h3>`;
    if (block.type === "bullets") return `<ul>${block.items.map((item) => `<li>${textToHtml(item)}</li>`).join("")}</ul>`;
    if (block.type === "numbered") return `<ol>${block.items.map((item) => `<li>${textToHtml(item)}</li>`).join("")}</ol>`;
    if (block.type === "checklist") return `<ul class="note-checklist">${block.items.map((item) =>
      `<li${item.checked ? ' class="is-checked" data-checked="true"' : ""}><span class="note-check" contenteditable="false" role="img" aria-label="${item.checked ? "Completed" : "Not completed"}">${item.checked ? CHECK_MARK_SVG : ""}</span><span class="note-check-text">${textToHtml(item.content)}</span></li>`).join("")}</ul>`;
    if (block.type === "table") return `<table><tbody>${block.rows.map((row) =>
      `<tr>${row.map((cell) => `<td>${escapeHtml(cell) || "<br>"}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
    if (block.type === "image") {
      const src = safeNoteSrc(block.src);
      return src ? `<img src="${src}"${block.alt ? ` alt="${escapeHtml(block.alt)}"` : ""} contenteditable="false">` : "";
    }
    const src = safeNoteSrc(block.src);
    return src ? `<span class="note-attachment" contenteditable="false" data-src="${src}" data-name="${escapeHtml(block.name)}">📎 ${escapeHtml(block.name)}</span>` : "";
  }).join("");
}

function inlineFromNode(node: Node, marks: NoteMark[], out: NoteText[]) {
  for (const child of Array.from(node.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) {
      const text = child.textContent ?? "";
      if (!text) continue;
      const last = out.at(-1);
      if (last && JSON.stringify(last.marks ?? []) === JSON.stringify(marks)) last.text += text;
      else out.push(marks.length ? { text, marks: [...marks] } : { text });
      continue;
    }
    if (child.nodeType !== Node.ELEMENT_NODE) continue;
    const element = child as Element;
    if (element.tagName === "BR") continue;
    if (element.classList.contains("note-check")) continue; // decorative bubble, not content
    const mark = MARK_TAGS[element.tagName];
    inlineFromNode(element, mark ? [...marks, mark] : marks, out);
  }
}
function inlineOf(node: Node): NoteText[] {
  const out: NoteText[] = [];
  inlineFromNode(node, [], out);
  return out;
}
const isBlockContainer = (element: Element) => ["UL", "OL", "TABLE", "IMG"].includes(element.tagName) || element.classList.contains("note-attachment");

function blocksFromChildren(node: Node, out: NoteBlock[]) {
  for (const child of Array.from(node.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) {
      const text = (child.textContent ?? "").trim();
      if (text) out.push({ type: "paragraph", content: [{ text: (child.textContent ?? "").replace(/\s+/g, " ") }] });
      continue;
    }
    if (child.nodeType !== Node.ELEMENT_NODE) continue;
    const element = child as Element;
    if (element.tagName === "UL" && element.classList.contains("note-checklist")) {
      const items = Array.from(element.children).map((child) => {
        const li = child as HTMLElement;
        return {
          checked: li.dataset.checked === "true" || li.classList.contains("is-checked"),
          content: inlineOf(li),
        };
      });
      if (items.length) out.push({ type: "checklist", items });
      continue;
    }
    if (element.tagName === "UL" || element.tagName === "OL") {
      const items = Array.from(element.children).map(inlineOf).filter((item) => item.length);
      if (items.length) out.push({ type: element.tagName === "UL" ? "bullets" : "numbered", items });
      continue;
    }
    if (element.tagName === "TABLE") {
      const rows = Array.from(element.querySelectorAll("tr")).map((tr) =>
        Array.from(tr.querySelectorAll("th,td")).map((cell) => (cell.textContent ?? "").trim()));
      if (rows.length) out.push({ type: "table", rows });
      continue;
    }
    if (element.tagName === "IMG") {
      const src = safeNoteSrc(element.getAttribute("src") ?? "");
      if (src) out.push({ type: "image", src, alt: element.getAttribute("alt") ?? undefined });
      continue;
    }
    if (element.classList.contains("note-attachment")) {
      const chip = element as HTMLElement;
      const src = safeNoteSrc(chip.dataset.src ?? "");
      if (src) out.push({ type: "attachment", src, name: chip.dataset.name || "Attachment" });
      continue;
    }
    if (isBlockContainer(element) || element.querySelector("ul, ol, table, img, .note-attachment")) {
      blocksFromChildren(element, out); // unwrap stray wrappers (paste, list edits)
      continue;
    }
    if (element.tagName === "H1" || element.tagName === "H2") { out.push({ type: "heading", content: inlineOf(element) }); continue; }
    if (element.tagName === "H3" || element.tagName === "H4" || element.tagName === "H5") { out.push({ type: "subheading", content: inlineOf(element) }); continue; }
    out.push({ type: "paragraph", content: inlineOf(element) });
  }
}

/** Editor DOM → model. `root` is the live contenteditable element (or parsed HTML). */
export function htmlToBlocks(root: Node): NoteBlock[] {
  const out: NoteBlock[] = [];
  blocksFromChildren(root, out);
  return out;
}
