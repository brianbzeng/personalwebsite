export type ReportPage = { kind: string; chapter: string; html: string; anchors: string[]; figure?: string; src?: string; caption?: string; alt?: string; figureSide?: number };
export type ReportBook = { title: string; subtitle: string; author: string; source: string; pages: ReportPage[]; anchors: Record<string, number>; contentsPage: number; width: number; height: number };
let request: Promise<ReportBook> | undefined;
// Bump together with repagination so an existing tab cannot mix old page numbers
// with newly rendered textures cached at the same asset paths.
const BOOK_REVISION = '20260910-title-github-v5';
export function loadReportBook() {
  return request ??= fetch(`/books/f1/book.json?v=${BOOK_REVISION}`).then(r => { if (!r.ok) throw new Error('Book unavailable'); return r.json() as Promise<ReportBook>; }).catch(error => { request = undefined; throw error; });
}
export const pageTextureURL = (page: number) => `/books/f1/pages/${String(page).padStart(3, '0')}.jpg?v=${BOOK_REVISION}`;
export const boundedSpread = (page: number, pageCount: number) => Math.max(0, Math.min(Math.ceil(pageCount / 2) - 1, Math.floor(page / 2)));
