export type DesktopWindowId = `terminal-${number}` | "recycle" | "notes" | "f1" | "help";
export type ManagedWindow = {
  id: DesktopWindowId; app: "terminal" | "recycle" | "notes" | "f1" | "help"; number: number;
  minimized: boolean; z: number; initialCommand?: string;
};
export type DesktopSession = {
  windows: ManagedWindow[]; active: DesktopWindowId | null;
  nextTerminal: number; restoreIds: DesktopWindowId[]; restoreActive: DesktopWindowId | null;
};
export const INITIAL_DESKTOP_SESSION: DesktopSession = {
  windows: [{ id: "terminal-1", app: "terminal", number: 1, minimized: false, z: 10 }],
  active: "terminal-1", nextTerminal: 2, restoreIds: [], restoreActive: null,
};
export type WindowAction =
  | { type: "new-terminal"; command?: string }
  | { type: "open-trash" | "open-notes" | "open-f1" | "open-help" | "show-desktop" | "close-terminals" | "hide-terminals" | "blur" }
  | { type: "focus" | "minimize" | "close"; id: DesktopWindowId };

export function frontWindow(windows: ManagedWindow[]) {
  return windows.filter((item) => !item.minimized).sort((a, b) => b.z - a.z)[0]?.id ?? null;
}
export function preferredTerminal(state: DesktopSession) {
  return state.windows.find((item) => item.app === "terminal" && item.id === state.active)
    ?? state.windows.filter((item) => item.app === "terminal").sort((a, b) => b.z - a.z)[0];
}
export function managedWindowTitle(item: ManagedWindow) {
  return item.app === "terminal" ? `Terminal ${item.number}` : item.app === "notes" ? "Notes" : item.app === "f1" ? "F1 Forecast" : item.app === "help" ? "Help" : "Trash";
}
export function desktopWindowReducer(state: DesktopSession, action: WindowAction): DesktopSession {
  const topZ = Math.max(9, ...state.windows.map((item) => item.z)) + 1;
  if (action.type === "new-terminal") {
    const item: ManagedWindow = { id: `terminal-${state.nextTerminal}`, app: "terminal", number: state.nextTerminal, minimized: false, z: topZ, initialCommand: action.command };
    return { ...state, windows: [...state.windows, item], active: item.id, nextTerminal: state.nextTerminal + 1 };
  }
  if (action.type === "open-trash" || action.type === "open-notes" || action.type === "open-f1" || action.type === "open-help") {
    const id = action.type === "open-notes" ? "notes" : action.type === "open-f1" ? "f1" : action.type === "open-help" ? "help" : "recycle";
    const exists = state.windows.some((item) => item.id === id);
    return { ...state, active: id, windows: exists
      ? state.windows.map((item) => item.id === id ? { ...item, minimized: false, z: topZ } : item)
      : [...state.windows, { id, app: id, number: 0, minimized: false, z: topZ }] };
  }
  if (action.type === "blur") return { ...state, active: null };
  if (action.type === "show-desktop") {
    const visible = state.windows.filter((item) => !item.minimized).map((item) => item.id);
    if (visible.length) return { ...state, windows: state.windows.map((item) => ({ ...item, minimized: true })), active: null, restoreIds: visible, restoreActive: state.active };
    const windows = state.windows.map((item) => ({ ...item, minimized: !state.restoreIds.includes(item.id) }));
    return { ...state, windows, active: windows.some((item) => item.id === state.restoreActive && !item.minimized) ? state.restoreActive : frontWindow(windows), restoreIds: [], restoreActive: null };
  }
  if (action.type === "close-terminals" || action.type === "hide-terminals") {
    const windows = action.type === "close-terminals" ? state.windows.filter((item) => item.app !== "terminal")
      : state.windows.map((item) => item.app === "terminal" ? { ...item, minimized: true } : item);
    return { ...state, windows, active: frontWindow(windows), restoreIds: state.restoreIds.filter((id) => windows.some((item) => item.id === id)) };
  }
  if (!("id" in action) || !state.windows.some((item) => item.id === action.id)) return state;
  if (action.type === "focus") return { ...state, active: action.id, windows: state.windows.map((item) => item.id === action.id ? { ...item, minimized: false, z: topZ } : item) };
  const windows = action.type === "close" ? state.windows.filter((item) => item.id !== action.id)
    : state.windows.map((item) => item.id === action.id ? { ...item, minimized: true } : item);
  return { ...state, windows, active: state.active === action.id ? frontWindow(windows) : state.active, restoreIds: state.restoreIds.filter((id) => id !== action.id) };
}
