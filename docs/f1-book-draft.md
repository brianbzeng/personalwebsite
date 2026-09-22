# F1 report book — style approval draft

Local review: `/review/report-book`. Also available through the original top-shelf book.

The complete report is converted into 234 pages. The source's ten chapters, methods,
reproduction notes, nine figures, nine tables, all 418 decision citations, and the
920-row audit link remain. Wide tables are reflowed as labeled entries, not truncated.
The original source prose and figure PNG bytes are preserved. The title and linked
contents use book typography, with chapter-based figure numbers 2.1 through 8.1.

Each figure stays within one page, never crossing the gutter. Charts are top-aligned
at natural aspect ratio, with captions directly below and following prose using
remaining space. Paragraphs may continue onto the next page without losing markup;
subsection headings move with their following paragraph. White image backgrounds
blend into the paper through CSS multiply compositing; original files remain intact.
At rest, hover, and during turns, artwork stays on the same thin paper meshes; an
invisible semantic DOM layer preserves accessible text and interactive links without
changing the visible typography. A native dialog gives full-size figures and reflowable single-page
reading; on mobile, wide figures scroll horizontally rather than shrinking labels.
Both hardcover boards remain visible around the open paper stack.
The front cover carries the report title. The repetitive bottom-left footer is removed.
First/last and contents navigation rapidly turn every intervening leaf (each leaf
has two numbered faces), keeping controls busy until landing. Reduced motion skips
the rapid animation. Hover reveals the actual neighboring page behind the folded
corner. Turning continues that same diagonal fold across the sheet toward the spine,
with a rounded bend and flat flap rather than rotating the entire page as a board.

Content lives outside Blender:

- `scripts/convert_f1_book.py <downloaded-source.html>` extracts and verifies the source.
- `public/books/f1/source.json` records full blocks, source hash, and figure hashes.
- `public/books/f1/page.css` defines the 600 × 750 page typography.
- `public/books/f1/paginate.js` measures DOM overflow, splits long blocks, resolves links.
- `node scripts/render_f1_book.mjs` regenerates the manifest and page JPEG textures from
  the local preview. This needs the locally available `@playwright/test` runtime.
- Bump `BOOK_REVISION` in `app/components/reportBook.ts` whenever pages are regenerated.
- `public/books/f1/book.json` controls page count, contents, source links and HTML.
- The viewer loads only needed page textures, keeping at most ten texture entries;
  it does not download all page images on entry. Closing rewinds in up to five quick
  groups before the cover closes and the book returns.

Source report: https://brianbzeng.github.io/f1-stewarding-analysis/reports/the_cost_of_discretion_study_v2.html

Validation: independent full text/cell/link audit; all generated pages measured for
overflow; original figure bytes hash-checked; nine full-size figures visually inspected;
desktop contents/turning and mobile reflow checked; horizontal touch panning verified.
Original chart colors have not been redesigned or certified for accessibility. Some
source yellow/white marks have limited contrast. The source's Chapter 8 phrase “in the
opposite direction from the favoritism claim” is retained, not silently edited; it
deserves a separate editorial check against the reported lower British sanction rate.

The generic Data Science book conversion skill is intentionally NOT created yet.
Create it only after Brian approves the style and conversion behavior.
