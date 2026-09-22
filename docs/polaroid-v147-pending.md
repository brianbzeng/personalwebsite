# Polaroid integration — completed v147

Saved `lofi-room-cathode-glm53f-city-v147-personal-polaroids.blend` from v146 using `blender/apply_polaroids_v147.py`. Images 1–4 map onto D,C,B,A (viewer left-to-right). All existing object transforms and Polaroid frames are preserved. Four images are packed into the blend. The local review has a Polaroids tab with a separate inspection camera; the original scene camera is unchanged.

The generative edits were rejected because they changed facial details and lettering. Brian explicitly approved standard non-AI cropping and grayscale conversion. `blender/prepare_polaroid_photos_v147.ps1` uses GDI+ grayscale and bicubic resizing only. Original copies and SHA256/crop metadata are retained under `blender/assets/polaroids/v147-originals/`.

Originals (in user attachment order) live at `C:/Users/BRIANZ~1/AppData/Local/Temp/`:

1. `codex-clipboard-0e41dd1d-f495-45a2-bb18-455e86ee2f83.png` (768×1024): square crop x0,y256,size768.
2. `codex-clipboard-454b3b51-2f48-4a9c-ad2d-56e8c80289ce.png` (1024×769): square crop x220,y119,size650.
3. `codex-clipboard-ce5c4898-97d9-49a2-9e76-15de83ef53aa.png` (1024×769): square crop x120,y0,size769.
4. `codex-clipboard-50701592-9440-4e70-b13b-a932caf160b5.png` (768×1024): square crop x0,y170,size768.

Textures are 512px square at `public/room/polaroid-art/v147/photo-1.png` through `photo-4.png`. Browser QA confirmed grayscale, upright orientation, correct order and preserved frames. Existing overlap partially covers photos 2 and 4; card positions were deliberately preserved. Screenshot: `blender/outputs/review-v147/browser-polaroids.png`. Ten regression checks pass. Production room footage remains v137, with no rerecording or deployment performed.
