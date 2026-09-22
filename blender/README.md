# Interactive room Blender archive

This directory contains the latest authored Blender source and the exterior
weather proof used by the portfolio work.

- `lofi-room-rebuild-v08-rainy-suburb.blend` — Blender 5.2 LTS source scene.
- `rebuild-v08-rainy-suburb-preview.gif` — short room-camera preview of the
  rainy neighborhood loop.
- `rebuild-v08-rainy-suburb-report.json` — scene handoff metadata.
- `rebuild_suburban_exterior_v07.py` — reproducible exterior rebuild script.
- `build_cathode_cinema_reference.py` — builds the standalone procedural
  monochrome Cathode Cinema reference scene from the recovered coordinate
  tables.
- `stylize_lofi_room_cathode.py` — saves a non-destructive monochrome Cathode
  material pass of the existing room while preserving its layout and targets.
  Version 39 removes the modeled second-room/neighborhood assembly, inserts
  bright procedural grayscale grass planes inset to the window openings (no
  source photo), removes the shelf-top plant and floor staging slabs, squares
  the floor grid, tucks the right shelf flush to the wall, converts the record
  player arm to the grayscale palette, and adds animated white edge ink with a
  moving scan/glint across the room. The floor grid is seven complete 0.8-unit
  squares across the 5.6-unit floor, with seams aligned to the floor edges.
  The pulsar-map frame is redrafted as a thin-line radial signal diagram with
  a sparse set of thin, physically modeled white rods and a central hub placed
  toward the left side of the dark frame backing; all perpendicular dashes and
  endpoint caps are removed, and no source image or pasted inset is used.
  The diploma frame is fitted with the supplied diploma artwork at its native
  centered in its native aspect over matching muted paper-white fill quads that
  reach every edge of the actual frame opening. The diploma and fill are one
  coplanar mesh flush to the frame, with no image-stretching; the artwork is
  packed into the blend and remapped to a subdued grayscale material.
  Monitor housings, stands, and bases use the room's mid-gray while the screen
  remains on the intentional bright-display treatment.
  The shelf bottom cubby uses two equal storage boxes with inset lids that clear
  the side walls, the second-lowest cubby is a continuous end-to-end run of
  earlier-scale upright books with varied skinny/thick spines, and the highest
  cubby's contents are swapped with the third cubby from the bottom. The camera
  now has a smaller compact body seated on the cubby floor, a circular modeled
  lens ring, raised flash and viewfinder, and shutter button; the camera, globe,
  polaroids, and record player are tucked behind the shelf front plane. The two
  vinyl supports are hollow triangular frames with modeled inner cutouts. The
  camera lens barrel and glass overlap at the body front and share one
  centerline, with the outer ring removed so the lens reads as one connected
  assembly.
  The four polaroids are thin modeled card/photo pairs arranged in a loose,
  offset stack with separated layers rather than intersecting or perfectly
  aligned; their card borders are white and their inset image panels are dark
  for clear separation. The leftmost vinyl sleeve leans into and contacts the
  left triangular holder.
- `cathode_lib.py`, `cathode_geo.py`, `cathode_emit.py`, `cathode_scene.py`,
  `cathode_feed.py` — shared support modules used by those two scripts.

The scene keeps the three web interaction targets (`TARGET_MONITOR`,
`TARGET_VINYLS`, and `TARGET_DIPLOMA`) and a 240-frame, 24 fps master timeline.
The original source scene retains its modeled exterior for archival comparison.
The v39 Cathode output uses two inset procedural grass planes with
the opaque window glass hidden in the render so the field reads as outside;
flowing outline is keyed across frames 1–240 and the preview render is captured
at frame 48. The website should use an exported compressed WebM/H.264 version
of the loop for runtime delivery; the GIF is included as a lightweight visual
reference.
