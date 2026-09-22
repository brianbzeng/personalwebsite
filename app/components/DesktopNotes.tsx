"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { FolderAdd24Regular } from "@fluentui/react-icons/svg/folder-add";
import { Folder24Regular } from "@fluentui/react-icons/svg/folder";
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

export default function DesktopNotes({ selectedId, openRequest, onSelect, ...windowProps }: Props) {
  const [query, setQuery] = useState("");
  const [folder, setFolder] = useState<"notes" | "quick">(() => findBoardNote(selectedId)?.folder ?? "notes");
  const [previousOpenRequest, setPreviousOpenRequest] = useState(openRequest);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [sort, setSort] = useState<"date" | "title">("date");
  const [options, setOptions] = useState<"sort" | "note" | null>(null);
  const [now, setNow] = useState<Date | null>(null);
  const [shareState, setShareState] = useState<"idle" | "copied" | "manual">("idle");
  const [shareUrl, setShareUrl] = useState("");
  const shareInput = useRef<HTMLInputElement>(null);
  const sidebarToggle = useRef<HTMLButtonElement>(null);
  const sortButton = useRef<HTMLButtonElement>(null);
  const optionsButton = useRef<HTMLButtonElement>(null);
  const optionsRoot = useRef<HTMLDivElement>(null);
  const shareGeneration = useRef(0);
  const content = useRef<HTMLElement>(null);
  const folderNotes = BOARD_NOTES.filter((item) => (item.folder ?? "notes") === folder);
  const results = filterBoardNotes(query, folderNotes);
  const note = results.find((item) => item.id === selectedId) ?? results[0];
  const [previousNoteId, setPreviousNoteId] = useState(note?.id);
  const groups = sort === "title" ? [{ label: "Notes", items: [...results].sort((a, b) => a.title.localeCompare(b.title)) }]
    : now ? groupBoardNotes(results, now) : [{ label: "Notes", items: results }];
  const authorOnly = "Managed by Brian in Codex — visitors can read and share notes";
  // Reset only for explicit widget/deep-link requests, not ordinary row selection.
  if (previousOpenRequest !== openRequest) {
    setPreviousOpenRequest(openRequest);
    if (openRequest) { setFolder(findBoardNote(openRequest.id)?.folder ?? "notes"); setQuery(""); }
  }
  if (previousNoteId !== note?.id) { setPreviousNoteId(note?.id); setShareState("idle"); }
  useEffect(() => {
    const tick = () => setNow(new Date()); tick();
    const timer = setInterval(tick, 60_000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => () => { shareGeneration.current++; }, []);
  useLayoutEffect(() => { shareGeneration.current++; content.current?.scrollTo(0, 0); }, [note?.id]);
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
  useEffect(() => {
    if (shareState !== "copied") return;
    const timer = setTimeout(() => setShareState("idle"), 2200);
    return () => clearTimeout(timer);
  }, [shareState]);

  async function shareNote() {
    if (!note) return;
    const generation = ++shareGeneration.current;
    const url = new URL(noteSharePath(note.id), window.location.origin).href;
    setShareUrl(url);
    try { await navigator.clipboard.writeText(url); if (shareGeneration.current === generation) setShareState("copied"); }
    catch { if (shareGeneration.current === generation) setShareState("manual"); }
  }

  const chooseFolder = (next: "notes" | "quick") => { setFolder(next); setQuery(""); };
  return <DesktopWindow {...windowProps} className={`mac-notes-window${sidebarVisible ? "" : " is-sidebar-hidden"}`} title="Notes" initialFrame={INITIAL_NOTES_FRAME} minimumSize={{ width: 440, height: 300 }}
    titlebar={<div ref={optionsRoot} className="mac-notes-toolbar" onKeyDown={(event) => {
      if (event.key === "Escape" && options) { event.preventDefault(); event.stopPropagation(); (options === "sort" ? sortButton : optionsButton).current?.focus(); setOptions(null); }
    }}>
      <div className="notes-sidebar-tools">
        <button type="button" disabled title={authorOnly} aria-label="New folder (read-only board)"><FolderAdd24Regular /></button>
        <button type="button" ref={sidebarToggle} title={sidebarVisible ? "Hide sidebar" : "Show sidebar"} aria-label={sidebarVisible ? "Hide Notes sidebar" : "Show Notes sidebar"} aria-expanded={sidebarVisible} onClick={() => setSidebarVisible((value) => !value)}><PanelLeft24Regular /></button>
      </div>
      <div className="notes-collection-tools">
        <div className="notes-collection-heading"><strong>{folder === "quick" ? "Quick Notes" : "Notes"}</strong><span>{results.length} {results.length === 1 ? "note" : "notes"}</span></div>
        <div className="notes-options-anchor" data-notes-options="sort"><button ref={sortButton} type="button" className="notes-round-tool" aria-label="Note list options" aria-expanded={options === "sort"} onClick={() => setOptions((value) => value === "sort" ? null : "sort")}><MoreHorizontal24Regular /></button>
          {options === "sort" && <div className="notes-options-panel" data-window-no-drag role="group" aria-label="Sort notes">
            <button type="button" aria-pressed={sort === "date"} onClick={() => { setSort("date"); setOptions(null); sortButton.current?.focus(); }}>Date edited {sort === "date" && "✓"}</button>
            <button type="button" aria-pressed={sort === "title"} onClick={() => { setSort("title"); setOptions(null); sortButton.current?.focus(); }}>Title {sort === "title" && "✓"}</button>
          </div>}
        </div>
      </div>
      <div className="notes-editor-tools">
        <span className="notes-toolbar-divider" aria-hidden="true" />
        <button type="button" className="notes-round-tool notes-compose" disabled title={authorOnly} aria-label="New note (read-only board)"><NoteEdit24Regular /></button>
        <div className="notes-tool-capsule notes-format-tools" role="group" aria-label="Note authoring tools">
          <button type="button" disabled title={authorOnly} aria-label="Format text (read-only board)"><TextFont24Regular /></button>
          <button type="button" disabled title={authorOnly} aria-label="Checklist (read-only board)"><TaskListLtr24Regular /></button>
          <button type="button" disabled title={authorOnly} aria-label="Table (read-only board)"><Table24Regular /></button>
          <button type="button" className="notes-secondary-tool" disabled title={authorOnly} aria-label="Attach file (read-only board)"><Attach24Regular /></button>
          <button type="button" className="notes-secondary-tool" disabled title={authorOnly} aria-label="Markup (read-only board)"><DrawShape24Regular /></button>
        </div>
        <div className="notes-tool-capsule notes-sharing-tools">
          <button type="button" disabled={!note} onClick={() => void shareNote()} aria-label="Copy link to this note" title={shareState === "copied" ? "Link copied" : "Share note"}><ShareIos24Regular /></button>
          <div className="notes-options-anchor" data-notes-options="note"><button ref={optionsButton} type="button" aria-label="Note options" aria-expanded={options === "note"} onClick={() => setOptions((value) => value === "note" ? null : "note")}><MoreHorizontal24Regular /></button>
            {options === "note" && <div className="notes-options-panel notes-options-right" data-window-no-drag role="group" aria-label="Note actions">
              <button type="button" disabled={!note} onClick={() => { setOptions(null); void shareNote(); optionsButton.current?.focus(); }}>Copy note link</button>
              <button type="button" onClick={() => { setSidebarVisible((value) => !value); setOptions(null); optionsButton.current?.focus(); }}>{sidebarVisible ? "Hide sidebar" : "Show sidebar"}</button>
            </div>}
          </div>
        </div>
        <label className="mac-notes-search" data-window-no-drag><Search24Regular /><ChevronDown12Regular /><span className="sr-only">Search notes</span><input type="search" placeholder="Search" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
      </div>
    </div>}>
    <div className="mac-notes-layout">
      <aside className="mac-notes-folders" aria-label="Notes folders" hidden={!sidebarVisible}>
        <button type="button" className="notes-folder-row notes-quick-folder" aria-current={folder === "quick" ? "true" : undefined} onClick={() => chooseFolder("quick")}><Note24Regular /><span>Quick Notes</span><small>{BOARD_NOTES.filter((item) => item.folder === "quick").length}</small></button>
        <h2 title="Visual account heading; this board does not connect to iCloud">iCloud</h2>
        <button type="button" className="notes-folder-row" aria-current={folder === "notes" ? "true" : undefined} onClick={() => chooseFolder("notes")}><Folder24Regular /><span>Notes</span><small>{BOARD_NOTES.filter((item) => item.folder !== "quick").length}</small></button>
        <h2 title="Visual account heading; no Google account is connected">Google</h2>
      </aside>
      <nav className="mac-notes-list" aria-label="Published notes">
        {groups.filter((group) => group.items.length).map((group) => <section className="notes-date-group" key={group.label}><h2>{group.label}</h2><div>
          {group.items.map((item) => <button key={item.id} type="button" aria-current={note?.id === item.id ? "true" : undefined} onClick={() => onSelect(item.id)}>
            <strong>{item.title}</strong><span>{now && <time dateTime={item.updatedAt}>{noteListDate(item, now)}</time>}<span>{notePlainText(item)}</span></span>
          </button>)}
        </div></section>)}
        {!results.length && <p className="mac-notes-empty">{query ? "No matching notes." : "No notes yet."}</p>}
      </nav>
      <div className="mac-notes-detail">
        <span className="sr-only" role="status">{shareState === "copied" ? "Note link copied to clipboard." : ""}</span>
        {shareState === "copied" && <span className="notes-copy-toast" aria-hidden="true">Link copied</span>}
        {shareState === "manual" && <label className="mac-notes-share-fallback">Copy this link<input ref={shareInput} readOnly value={shareUrl} onFocus={(event) => event.target.select()} /></label>}
        <article ref={content} className="mac-note-page" tabIndex={0} aria-label={note?.title ?? "Note"}>
          {note ? <>{note.updatedAt && <time className="notes-timestamp" dateTime={note.updatedAt}>{noteDateLabel(note)}</time>}<h1>{note.title}</h1><NoteContent note={note} /></> : <p className="mac-notes-empty">{query ? "No matching notes." : "No note selected."}</p>}
        </article>
      </div>
    </div>
  </DesktopWindow>;
}
