import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import * as notesData from "../app/components/notesData.ts";
import * as desktopState from "../app/components/desktopState.ts";
import * as noteEditor from "../app/components/noteEditor.ts";
import * as localNotes from "../app/components/localNotes.ts";
const { BOARD_NOTES, filterBoardNotes, findBoardNote, groupBoardNotes, noteDateLabel, noteListDate, notePlainText, noteSharePath } = notesData;
const { blocksToHtml, safeNoteSrc } = noteEditor;
const { freshLocalNotes, mergeBoardInto, loadLocalNotes, saveLocalNotes, NOTES_STORAGE_KEY, isLocalNoteId, ATTACHMENT_LIMIT_BYTES } = localNotes;
import { desktopWindowReducer as reduce, INITIAL_DESKTOP_SESSION, managedWindowTitle } from "../app/components/desktopWindowManager.ts";

const source = (file) => readFileSync(new URL(`../app/components/${file}`, import.meta.url), "utf8");
const richNote = { id: "formatting", title: "Formatting", blocks: [
  { type: "heading", content: [{ text: "Heading" }] },
  { type: "subheading", content: [{ text: "Subheading" }] },
  { type: "paragraph", content: [{ text: "All four", marks: ["bold", "italic", "underline", "strikethrough"] }, { text: " <script>alert(1)</script>" }] },
  { type: "bullets", items: [[{ text: "Bullet" }]] },
  { type: "numbered", items: [[{ text: "Numbered" }]] },
  { type: "checklist", items: [{ checked: true, content: [{ text: "Done" }] }, { checked: false, content: [{ text: "To do" }] }] },
] };

test("published board contains Brian's supplied note, stable unique IDs, and no invented entries", () => {
  assert.equal(BOARD_NOTES.length, 1);
  assert.equal(BOARD_NOTES[0].title, "to do:");
  assert.equal(notePlainText(BOARD_NOTES[0]), "JS debugging through console and devtools\nVersion control & VCS hosting\nData structures & algorithms\nSystem design\nPerformance/Latency\nCache control\nScaling databases");
  const checked = BOARD_NOTES[0].blocks[0].items.map((item) => item.checked);
  assert.deepEqual(checked, [true, true, true, true, true, true, false]);
  assert.equal(new Set(BOARD_NOTES.map((note) => note.id)).size, BOARD_NOTES.length);
  assert.equal(findBoardNote("to-do"), BOARD_NOTES[0]);
  assert.equal(findBoardNote("unknown"), undefined);
});

test("multiple notes can be selected and searched by title or rich text body", () => {
  const notes = [...BOARD_NOTES, richNote];
  assert.equal(findBoardNote("formatting", notes), richNote);
  assert.deepEqual(filterBoardNotes("  SCALING databases ", notes), [BOARD_NOTES[0]]);
  assert.deepEqual(filterBoardNotes("All four", notes), [richNote]);
  assert.deepEqual(filterBoardNotes("Formatting", notes), [richNote]);
  assert.deepEqual(filterBoardNotes(" ", notes), notes);
  assert.deepEqual(filterBoardNotes("nonexistent", notes), []);
});

test("formatted note text remains searchable without leaking markup into previews", () => {
  assert.equal(notePlainText(richNote), "Heading\nSubheading\nAll four <script>alert(1)</script>\nBullet\nNumbered\nDone\nTo do");
  const mediaNote = { id: "media", title: "Media", blocks: [
    { type: "table", rows: [["a", "b"], ["c", "d"]] },
    { type: "image", src: "data:image/png;base64,AAAA", alt: "Chart" },
    { type: "attachment", src: "data:application/pdf;base64,BBBB", name: "Resume.pdf" },
  ] };
  assert.equal(notePlainText(mediaNote), "a b\nc d\nImage — Chart\nResume.pdf");
});

test("Notes groups actual edit dates in Pacific time without mutating published order", () => {
  const make = (id, updatedAt) => ({ id, title: id, blocks: [], updatedAt });
  const notes = [make("old", "2025-07-01T12:00:00-07:00"), make("undated"), make("yesterday", "2026-09-04T23:59:00-07:00"), make("today", "2026-09-05T00:01:00-07:00"), make("recent", "2026-08-19T12:00:00-07:00"), make("july", "2026-07-13T12:00:00-07:00"), make("invalid", "not a date")];
  const before = [...notes];
  const now = new Date("2026-09-05T12:00:00-07:00");
  assert.deepEqual(groupBoardNotes(notes, now).map(({ label, items }) => [label, items.map((note) => note.id)]), [
    ["Today", ["today"]], ["Yesterday", ["yesterday"]], ["Previous 30 Days", ["recent"]], ["July", ["july"]], ["July 2025", ["old"]], ["Notes", ["undated", "invalid"]],
  ]);
  assert.deepEqual(notes, before);
  assert.equal(noteListDate(notes[3], now), "12:01 AM");
  assert.equal(noteListDate(notes[2], now), "9/4/26");
  assert.match(noteDateLabel(notes[3]), /September 5, 2026 at 12:01 AM/);
  assert.equal(noteDateLabel(notes[6]), "");
  assert.equal(noteListDate(notes[1], now), "");
});

test("Notes date headings use calendar days across DST and Pacific midnight", () => {
  for (const [edited, now] of [
    ["2026-03-07T23:45:00-08:00", "2026-03-08T23:15:00-07:00"],
    ["2026-11-01T00:15:00-07:00", "2026-11-02T00:15:00-08:00"],
    ["2026-09-06T06:59:00Z", "2026-09-06T07:01:00Z"],
  ]) {
    assert.equal(groupBoardNotes([{ id: "test", title: "test", blocks: [], updatedAt: edited }], new Date(now))[0].label, "Yesterday");
  }
});

test("Notes renders combined text styles, semantic lists and interactive checklists safely", () => {
  const { outputText } = ts.transpileModule(source("NoteContent.tsx"), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 } });
  const module = { exports: {} };
  new Function("require", "module", "exports", outputText)((id) => id === "./noteEditor" ? noteEditor : id.endsWith(".css") ? {} : createRequire(import.meta.url)(id), module, module.exports);
  const html = renderToStaticMarkup(createElement(module.exports.default, { note: richNote }));
  assert.match(html, /<s><span class="note-underline"><em><strong>All four<\/strong><\/em><\/span><\/s>/);
  assert.match(html, /<h2>Heading<\/h2>/);
  assert.match(html, /<h3>Subheading<\/h3>/);
  assert.match(html, /<ul><li>Bullet<\/li><\/ul>/);
  assert.match(html, /<ol><li>Numbered<\/li><\/ol>/);
  assert.match(html, /aria-label="Completed"/);
  assert.match(html, /aria-label="Not completed"/);
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<script>|contenteditable|<input/);
});

test("NoteContent renders editor-created tables, images and attachments with safe sources", () => {
  const { outputText } = ts.transpileModule(source("NoteContent.tsx"), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 } });
  const module = { exports: {} };
  new Function("require", "module", "exports", outputText)((id) => id === "./noteEditor" ? noteEditor : id.endsWith(".css") ? {} : createRequire(import.meta.url)(id), module, module.exports);
  const mediaNote = { id: "media", title: "Media", blocks: [
    { type: "table", rows: [["Plan", "Ship"], ["<b>no</b>", "yes & no"]] },
    { type: "image", src: "data:image/png;base64,AAAA", alt: "Sketch" },
    { type: "attachment", src: "data:application/pdf;base64,BBBB", name: "Notes <draft>.pdf" },
    { type: "image", src: "javascript:alert(1)" },
  ] };
  const html = renderToStaticMarkup(createElement(module.exports.default, { note: mediaNote }));
  assert.match(html, /<table class="note-table"><tbody><tr><td>Plan<\/td><td>Ship<\/td><\/tr>/);
  assert.match(html, /&lt;b&gt;no&lt;\/b&gt;/);
  assert.match(html, /&amp; no/);
  assert.match(html, /<img class="note-image" src="data:image\/png;base64,AAAA" alt="Sketch" loading="lazy"\/>/);
  assert.match(html, /download="Notes &lt;draft&gt;.pdf"/);
  assert.doesNotMatch(html, /javascript:/);
});

test("editor HTML is produced only through escaped serialization with whitelisted sources", () => {
  const html = blocksToHtml([
    { type: "paragraph", content: [{ text: "plain <img src=x onerror=alert(1)>" }] },
    { type: "heading", content: [{ text: "Title", marks: ["bold"] }] },
    { type: "checklist", items: [{ checked: true, content: [{ text: "Done", marks: ["italic"] }] }] },
    { type: "table", rows: [["a<b", "c&d"]] },
    { type: "image", src: "javascript:alert(1)" },
    { type: "image", src: "data:image/png;base64,AAAA", alt: `"quoted"` },
    { type: "attachment", src: "javascript:alert(1)", name: "evil" },
    { type: "attachment", src: "data:application/pdf;base64,BBBB", name: "ok.pdf" },
  ]);
  assert.doesNotMatch(html, /<img src=x/);
  assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.match(html, /<h2><strong>Title<\/strong><\/h2>/);
  assert.match(html, /data-checked="true"/);
  assert.match(html, /<em>Done<\/em>/);
  assert.match(html, /<td>a&lt;b<\/td><td>c&amp;d<\/td>/);
  assert.doesNotMatch(html, /javascript:/);
  assert.match(html, /<img src="data:image\/png;base64,AAAA" alt="&quot;quoted&quot;" contenteditable="false">/);
  assert.match(html, /data-name="ok.pdf"/);
  assert.equal(safeNoteSrc("javascript:alert(1)"), "");
  assert.equal(safeNoteSrc("data:image/gif;base64,AA"), "data:image/gif;base64,AA");
  assert.equal(safeNoteSrc("https://example.com/a.png"), "https://example.com/a.png");
});

test("local notes store refreshes unedited board copies but never loses local work", () => {
  assert.equal(isLocalNoteId("local-3"), true);
  assert.equal(isLocalNoteId("to-do"), false);
  const fresh = freshLocalNotes();
  assert.deepEqual(fresh.notes.map((note) => note.id), BOARD_NOTES.map((note) => note.id));
  assert.equal(fresh.sync, notesData.BOARD_SYNC);
  // An edited board copy survives a board refresh; an unedited one is replaced.
  const edited = { ...structuredClone(BOARD_NOTES[0]), title: "my version", edited: true };
  const stored = { ...fresh, sync: 0, notes: [edited, { id: "local-1", title: "mine", blocks: [], edited: true }], removedBoardIds: [], nextId: 2 };
  const merged = mergeBoardInto(stored);
  assert.equal(merged.sync, notesData.BOARD_SYNC);
  assert.equal(merged.notes.find((note) => note.id === "to-do")?.title, "my version");
  assert.equal(merged.notes.find((note) => note.id === "local-1")?.title, "mine");
  // Visitor-deleted board notes stay deleted across a board refresh.
  const removed = mergeBoardInto({ ...fresh, sync: 0, notes: [], removedBoardIds: [BOARD_NOTES[0].id] });
  assert.deepEqual(removed.notes, []);
  // Without localStorage (server render), the published board is the state.
  assert.deepEqual(loadLocalNotes().notes.map((note) => note.id), BOARD_NOTES.map((note) => note.id));
  assert.equal(saveLocalNotes(fresh).ok, false); // no storage available in this environment
  assert.equal(ATTACHMENT_LIMIT_BYTES, 750 * 1024);
});

test("the MacBook layout renders three panes with an operational editor and toolbar", () => {
  const require = createRequire(import.meta.url);
  function component(file, mocks = {}) {
    const { outputText } = ts.transpileModule(source(file), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 } });
    const module = { exports: {} };
    new Function("require", "module", "exports", outputText)((id) => id in mocks ? mocks[id] : id.endsWith(".css") ? {} : require(id), module, module.exports);
    return module.exports;
  }
  const Notes = component("DesktopNotes.tsx", {
    "./DesktopWindow": component("DesktopWindow.tsx", { "./desktopState": desktopState }),
    "./DesktopIcon": { default: () => null },
    "./NoteContent": component("NoteContent.tsx", { "./noteEditor": noteEditor }),
    "./notesData": notesData,
    "./desktopState": desktopState,
    "./noteEditor": noteEditor,
    "./localNotes": localNotes,
  }).default;
  const html = renderToStaticMarkup(createElement(Notes, {
    selectedId: "to-do", openRequest: null, onSelect() {}, active: true, foreground: true, minimized: false, zIndex: 2, onActivate() {}, onMinimize() {}, onClose() {},
  }));
  for (const label of ["Notes folders", "Hide Notes sidebar", "Note list options", "Copy link to this note", "Close Notes", "Minimize Notes", "Enter full screen for Notes", "Note title", "Note body"]) assert.ok(html.includes(`aria-label="${label}"`), label);
  for (const label of ["New folder", "New note", "Format text", "Checklist", "Table", "Attach file", "Markup"]) {
    const match = html.match(new RegExp(`<button[^>]*aria-label="${label}"[^>]*>`));
    assert.ok(match, label);
    assert.doesNotMatch(match[0], /disabled/, `${label} must be enabled`);
  }
  assert.doesNotMatch(html, /read-only board/);
  assert.match(html, /contentEditable="true"/g);
  assert.match(html, /data-placeholder="Title"/);
  assert.match(html, /data-placeholder="Type here…"/);
  assert.match(html, /role="textbox"/);
  assert.match(html, /JS debugging through console and devtools/);
  assert.match(html, /Scaling databases/);
  assert.match(html, /<span>1 note<\/span>/);
  assert.match(html, /type="search"/);
  assert.doesNotMatch(html, /<textarea|6 notes/);
});

test("sharing uses stable encoded note links without redirect destinations", () => {
  assert.equal(noteSharePath("to-do"), "/desktop?note=to-do");
  const path = noteSharePath("note & another");
  assert.equal(new URL(path, "https://example.com").searchParams.get("note"), "note & another");
  assert.equal(new URL(noteSharePath("https://evil.example"), "https://example.com").origin, "https://example.com");
});

test("Notes is a singleton window with independent focus, minimize and restore behavior", () => {
  assert.deepEqual(INITIAL_DESKTOP_SESSION.windows.map((item) => item.id), ["terminal-1"]);
  assert.equal(INITIAL_DESKTOP_SESSION.active, "terminal-1");
  let state = reduce(structuredClone(INITIAL_DESKTOP_SESSION), { type: "open-notes" });
  assert.equal(state.active, "notes");
  assert.equal(managedWindowTitle(state.windows[1]), "Notes");
  const originalTerminal = state.windows[0];
  state = reduce(state, { type: "minimize", id: "notes" });
  assert.equal(state.active, "terminal-1");
  state = reduce(state, { type: "open-notes" });
  assert.equal(state.windows.filter((item) => item.app === "notes").length, 1);
  assert.equal(state.windows[0], originalTerminal);
  assert.equal(state.windows[1].minimized, false);
  state = reduce(reduce(state, { type: "show-desktop" }), { type: "show-desktop" });
  assert.equal(state.active, "notes");
  state = reduce(state, { type: "close-terminals" });
  assert.deepEqual(state.windows.map((item) => item.id), ["notes"]);
  assert.equal(reduce(state, { type: "close", id: "notes" }).windows.length, 0);
});

test("Notes integrates with desktop, Dock, deep links and existing window controls", () => {
  const desktop = source("MonitorDesktop.tsx"), notes = source("DesktopNotes.tsx"), store = source("localNotes.ts");
  assert.match(source("DesktopIcon.tsx"), /name: "Notes"/);
  assert.match(source("MacDock.tsx"), /"terminal", "notes"/);
  assert.doesNotMatch(desktop, /<NotesWidget/);
  assert.match(desktop, /<GitHubPulse variant="widget"/);
  assert.match(desktop, /new URLSearchParams\(window.location.search\).get\("note"\)/);
  assert.match(desktop, /id\.startsWith\("local-"\)/);
  assert.match(desktop, /Hide Notes/);
  assert.match(desktop, /Close Notes/);
  assert.match(notes, /<DesktopWindow \{\.\.\.windowProps\}/);
  assert.match(notes, /initialFrame=\{INITIAL_NOTES_FRAME\}/);
  assert.match(notes, /minimumSize=\{\{ width: 440, height: 300 \}\}/);
  assert.match(notes, /navigator.clipboard.writeText\(url\)/);
  assert.match(notes, /shareState === "manual"/);
  assert.match(desktop, /setNoteOpenRequest\(\{ id \}\)/);
  assert.match(notes, /previousOpenRequest !== openRequest/);
  assert.doesNotMatch(notes, /setQuery\(""\); \}, \[selectedId\]/);
  assert.match(notes, /shareGeneration.current === generation/);
  assert.match(notes, /className="mac-note-page" tabIndex=\{0\}/);
  assert.match(desktop, /!target.contains\(document.activeElement\)/);
  assert.match(source("desktopNotes.css"), /@container \(max-width: 400px\)/);
  // Editing is visitor-local by design: guarded localStorage, no raw HTML injection.
  assert.match(store, /NOTES_STORAGE_KEY = "bz-notes-v1"/);
  assert.match(store, /typeof localStorage === "undefined"/);
  assert.match(notes, /saveLocalNotes\(store\)/);
  assert.match(notes, /contentEditable/);
  assert.doesNotMatch(notes + store, /sessionStorage|dangerouslySetInnerHTML/);
  const icon = readFileSync(new URL("../public/macos-icons/notes.png", import.meta.url));
  assert.equal(icon.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
  assert.equal(icon.readUInt32BE(16), 400);
});
