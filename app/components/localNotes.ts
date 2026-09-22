import { BOARD_NOTES, BOARD_SYNC, type BoardNote } from "./notesData.ts";

/**
 * Visitor-local Notes state. The published board remains the first-load content;
 * every edit, creation, folder, or deletion lives in this browser only. Unedited
 * board copies refresh whenever BOARD_SYNC/BOARD_NOTES change; edited copies and
 * locally created notes are never overwritten.
 */

export type StoredNote = BoardNote & { edited?: boolean };
export type LocalFolder = { id: string; name: string };
export type LocalNotesState = {
  version: 1;
  sync: number;
  notes: StoredNote[];
  folders: LocalFolder[];
  removedBoardIds: string[];
  nextId: number;
  nextFolder: number;
};

export const NOTES_STORAGE_KEY = "bz-notes-v1";
export const isLocalNoteId = (id: string) => id.startsWith("local-");

export function freshLocalNotes(): LocalNotesState {
  return {
    version: 1, sync: BOARD_SYNC,
    notes: BOARD_NOTES.map((note) => ({ ...note, blocks: note.blocks.map((block) => ({ ...block })) })),
    folders: [], removedBoardIds: [], nextId: 1, nextFolder: 1,
  };
}

/** Pull published board updates into a stored state without losing local work. */
export function mergeBoardInto(state: LocalNotesState): LocalNotesState {
  const notes = [...state.notes];
  for (const board of BOARD_NOTES) {
    const index = notes.findIndex((note) => note.id === board.id);
    if (index === -1) {
      if (!state.removedBoardIds.includes(board.id)) notes.push({ ...board, blocks: board.blocks.map((block) => ({ ...block })) });
      continue;
    }
    if (!notes[index].edited) notes[index] = { ...board, blocks: board.blocks.map((block) => ({ ...block })) };
  }
  const boardIds = new Set(BOARD_NOTES.map((note) => note.id));
  const kept = notes.filter((note) => isLocalNoteId(note.id) || boardIds.has(note.id) || note.edited);
  return { ...state, sync: BOARD_SYNC, notes: kept };
}

function parseState(raw: string | null): LocalNotesState | null {
  if (!raw) return null;
  try {
    const data = JSON.parse(raw) as Partial<LocalNotesState>;
    const shaped = data
      && Array.isArray(data.notes)
      && data.notes.every((note) => note && typeof note.id === "string" && typeof note.title === "string" && Array.isArray(note.blocks))
      && Array.isArray(data.folders ?? [])
      && (data.folders ?? []).every((folder) => folder && typeof folder.id === "string" && typeof folder.name === "string")
      && Array.isArray(data.removedBoardIds ?? []);
    if (!shaped) return null;
    return {
      version: 1,
      sync: typeof data.sync === "number" ? data.sync : 0,
      notes: (data.notes as StoredNote[]).map((note) => ({ ...note, edited: note.edited === true })),
      folders: (data.folders as LocalFolder[]).slice(),
      removedBoardIds: (data.removedBoardIds as string[]).filter((id) => typeof id === "string"),
      nextId: Math.max(1, Number(data.nextId) || 1),
      nextFolder: Math.max(1, Number(data.nextFolder) || 1),
    };
  } catch {
    return null;
  }
}

export function loadLocalNotes(): LocalNotesState {
  let state: LocalNotesState | null = null;
  try {
    state = typeof localStorage === "undefined" ? null : parseState(localStorage.getItem(NOTES_STORAGE_KEY));
  } catch { /* storage unavailable (private mode): fall back to the published board */ }
  const base = state ?? freshLocalNotes();
  return state && (state.sync !== BOARD_SYNC) ? mergeBoardInto(base) : base;
}

export type SaveResult = { ok: true } | { ok: false; error: string };
export function saveLocalNotes(state: LocalNotesState): SaveResult {
  try {
    localStorage.setItem(NOTES_STORAGE_KEY, JSON.stringify(state));
    return { ok: true };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "storage unavailable" };
  }
}

/** Quota guard before embedding a picked file as a data URL. */
export const ATTACHMENT_LIMIT_BYTES = 750 * 1024;
export function readAttachment(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    if (file.size > ATTACHMENT_LIMIT_BYTES) { reject(new Error(`"${file.name}" is larger than the 750 KB local-notes limit.`)); return; }
    const reader = new FileReader();
    reader.onload = () => typeof reader.result === "string" ? resolve(reader.result) : reject(new Error("Could not read the file."));
    reader.onerror = () => reject(new Error("Could not read the file."));
    reader.readAsDataURL(file);
  });
}
