export type NoteMark = "bold" | "italic" | "underline" | "strikethrough";
export type NoteText = { text: string; marks?: NoteMark[] };
export type NoteBlock =
  | { type: "paragraph"; content: NoteText[] }
  | { type: "heading"; content: NoteText[] }
  | { type: "subheading"; content: NoteText[] }
  | { type: "bullets"; items: NoteText[][] }
  | { type: "numbered"; items: NoteText[][] }
  | { type: "checklist"; items: { checked: boolean; content: NoteText[] }[] }
  | { type: "table"; rows: string[][] }
  | { type: "image"; src: string; alt?: string }
  | { type: "attachment"; src: string; name: string };
/** Folders are ids: the board ships "notes" and "quick"; visitors add local ones. */
export type BoardNote = { id: string; title: string; blocks: NoteBlock[]; updatedAt?: string; folder?: string };

/** Bump when BOARD_NOTES changes so unedited board copies refresh for returning visitors. */
export const BOARD_SYNC = 1;

// Published content is managed with Brian in Codex, not visitor-local storage.
export const BOARD_NOTES: BoardNote[] = [{
  id: "to-do",
  title: "to do:",
  updatedAt: "2026-09-22T05:55:00.000-07:00",
  blocks: [{ type: "checklist", items: [
    { checked: true, content: [{ text: "JS debugging through console and devtools" }] },
    { checked: true, content: [{ text: "Version control & VCS hosting" }] },
    { checked: true, content: [{ text: "Data structures & algorithms" }] },
    { checked: true, content: [{ text: "System design" }] },
    { checked: true, content: [{ text: "Performance/Latency" }] },
    { checked: true, content: [{ text: "Cache control" }] },
    { checked: false, content: [{ text: "Scaling databases" }] },
  ] }],
}];

export function notePlainText(note: BoardNote): string {
  const text = (content: NoteText[]) => content.map((part) => part.text).join("");
  return note.blocks.map((block) => {
    if (block.type === "checklist") return block.items.map((item) => text(item.content)).join("\n");
    if (block.type === "bullets" || block.type === "numbered") return block.items.map(text).join("\n");
    if (block.type === "table") return block.rows.map((row) => row.join(" ")).join("\n");
    if (block.type === "image") return block.alt ? `Image — ${block.alt}` : "Image";
    if (block.type === "attachment") return block.name;
    return text(block.content);
  }).join("\n");
}
export function findBoardNote(id: string | null, notes = BOARD_NOTES) {
  return notes.find((note) => note.id === id);
}
export function filterBoardNotes(query: string, notes = BOARD_NOTES) {
  const term = query.trim().toLocaleLowerCase();
  return notes.filter((note) => `${note.title}\n${notePlainText(note)}`.toLocaleLowerCase().includes(term));
}
export function noteSharePath(id: string) { return `/desktop?note=${encodeURIComponent(id)}`; }

const NOTE_TIME_ZONE = "America/Los_Angeles";
function noteDate(note: BoardNote) {
  const date = note.updatedAt ? new Date(note.updatedAt) : null;
  return date && Number.isFinite(date.getTime()) ? date : null;
}
function calendarDay(date: Date) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: NOTE_TIME_ZONE, year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
}
export function noteDateLabel(note: BoardNote) {
  const date = noteDate(note);
  return date ? new Intl.DateTimeFormat("en-US", { timeZone: NOTE_TIME_ZONE, dateStyle: "long", timeStyle: "short" }).format(date) : "";
}
export function noteListDate(note: BoardNote, now: Date) {
  const date = noteDate(note);
  if (!date) return "";
  return new Intl.DateTimeFormat("en-US", calendarDay(date) === calendarDay(now)
    ? { timeZone: NOTE_TIME_ZONE, hour: "numeric", minute: "2-digit" }
    : { timeZone: NOTE_TIME_ZONE, month: "numeric", day: "numeric", year: "2-digit" }).format(date);
}
export function groupBoardNotes(notes: BoardNote[], now: Date) {
  const groups = new Map<string, BoardNote[]>();
  const today = Date.parse(calendarDay(now));
  for (const note of [...notes].sort((a, b) => (noteDate(b)?.getTime() ?? 0) - (noteDate(a)?.getTime() ?? 0))) {
    const date = noteDate(note);
    const age = date ? (today - Date.parse(calendarDay(date))) / 86400_000 : NaN;
    const label = !date ? "Notes" : age === 0 ? "Today" : age === 1 ? "Yesterday" : age > 1 && age <= 30 ? "Previous 30 Days"
      : new Intl.DateTimeFormat("en-US", { timeZone: NOTE_TIME_ZONE, month: "long", ...(calendarDay(date).slice(0, 4) !== calendarDay(now).slice(0, 4) ? { year: "numeric" as const } : {}) }).format(date);
    const group = groups.get(label) ?? [];
    group.push(note); groups.set(label, group);
  }
  return [...groups].map(([label, items]) => ({ label, items }));
}
