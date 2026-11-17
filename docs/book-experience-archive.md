# Book experience archive

On 2026-09-30 Brian requested retiring the interactive books and top-cubby navigation, while retaining all implementation and assets for possible reuse.

`app/components/shelfState.ts` is the restoration switch: `BOOK_EXPERIENCE_ENABLED` is false. The room menu, hotspot, cues and pan prewarming honor it. Shelf entry and every movement path clamp to `FIRST_CUBBY` (Records); book plates are not preloaded. The report overlay is lazy-loaded. Decorative books remain part of existing room/shelf artwork.

No book sources, Blender authoring work, page images, recordings, or models were deleted. Book-only review entries cannot enter the archived cubby; the old player/books prototype is unavailable while the switch is off. Re-enable the switch and verify the retained review routes before restoring production.
