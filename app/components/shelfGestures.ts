export function swipeCubbyDirection(dx: number, dy: number): -1 | 1 | null {
  if (Math.abs(dy) < 48 || Math.abs(dy) < Math.abs(dx) * 1.4) return null;
  return dy < 0 ? 1 : -1; // Same direction as scrolling a document by touch.
}
export function wheelPixels(delta: number, mode: number, height: number) {
  return delta * (mode === 1 ? 16 : mode === 2 ? height : 1);
}
export function swipeBookDirection(dx: number, dy: number): -1 | 1 | null {
  if (Math.abs(dx) < 48 || Math.abs(dx) < Math.abs(dy) * 1.4) return null;
  return dx < 0 ? 1 : -1;
}
