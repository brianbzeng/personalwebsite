export const MAC_TERMINAL_PROMPT = "brian@Mac ~ % ";
export const DOCK_REVEAL_FRACTION = .08;

export type TerminalGrid = { columns: number; rows: number };
export function terminalGridSize(width: number, height: number, cellWidth: number, lineHeight: number): TerminalGrid | null {
  if (![width, height, cellWidth, lineHeight].every((value) => Number.isFinite(value) && value > 0)) return null;
  return { columns: Math.max(1, Math.floor(width / cellWidth)), rows: Math.max(1, Math.floor(height / lineHeight)) };
}

export function isInDockRevealRegion(pointerY: number, top: number, height: number) {
  if (!Number.isFinite(pointerY) || !Number.isFinite(top) || !Number.isFinite(height) || height <= 0) return false;
  return pointerY >= top + height * (1 - DOCK_REVEAL_FRACTION) && pointerY <= top + height;
}

// Fixed rest-position centers keep magnification stable as neighboring icons move.
export function dockLayout(pointer: number | null, count: number, size = 52, gap = 10) {
  const centers = Array.from({ length: count }, (_, index) => index * (size + gap) + size / 2);
  const scales = centers.map((center) => {
    if (pointer === null || !Number.isFinite(pointer)) return 1;
    const distance = Math.min(1, Math.abs(pointer - center) / (size * 2.5));
    return 1 + .55 * (1 + Math.cos(distance * Math.PI)) / 2;
  });
  const widths = scales.map((scale) => size * (scale - 1));
  const expansion = widths.reduce((sum, width) => sum + width, 0);
  let accumulated = -expansion / 2;
  const offsets = widths.map((width) => {
    const offset = accumulated + width / 2;
    accumulated += width;
    return offset;
  });
  return { scales, offsets, expansion };
}
