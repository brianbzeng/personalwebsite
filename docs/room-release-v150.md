# Direct books camera and paper interaction — v150

Local-only release; no deployment. Existing v149 room footage and approved cover artwork remain unchanged.

- Blender source: `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v150-direct-book-camera.blend`.
- Editable camera `CAM_BooksApproach_v150`: frames 1–73 approach, 97–169 direct return. Created by `blender/direct_books_v150.py` from v149 without overwriting it.
- New media: `public/room/v150/books-in.mp4` and `books-out.mp4`, each 73 frames, 1920×1080, 24 fps, H.264 CRF18. No rerender of unchanged clips.
- Raw entry-end and exit-start frames exactly match the v149 books still (SSIM 1.0); room endpoints match idle at >0.99999 SSIM.
- Books shortcut and upper-shelf hotspot enter directly. Exiting books settles geometry and returns directly, retaining the shelf until the first decoded video frame. Photos retain their existing supported route through records.
- Removed shelf hover/drag instructional hints, retaining navigation, project titles, accessible labels, and loading/status text.
- A single click on the inspected sleeve or exposed record snaps to the opposite face; dragging remains available. Opening projects remains a separate control.
- Web book uses zero-thickness double-sided 32×24 paper meshes. Bottom corner hover/focus curls are localized; clicking turns a leaf in 900ms. Previous/next arrows are replaced by transparent accessible hit areas. Reduced motion changes spread immediately.
- Verified forward/back page turns, direct books returns via both entry routes, single-click vinyl flip, 390px reduced-motion layout, all 140 tests, and production build. Detailed player and binding approval prototypes remain isolated at `/review/player-books`.
