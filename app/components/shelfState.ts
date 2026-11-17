export const CUBBIES = ["Books", "Records", "Camera & photographs"] as const;
// Archived, not deleted: re-enable this to restore the book experience.
export const BOOK_EXPERIENCE_ENABLED = false;
export const FIRST_CUBBY = BOOK_EXPERIENCE_ENABLED ? 0 : 1;
export const BLANK_SPREADS = 3;
export type ShelfSelection = number | "book" | "photos" | null;
export function canSelectRecord(index: number) { return Number.isInteger(index) && index >= 0 && index < 5; }
export function adjacentCubby(cubby: number, direction: -1 | 1) { return Math.max(FIRST_CUBBY, Math.min(2, cubby + direction)); }
export function nextSpread(spread: number, direction: -1 | 1, count = BLANK_SPREADS) { return Math.max(0, Math.min(count - 1, spread + direction)); }
