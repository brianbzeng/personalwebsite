export const PACIFIC_ZONE = "America/Los_Angeles";

export function pacificClock(now: Date) {
  const format = (options: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("en-US", { timeZone: PACIFIC_ZONE, ...options }).format(now);
  return {
    time: format({ hour: "numeric", minute: "2-digit" }),
    date: format({ month: "numeric", day: "numeric", year: "numeric" }),
    fullDate: format({ weekday: "long", month: "long", day: "numeric", year: "numeric" }),
    zone: format({ timeZoneName: "short" }).split(" ").at(-1)!,
    dayKey: new Intl.DateTimeFormat("en-CA", { timeZone: PACIFIC_ZONE, year: "numeric", month: "2-digit", day: "2-digit" }).format(now),
  };
}

export type WindowFrame = { x: number; y: number; width: number; height: number };
export type WindowMode = "normal" | "maximized" | "fullscreen" | "left" | "right";
export const INITIAL_FRAME: WindowFrame = { x: .20, y: .10, width: .62, height: .68 };
// Brian's compact Notes reference, relative to the desktop workarea.
export const INITIAL_NOTES_FRAME: WindowFrame = { x: 194 / 1918, y: 288 / 877, width: 888 / 1918, height: 540 / 877 };
export const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

export function terminalInitialFrame(instance: number): WindowFrame {
  const offset = ((Math.max(1, instance) - 1) % 6) * .025;
  return fitFrame({ ...INITIAL_FRAME, x: INITIAL_FRAME.x + offset, y: INITIAL_FRAME.y + offset });
}

export function fitFrame(frame: WindowFrame, minWidth = .25, minHeight = .2): WindowFrame {
  const width = clamp(frame.width, Math.min(minWidth, 1), 1);
  const height = clamp(frame.height, Math.min(minHeight, 1), 1);
  return { width, height, x: clamp(frame.x, 0, 1 - width), y: clamp(frame.y, 0, 1 - height) };
}

export function fitFrameToArea(frame: WindowFrame, area: { width: number; height: number }, minimum: { width: number; height: number }): WindowFrame {
  if (![area.width, area.height].every((value) => Number.isFinite(value) && value > 0)) return fitFrame(frame);
  return fitFrame(frame, Math.min(minimum.width / area.width, 1), Math.min(minimum.height / area.height, 1));
}

export function modeFrame(mode: WindowMode, normal: WindowFrame): WindowFrame {
  if (mode === "maximized" || mode === "fullscreen") return { x: 0, y: 0, width: 1, height: 1 };
  if (mode === "left" || mode === "right") return { x: mode === "left" ? 0 : .5, y: 0, width: .5, height: 1 };
  return normal;
}

export function calendarMonth(year: number, month: number) {
  const first = new Date(Date.UTC(year, month, 1));
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(Date.UTC(year, month, index - first.getUTCDay() + 1));
    return { key: day.toISOString().slice(0, 10), date: day.getUTCDate(), current: day.getUTCMonth() === month };
  });
}
