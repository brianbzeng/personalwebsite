"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { FolderAdd24Regular } from "@fluentui/react-icons/svg/folder-add";
import { Folder24Regular } from "@fluentui/react-icons/svg/folder";
import { Dismiss12Regular } from "@fluentui/react-icons/svg/dismiss";
import { PanelLeft24Regular } from "@fluentui/react-icons/svg/panel-left";
import { NoteEdit24Regular } from "@fluentui/react-icons/svg/note-edit";
import { Note24Regular } from "@fluentui/react-icons/svg/note";
import { TextFont24Regular } from "@fluentui/react-icons/svg/text-font";
import { TaskListLtr24Regular } from "@fluentui/react-icons/svg/task-list-ltr";
import { Table24Regular } from "@fluentui/react-icons/svg/table";
import { Attach24Regular } from "@fluentui/react-icons/svg/attach";
import { DrawShape24Regular } from "@fluentui/react-icons/svg/draw-shape";
import { ShareIos24Regular } from "@fluentui/react-icons/svg/share-ios";
import { MoreHorizontal24Regular } from "@fluentui/react-icons/svg/more-horizontal";
import { Search24Regular } from "@fluentui/react-icons/svg/search";
import { ChevronDown12Regular } from "@fluentui/react-icons/svg/chevron-down";
import DesktopWindow from "./DesktopWindow";
import DesktopIcon from "./DesktopIcon";
import NoteContent from "./NoteContent";
import { INITIAL_NOTES_FRAME } from "./desktopState";
import { BOARD_NOTES, filterBoardNotes, findBoardNote, groupBoardNotes, noteDateLabel, noteListDate, notePlainText, noteSharePath } from "./notesData";
import { blocksToHtml, htmlToBlocks, safeNoteSrc, CHECK_MARK_SVG } from "./noteEditor";
import { loadLocalNotes, saveLocalNotes, isLocalNoteId, readAttachment, type LocalNotesState, type StoredNote } from "./localNotes";
import "./desktopNotes.css";

type Props = {
  selectedId: string; onSelect: (id: string) => void;
  openRequest: { id: string } | null;
  active: boolean; foreground: boolean; minimized: boolean; zIndex: number;
  onActivate: () => void; onMinimize: () => void; onClose: () => void;
};

export function NotesWidget({ onOpen }: { onOpen: (id?: string) => void }) {
  const note = BOARD_NOTES[0];
  return <button type="button" className="notes-widget" onClick={() => onOpen(note?.id)} aria-label={note ? `Open Notes — ${note.title}` : "Open Notes"}>
    <span className="notes-widget-label"><DesktopIcon name="notes" /><span>Notes</span><span aria-hidden="true">↗</span></span>
    {note ? <><strong className="notes-widget-title">{note.title}</strong><NoteContent note={note} preview /></> : <span>No notes yet.</span>}
  </button>;
}

const MARK_COMMANDS: { mark: string; label: string; glyph: string; className: string }[] = [
  { mark: "bold", label: "Bold", glyph: "B", className: "notes-mark-button-bold" },
  { mark: "italic", label: "Italic", glyph: "I", className: "notes-mark-button-italic" },
  { mark: "underline", label: "Underline", glyph: "U", className: "notes-mark-button-underline" },
  { mark: "strikeThrough", label: "Strikethrough", glyph: "S", className: "notes-mark-button-strike" },
];

function caretRootBlock(editor: HTMLElement): HTMLElement | null {
  const node = window.getSelection()?.anchorNode ?? null;
  if (!node || !editor.contains(node)) return null;
  let current: Node | null = node;
  while (current && current.parentElement !== editor) current = current.parentElement;
  return current instanceof HTMLElement ? current : null;
}
function placeCaret(node: Node, where: "start" | "end" = "end") {
  const range = document.createRange();
  range.selectNodeContents(node);
  range.collapse(where === "start");
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
}
function checkBubble(checked: boolean) {
  const span = document.createElement("span");
  span.className = "note-check";
  span.contentEditable = "false";
  span.setAttribute("role", "img");
  span.setAttribute("aria-label", checked ? "Completed" : "Not completed");
  if (checked) { span.classList.add("is-checked"); span.innerHTML = CHECK_MARK_SVG; }
  return span;
}
function checklistItem(content: Node | string, checked = false) {
  const li = document.createElement("li");
  if (checked) { li.classList.add("is-checked"); li.dataset.checked = "true"; }
  li.appendChild(checkBubble(checked));
  const text = document.createElement("span");
  text.className = "note-check-text";
  if (typeof content === "string") text.innerHTML = content;
  else if (content) Array.from(content.childNodes).forEach((child) => text.appendChild(child));
  li.appendChild(text);
  return li;
}

export default function DesktopNotes({ selectedId, openRequest, onSelect, ...windowProps }: Props) {
  const [store, setStore] = useState<LocalNotesState>(loadLocalNotes);
  const [query, setQuery] = useState("");
  const [folder, setFolder] = useState<string>(() => findBoardNote(selectedId)?.folder ?? "notes");
  const [previousOpenRequest, setPreviousOpenRequest] = useState(openRequest);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [sort, setSort] = useState<"date" | "title">("date");
  const [options, setOptions] = useState<"sort" | "note" | "format" | "table" | null>(null);
  const [now, setNow] = useState<Date | null>(null);
  const [shareState, setShareState] = useState<"idle" | "copied" | "manual">("idle");
  const [shareUrl, setShareUrl] = useState("");
  const [notice, setNotice] = useState("");
  const [undoDelete, setUndoDelete] = useState<StoredNote | null>(null);
  const [renamingFolder, setRenamingFolder] = useState<string | null>(null);
  const [tableSize, setTableSize] = useState({ rows: 2, columns: 2 });
  const [markupOpen, setMarkupOpen] = useState(false);
  const [formatState, setFormatState] = useState<Record<string, boolean>>({});
  const shareInput = useRef<HTMLInputElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const editorRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const sidebarToggle = useRef<HTMLButtonElement>(null);
  const sortButton = useRef<HTMLButtonElement>(null);
  const optionsButton = useRef<HTMLButtonElement>(null);
  const optionsRoot = useRef<HTMLDivElement>(null);
  const formatButton = useRef<HTMLButtonElement>(null);
  const tableButton = useRef<HTMLButtonElement>(null);
  const folderNameInput = useRef<HTMLInputElement>(null);
  const shareGeneration = useRef(0);
  const content = useRef<HTMLElement>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const noticeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const undoTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const notes = store.notes;
  const folderNotes = notes.filter((item) => (item.folder ?? "notes") === folder);
  const results = filterBoardNotes(query, folderNotes);
  const note = results.find((item) => item.id === selectedId) ?? results[0] ?? folderNotes.find((item) => item.id === selectedId) ?? null;
  const [previousNoteId, setPreviousNoteId] = useState(note?.id);
  const groups = sort === "title" ? [{ label: "Notes", items: [...results].sort((a, b) => a.title.localeCompare(b.title)) }]
    : now ? groupBoardNotes(results, now) : [{ label: "Notes", items: results }];

  // Reset only for explicit widget/deep-link requests, not ordinary row selection.
  if (previousOpenRequest !== openRequest) {
    setPreviousOpenRequest(openRequest);
    if (openRequest) {
      const target = notes.find((item) => item.id === openRequest.id);
      if (target) { setFolder(target.folder ?? "notes"); setQuery(""); }
    }
  }
  if (previousNoteId !== note?.id) { setPreviousNoteId(note?.id); setShareState("idle"); }

  useEffect(() => {
    const tick = () => setNow(new Date()); tick();
    const timer = setInterval(tick, 60_000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => () => { shareGeneration.current++; if (saveTimer.current) clearTimeout(saveTimer.current); if (noticeTimer.current) clearTimeout(noticeTimer.current); if (undoTimer.current) clearTimeout(undoTimer.current); }, []);
  useLayoutEffect(() => { shareGeneration.current++; content.current?.scrollTo(0, 0); }, [note?.id]);
  // Debounced persistence; failures surface as a toast instead of silent data loss.
  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const result = saveLocalNotes(store);
      if (!result.ok) setNotice(`Couldn't save notes — ${result.error}`);
    }, 350);
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current); };
  }, [store]);
  useEffect(() => {
    if (!notice) return;
    if (noticeTimer.current) clearTimeout(noticeTimer.current);
    noticeTimer.current = setTimeout(() => setNotice(""), 3600);
  }, [notice]);
  useEffect(() => {
    if (!undoDelete) return;
    undoTimer.current = setTimeout(() => setUndoDelete(null), 8000);
    return () => { if (undoTimer.current) clearTimeout(undoTimer.current); };
  }, [undoDelete]);
  useEffect(() => {
    if (!options) return;
    const dismiss = (event: PointerEvent) => {
      const anchor = optionsRoot.current?.querySelector(`[data-notes-options="${options}"]`);
      if (!anchor?.contains(event.target as Node)) setOptions(null);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [options]);
  useEffect(() => { if (shareState === "manual") { shareInput.current?.focus(); shareInput.current?.select(); } }, [shareState]);
  useEffect(() => { if (shareState !== "copied") return; const timer = setTimeout(() => setShareState("idle"), 2200); return () => clearTimeout(timer); }, [shareState]);
  useEffect(() => { if (renamingFolder) folderNameInput.current?.focus(); }, [renamingFolder]);
  useEffect(() => { if (!markupOpen) return; const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") setMarkupOpen(false); }; document.addEventListener("keydown", onKey); return () => document.removeEventListener("keydown", onKey); }, [markupOpen]);
  // Track active marks so the format popover reflects the selection.
  useEffect(() => {
    const update = () => {
      if (!editorRef.current) return;
      const selection = document.getSelection();
      if (!selection || !selection.anchorNode || !editorRef.current.contains(selection.anchorNode)) return;
      try {
        setFormatState({
          bold: document.queryCommandState("bold"),
          italic: document.queryCommandState("italic"),
          underline: document.queryCommandState("underline"),
          strikeThrough: document.queryCommandState("strikeThrough"),
        });
      } catch { /* command state unavailable; popover still acts on the selection */ }
    };
    document.addEventListener("selectionchange", update);
    return () => document.removeEventListener("selectionchange", update);
  }, []);
  // The editor DOM owns note content while a note is open; reseed only when switching notes.
  useEffect(() => {
    if (editorRef.current) editorRef.current.innerHTML = blocksToHtml(note?.blocks ?? []);
    if (titleRef.current) titleRef.current.textContent = note?.title ?? "";
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [note?.id]);

  function flashNotice(message: string) { setNotice(message); }
  function patchNote(id: string, patch: (note: StoredNote) => StoredNote) {
    setStore((state) => ({ ...state, notes: state.notes.map((item) => item.id === id ? patch(item) : item) }));
  }
  function syncFromEditor() {
    if (!note || !editorRef.current || !titleRef.current) return;
    const blocks = htmlToBlocks(editorRef.current);
    const title = titleRef.current.textContent ?? "";
    patchNote(note.id, (item) => ({ ...item, title, blocks, edited: true, updatedAt: new Date().toISOString() }));
  }
  function runCommand(command: string) {
    editorRef.current?.focus();
    document.execCommand(command);
    syncFromEditor();
  }
  function currentBlock() { return editorRef.current ? caretRootBlock(editorRef.current) : null; }
  function transformBlock(replace: (block: HTMLElement) => HTMLElement | DocumentFragment | null) {
    const editor = editorRef.current;
    const block = currentBlock();
    if (!editor || !block) return;
    const next = replace(block);
    if (!next) return;
    const landing = next instanceof HTMLElement ? next : (next.lastChild ?? next);
    block.replaceWith(next);
    if (landing instanceof Node) placeCaret(landing);
    syncFromEditor();
  }
  function inlineHtml(block: HTMLElement) {
    const clone = block.cloneNode(true) as HTMLElement;
    clone.querySelectorAll(".note-check").forEach((node) => node.remove());
    const text = clone.querySelector(".note-check-text");
    return (text ?? clone).innerHTML;
  }
  /** List items of a root block (or the block itself as a single pseudo-item). */
  function listItems(block: HTMLElement): HTMLElement[] {
    if (block.tagName === "UL" || block.tagName === "OL") return Array.from(block.children).filter((child): child is HTMLElement => child.tagName === "LI");
    return [block];
  }
  function setBlockType(type: "paragraph" | "heading" | "subheading") {
    transformBlock((block) => {
      const tag = type === "heading" ? "h2" : type === "subheading" ? "h3" : "p";
      if (block.tagName === tag.toUpperCase()) return null;
      const fragment = document.createDocumentFragment();
      for (const item of listItems(block)) {
        const next = document.createElement(tag);
        next.innerHTML = inlineHtml(item);
        fragment.appendChild(next);
      }
      return fragment;
    });
  }
  function setListType(type: "bullets" | "numbered") {
    transformBlock((block) => {
      const list = document.createElement(type === "bullets" ? "ul" : "ol");
      for (const item of listItems(block)) {
        const li = document.createElement("li");
        li.innerHTML = inlineHtml(item);
        list.appendChild(li);
      }
      return list;
    });
  }
  function setChecklist() {
    transformBlock((block) => {
      if (block.tagName === "UL" && block.classList.contains("note-checklist")) {
        const fragment = document.createDocumentFragment();
        for (const item of listItems(block)) {
          const paragraph = document.createElement("p");
          paragraph.innerHTML = inlineHtml(item);
          fragment.appendChild(paragraph);
        }
        return fragment;
      }
      const list = document.createElement("ul");
      list.className = "note-checklist";
      for (const item of listItems(block)) list.appendChild(checklistItem(inlineHtml(item)));
      return list;
    });
  }
  function insertTable() {
    const editor = editorRef.current;
    if (!editor) return;
    const table = document.createElement("table");
    const body = document.createElement("tbody");
    for (let row = 0; row < tableSize.rows; row++) {
      const tr = document.createElement("tr");
      for (let column = 0; column < tableSize.columns; column++) {
        const td = document.createElement("td");
        td.innerHTML = "<br>";
        tr.appendChild(td);
      }
      body.appendChild(tr);
    }
    table.appendChild(body);
    const paragraph = document.createElement("p");
    paragraph.innerHTML = "<br>";
    const block = currentBlock();
    if (block) { block.insertAdjacentElement("afterend", table); table.insertAdjacentElement("afterend", paragraph); } else { editor.appendChild(table); editor.appendChild(paragraph); }
    placeCaret(body.querySelector("td")!, "start");
    setOptions(null);
    syncFromEditor();
  }
  function insertAttachment(src: string, name: string, kind: "image" | "file") {
    const editor = editorRef.current;
    if (!editor) return;
    const element = kind === "image"
      ? Object.assign(document.createElement("img"), { src }) as HTMLImageElement
      : (() => { const span = document.createElement("span"); span.className = "note-attachment"; span.contentEditable = "false"; span.dataset.src = src; span.dataset.name = name; span.textContent = `📎 ${name}`; return span; })();
    if (kind === "image") element.contentEditable = "false";
    const paragraph = document.createElement("p");
    paragraph.innerHTML = "<br>";
    const block = currentBlock();
    if (block) { block.insertAdjacentElement("afterend", element); element.insertAdjacentElement("afterend", paragraph); } else { editor.appendChild(element); editor.appendChild(paragraph); }
    placeCaret(paragraph, "start");
    syncFromEditor();
  }
  function createNote() {
    const id = `local-${store.nextId}`;
    const targetFolder = folder === "quick" ? "notes" : folder;
    const created: StoredNote = { id, title: "", blocks: [{ type: "paragraph", content: [] }], folder: targetFolder, updatedAt: new Date().toISOString(), edited: true };
    setStore((state) => ({ ...state, notes: [created, ...state.notes], nextId: state.nextId + 1 }));
    setQuery("");
    setFolder(targetFolder);
    onSelect(id);
    requestAnimationFrame(() => titleRef.current?.focus());
  }
  function deleteNote(target: StoredNote) {
    setStore((state) => ({
      ...state,
      notes: state.notes.filter((item) => item.id !== target.id),
      removedBoardIds: isLocalNoteId(target.id) ? state.removedBoardIds : [...state.removedBoardIds, target.id],
    }));
    setUndoDelete(target);
    setOptions(null);
    flashNotice("Note deleted");
  }
  function restoreDeleted() {
    if (!undoDelete) return;
    const restored = undoDelete;
    setStore((state) => ({
      ...state,
      notes: [restored, ...state.notes],
      removedBoardIds: state.removedBoardIds.filter((id) => id !== restored.id),
    }));
    setUndoDelete(null);
    setNotice("");
  }
  function createFolder() {
    const id = `folder-${store.nextFolder}`;
    setStore((state) => ({ ...state, folders: [...state.folders, { id, name: "New Folder" }], nextFolder: state.nextFolder + 1 }));
    setFolder(id);
    setRenamingFolder(id);
  }
  function renameFolder(id: string, name: string) {
    const clean = name.trim();
    setStore((state) => clean
      ? { ...state, folders: state.folders.map((item) => item.id === id ? { ...item, name: clean } : item) }
      : state);
    setRenamingFolder(null);
  }
  function deleteFolder(id: string) {
    setStore((state) => ({
      ...state,
      folders: state.folders.filter((item) => item.id !== id),
      notes: state.notes.map((item) => (item.folder === id ? { ...item, folder: "notes" } : item)),
    }));
    if (folder === id) setFolder("notes");
  }

  async function shareNote() {
    if (!note) return;
    const generation = ++shareGeneration.current;
    const url = new URL(noteSharePath(note.id), window.location.origin).href;
    setShareUrl(url);
    try { await navigator.clipboard.writeText(url); if (shareGeneration.current === generation) setShareState("copied"); }
    catch { if (shareGeneration.current === generation) setShareState("manual"); }
  }

  async function onAttach(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    try {
      const src = await readAttachment(file);
      insertAttachment(src, file.name, file.type.startsWith("image/") ? "image" : "file");
    } catch (error) {
      flashNotice(error instanceof Error ? error.message : "Could not attach the file.");
    }
  }

  const chooseFolder = (next: string) => { setFolder(next); setQuery(""); };
  const folderLabel = folder === "quick" ? "Quick Notes" : folder === "notes" ? "Notes" : (store.folders.find((item) => item.id === folder)?.name ?? "Notes");
  return <DesktopWindow {...windowProps} className={`mac-notes-window${sidebarVisible ? "" : " is-sidebar-hidden"}`} title="Notes" initialFrame={INITIAL_NOTES_FRAME} minimumSize={{ width: 440, height: 300 }}
    titlebar={<div ref={optionsRoot} className="mac-notes-toolbar" onKeyDown={(event) => {
      if (event.key === "Escape" && options) { event.preventDefault(); event.stopPropagation(); (options === "sort" ? sortButton : options === "note" ? optionsButton : options === "format" ? formatButton : tableButton).current?.focus(); setOptions(null); }
    }}>
      <div className="notes-sidebar-tools">
        <button type="button" onClick={createFolder} aria-label="New folder" title="New folder"><FolderAdd24Regular /></button>
        <button type="button" ref={sidebarToggle} title={sidebarVisible ? "Hide sidebar" : "Show sidebar"} aria-label={sidebarVisible ? "Hide Notes sidebar" : "Show Notes sidebar"} aria-expanded={sidebarVisible} onClick={() => setSidebarVisible((value) => !value)}><PanelLeft24Regular /></button>
      </div>
      <div className="notes-collection-tools">
        <div className="notes-collection-heading"><strong>{folderLabel}</strong><span>{results.length} {results.length === 1 ? "note" : "notes"}</span></div>
        <div className="notes-options-anchor" data-notes-options="sort"><button ref={sortButton} type="button" className="notes-round-tool" aria-label="Note list options" aria-expanded={options === "sort"} onClick={() => setOptions((value) => value === "sort" ? null : "sort")}><MoreHorizontal24Regular /></button>
          {options === "sort" && <div className="notes-options-panel" data-window-no-drag role="group" aria-label="Sort notes">
            <button type="button" aria-pressed={sort === "date"} onClick={() => { setSort("date"); setOptions(null); sortButton.current?.focus(); }}>Date edited {sort === "date" && "✓"}</button>
            <button type="button" aria-pressed={sort === "title"} onClick={() => { setSort("title"); setOptions(null); sortButton.current?.focus(); }}>Title {sort === "title" && "✓"}</button>
          </div>}
        </div>
      </div>
      <div className="notes-editor-tools">
        <span className="notes-toolbar-divider" aria-hidden="true" />
        <button type="button" className="notes-round-tool notes-compose" onClick={createNote} aria-label="New note" title="New note"><NoteEdit24Regular /></button>
        <div className="notes-tool-capsule notes-format-tools" role="group" aria-label="Note authoring tools">
          <div className="notes-options-anchor" data-notes-options="format">
            <button ref={formatButton} type="button" aria-label="Format text" aria-expanded={options === "format"} aria-haspopup="menu" title="Format text"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => setOptions((value) => value === "format" ? null : "format")}><TextFont24Regular /></button>
            {options === "format" && <div className="notes-options-panel notes-format-panel" data-window-no-drag role="menu" aria-label="Format text"
              onKeyDown={(event) => { if (event.key === "Escape") { event.stopPropagation(); setOptions(null); formatButton.current?.focus(); } }}>
              <div className="notes-format-blocks" role="group" aria-label="Paragraph styles">
                <button type="button" role="menuitem" onMouseDown={(event) => event.preventDefault()} onClick={() => setBlockType("heading")}>Title</button>
                <button type="button" role="menuitem" onMouseDown={(event) => event.preventDefault()} onClick={() => setBlockType("subheading")}>Heading</button>
                <button type="button" role="menuitem" onMouseDown={(event) => event.preventDefault()} onClick={() => setBlockType("paragraph")}>Body</button>
              </div>
              <hr />
              <div className="notes-format-marks" role="group" aria-label="Text styles">
                {MARK_COMMANDS.map((item) => <button key={item.mark} type="button" role="menuitem" className={`notes-mark-button ${item.className}`}
                  aria-pressed={formatState[item.mark] === true} aria-label={item.label} title={item.label}
                  onMouseDown={(event) => event.preventDefault()} onClick={() => runCommand(item.mark)}>{item.glyph}</button>)}
              </div>
              <hr />
              <div className="notes-format-lists" role="group" aria-label="List styles">
                <button type="button" role="menuitem" onMouseDown={(event) => event.preventDefault()} onClick={setListType.bind(null, "bullets")} aria-label="Bulleted list" title="Bulleted list">• List</button>
                <button type="button" role="menuitem" onMouseDown={(event) => event.preventDefault()} onClick={setListType.bind(null, "numbered")} aria-label="Numbered list" title="Numbered list">1. List</button>
                <button type="button" role="menuitem" onMouseDown={(event) => event.preventDefault()} onClick={setChecklist} aria-label="Checklist" title="Checklist">✓ List</button>
              </div>
            </div>}
          </div>
          <button type="button" aria-label="Checklist" title="Checklist" onMouseDown={(event) => event.preventDefault()} onClick={setChecklist}><TaskListLtr24Regular /></button>
          <div className="notes-options-anchor" data-notes-options="table">
            <button ref={tableButton} type="button" aria-label="Table" aria-expanded={options === "table"} aria-haspopup="menu" title="Table"
              onMouseDown={(event) => event.preventDefault()} onClick={() => setOptions((value) => value === "table" ? null : "table")}><Table24Regular /></button>
            {options === "table" && <div className="notes-options-panel notes-table-panel" data-window-no-drag role="group" aria-label="Insert table">
              <label>Rows<input type="number" min={1} max={12} inputMode="numeric" value={tableSize.rows}
                onChange={(event) => setTableSize((size) => ({ ...size, rows: Math.min(12, Math.max(1, Number(event.target.value) || 1)) }))} /></label>
              <label>Columns<input type="number" min={1} max={8} inputMode="numeric" value={tableSize.columns}
                onChange={(event) => setTableSize((size) => ({ ...size, columns: Math.min(8, Math.max(1, Number(event.target.value) || 1)) }))} /></label>
              <button type="button" onClick={insertTable}>Insert Table</button>
            </div>}
          </div>
          <button type="button" className="notes-secondary-tool" aria-label="Attach file" title="Attach file" onClick={() => fileInput.current?.click()}><Attach24Regular /></button>
          <button type="button" className="notes-secondary-tool" aria-label="Markup" title="Markup" onClick={() => setMarkupOpen(true)}><DrawShape24Regular /></button>
        </div>
        <div className="notes-tool-capsule notes-sharing-tools">
          <button type="button" disabled={!note} onClick={() => void shareNote()} aria-label="Copy link to this note" title={shareState === "copied" ? "Link copied" : "Share note"}><ShareIos24Regular /></button>
          <div className="notes-options-anchor" data-notes-options="note"><button ref={optionsButton} type="button" aria-label="Note options" aria-expanded={options === "note"} onClick={() => setOptions((value) => value === "note" ? null : "note")}><MoreHorizontal24Regular /></button>
            {options === "note" && <div className="notes-options-panel notes-options-right" data-window-no-drag role="group" aria-label="Note actions">
              <button type="button" disabled={!note} onClick={() => { setOptions(null); void shareNote(); optionsButton.current?.focus(); }}>Copy note link</button>
              <button type="button" disabled={!note} onClick={() => { setSidebarVisible((value) => !value); setOptions(null); optionsButton.current?.focus(); }}>{sidebarVisible ? "Hide sidebar" : "Show sidebar"}</button>
              <button type="button" disabled={!note} onClick={() => note && deleteNote(note)}>Delete Note</button>
            </div>}
          </div>
        </div>
        <label className="mac-notes-search" data-window-no-drag><Search24Regular /><ChevronDown12Regular /><span className="sr-only">Search notes</span><input type="search" placeholder="Search" value={query} onChange={(event) => { setQuery(event.target.value); }} /></label>
      </div>
      <input ref={fileInput} type="file" hidden onChange={(event) => void onAttach(event)} aria-hidden="true" tabIndex={-1} accept="image/*,.pdf,.txt,.md,.json,.csv" />
    </div>}>
    <div className="mac-notes-layout">
      <aside className="mac-notes-folders" aria-label="Notes folders" hidden={!sidebarVisible}>
        <button type="button" className="notes-folder-row notes-quick-folder" aria-current={folder === "quick" ? "true" : undefined} onClick={() => chooseFolder("quick")}><Note24Regular /><span>Quick Notes</span><small>{notes.filter((item) => item.folder === "quick").length}</small></button>
        <h2 title="Visual account heading; this board does not connect to iCloud">iCloud</h2>
        <button type="button" className="notes-folder-row" aria-current={folder === "notes" ? "true" : undefined} onClick={() => chooseFolder("notes")}><Folder24Regular /><span>Notes</span><small>{notes.filter((item) => (item.folder ?? "notes") === "notes").length}</small></button>
        {store.folders.map((item) => <div key={item.id} className="notes-folder-entry" data-renaming={renamingFolder === item.id || undefined}>
          {renamingFolder === item.id
            ? <input ref={folderNameInput} className="notes-folder-rename" defaultValue={item.name} aria-label="Folder name"
              onBlur={(event) => renameFolder(item.id, event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") renameFolder(item.id, (event.target as HTMLInputElement).value);
                if (event.key === "Escape") setRenamingFolder(null);
              }} />
            : <button type="button" className="notes-folder-row" aria-current={folder === item.id ? "true" : undefined} onClick={() => chooseFolder(item.id)} onDoubleClick={() => setRenamingFolder(item.id)}>
              <Folder24Regular /><span>{item.name}</span><small>{notes.filter((entry) => entry.folder === item.id).length}</small>
            </button>}
          <button type="button" className="notes-folder-delete" aria-label={`Delete folder ${item.name}`} title={`Delete folder ${item.name}`}
            onClick={() => deleteFolder(item.id)}><Dismiss12Regular /></button>
        </div>)}
        <h2 title="Visual account heading; no Google account is connected">Google</h2>
      </aside>
      <nav className="mac-notes-list" aria-label="Notes">
        {groups.filter((group) => group.items.length).map((group) => <section className="notes-date-group" key={group.label}><h2>{group.label}</h2><div>
          {group.items.map((item) => <button key={item.id} type="button" aria-current={note?.id === item.id ? "true" : undefined} onClick={() => onSelect(item.id)}>
            <strong>{item.title || "New Note"}</strong><span>{now && <time dateTime={item.updatedAt}>{noteListDate(item, now)}</time>}<span>{notePlainText(item)}</span></span>
          </button>)}
        </div></section>)}
        {!results.length && <p className="mac-notes-empty">{query ? "No matching notes." : "No notes yet."}</p>}
      </nav>
      <div className="mac-notes-detail">
        <span className="sr-only" role="status">{shareState === "copied" ? "Note link copied to clipboard." : ""}</span>
        {shareState === "copied" && <span className="notes-copy-toast" aria-hidden="true">Link copied</span>}
        {notice && <span className="notes-copy-toast is-action" role="status">{notice}{undoDelete && <button type="button" onClick={restoreDeleted}>Undo</button>}</span>}
        {shareState === "manual" && <label className="mac-notes-share-fallback">Copy this link<input ref={shareInput} readOnly value={shareUrl} onFocus={(event) => event.target.select()} /></label>}
        <article ref={content} className="mac-note-page" tabIndex={0} aria-label={note?.title || "Note"}>
          {note ? <>
            {note.updatedAt && <time className="notes-timestamp" dateTime={note.updatedAt}>{noteDateLabel(note)}</time>}
            <h1 ref={titleRef} className="mac-note-title" contentEditable suppressContentEditableWarning role="textbox" aria-label="Note title" spellCheck
              data-placeholder="Title"
              onInput={() => syncFromEditor()}
              onPaste={(event) => { event.preventDefault(); document.execCommand("insertText", false, event.clipboardData.getData("text/plain")); }}
              onKeyDown={(event) => {
                if (event.key === "Enter") { event.preventDefault(); if (editorRef.current) placeCaret(editorRef.current, "start"); }
              }} />
            <div ref={editorRef} className="note-content mac-note-editor" contentEditable suppressContentEditableWarning role="textbox" aria-multiline="true" aria-label="Note body" spellCheck
              data-placeholder="Type here…"
              onInput={() => syncFromEditor()}
              onPaste={(event) => { event.preventDefault(); document.execCommand("insertText", false, event.clipboardData.getData("text/plain")); }}
              onClick={(event) => {
                const bubble = (event.target as HTMLElement).closest(".note-check");
                if (!bubble) return;
                const li = bubble.closest("li");
                if (!li) return;
                const checked = li.dataset.checked !== "true";
                li.classList.toggle("is-checked", checked);
                li.dataset.checked = checked ? "true" : "false";
                li.replaceChild(checkBubble(checked), bubble);
                syncFromEditor();
              }}
              onKeyDown={(event) => {
                if (event.key !== "Enter") return;
                event.preventDefault();
                const editor = editorRef.current;
                if (!editor) return;
                const anchor = window.getSelection()?.anchorNode;
                const li = anchor?.nodeType === Node.TEXT_NODE || anchor instanceof Element
                  ? (anchor instanceof Element ? anchor : anchor.parentElement)?.closest("li") : null;
                if (li && li.parentElement && li.parentElement.tagName === "UL" && li.parentElement.classList.contains("note-checklist")) {
                  const text = li.querySelector(".note-check-text");
                  if (text && !text.textContent) {
                    const paragraph = document.createElement("p");
                    paragraph.innerHTML = "<br>";
                    li.parentElement.insertAdjacentElement("afterend", paragraph);
                    li.remove();
                    if (!li.parentElement.children.length) li.parentElement.remove();
                    placeCaret(paragraph, "start");
                  } else {
                    const fresh = checklistItem("");
                    li.insertAdjacentElement("afterend", fresh);
                    placeCaret(fresh.querySelector(".note-check-text")!, "start");
                  }
                } else {
                  const cell = anchor ? (anchor instanceof Element ? anchor : anchor.parentElement)?.closest("td, th") : null;
                  if (!cell) {
                    // An explicit split keeps block structure predictable across browsers.
                    document.execCommand("defaultParagraphSeparator", false, "p");
                    document.execCommand("insertParagraph");
                  }
                }
                syncFromEditor();
              }} />
          </> : <p className="mac-notes-empty">{query ? "No matching notes." : "No note selected."}</p>}
        </article>
        {markupOpen && note && <NotesMarkup onCancel={() => setMarkupOpen(false)} onDone={(src) => {
          setMarkupOpen(false);
          insertAttachment(src, "Markup.png", "image");
        }} />}
      </div>
    </div>
  </DesktopWindow>;
}

/** Mac-style markup sheet: draw over a clean canvas, then insert it as an image. */
function NotesMarkup({ onDone, onCancel }: { onDone: (src: string) => void; onCancel: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const [color, setColor] = useState("#f5f5f5");
  const [width, setWidth] = useState(3);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    context.fillStyle = "#f7f7f0";
    context.fillRect(0, 0, canvas.width, canvas.height);
  }, []);
  function point(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return { x: (event.clientX - rect.left) * (canvas.width / rect.width), y: (event.clientY - rect.top) * (canvas.height / rect.height) };
  }
  function stroke(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context || !drawing.current) return;
    const { x, y } = point(event);
    context.strokeStyle = color;
    context.lineWidth = width * 2;
    context.lineCap = "round";
    context.lineJoin = "round";
    context.lineTo(x, y);
    context.stroke();
  }
  return <div className="notes-markup" role="dialog" aria-modal="true" aria-label="Markup" data-window-no-drag>
    <div className="notes-markup-tools">
      {[{ value: "#f5f5f5", label: "White" }, { value: "#ff5148", label: "Red" }, { value: "#6db2ff", label: "Blue" }, { value: "#ffd465", label: "Yellow" }].map((item) =>
        <button key={item.value} type="button" className="notes-markup-color" aria-pressed={color === item.value} aria-label={item.label} title={item.label}
          style={{ background: item.value }} onClick={() => setColor(item.value)} />)}
      <span className="notes-toolbar-divider" aria-hidden="true" />
      {[2, 4, 8].map((size) => <button key={size} type="button" className="notes-markup-width" aria-pressed={width === size} aria-label={`${size === 2 ? "Thin" : size === 4 ? "Medium" : "Thick"} pen`} title={`${size === 2 ? "Thin" : size === 4 ? "Medium" : "Thick"} pen`} onClick={() => setWidth(size)}><i style={{ width: size + 3, height: size + 3 }} /></button>)}
      <span className="notes-toolbar-divider" aria-hidden="true" />
      <button type="button" onClick={() => {
        const canvas = canvasRef.current;
        const context = canvas?.getContext("2d");
        if (!canvas || !context) return;
        context.fillStyle = "#f7f7f0";
        context.fillRect(0, 0, canvas.width, canvas.height);
      }}>Clear</button>
      <button type="button" onClick={onCancel}>Cancel</button>
      <button type="button" className="notes-markup-done" onClick={() => onDone(canvasRef.current?.toDataURL("image/png") ?? "")}>Done</button>
    </div>
    <canvas ref={canvasRef} width={920} height={520} aria-label="Drawing canvas" tabIndex={0}
      onPointerDown={(event) => {
        const context = canvasRef.current?.getContext("2d");
        if (!context) return;
        event.currentTarget.setPointerCapture(event.pointerId);
        drawing.current = true;
        const { x, y } = point(event);
        context.strokeStyle = color;
        context.lineWidth = width * 2;
        context.lineCap = "round";
        context.beginPath();
        context.moveTo(x, y);
      }}
      onPointerMove={stroke}
      onPointerUp={() => { drawing.current = false; }}
      onPointerLeave={() => { drawing.current = false; }} />
  </div>;
}
