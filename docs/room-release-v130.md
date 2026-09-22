# Room media v130

Source: `lofi-room-cathode-glm53f-city-v130-cubby-monitor-pan.blend`, derived from the approved v129 lamp lighting study. Previous Blender versions and shipped media remain untouched.

## Changes

- Floor lamp height reduced from 2.082 m to 1.388 m (exactly one third shorter). Shade/base shape and width retained; stem, bulb, contours, and lights move together. Downlight energy softened for its shorter throw.
- Approved v129 dim indoor fills, real upward/downward soft lamp lighting, short grouped outline flashes, amber cues, and retained weather lightning are included in all new footage.
- Monitor camera starts at the unchanged greeting pose, tucks toward the cubby at `(1, -2.8, 2.35)`, then follows a straight descending segment into the blank screen. The curve joins the straight segment with continuous position and speed, and ends at rest. The chair-clearance audit reports about 0.119 m.
- The endpoint lies inside the black display framing, allowing the existing boot reveal to take over without showing a residual bezel.
- Shelf geometry, project textures, interaction coordinates, and diploma camera framing are unchanged.

## Coordinated release

All seven movies are 1920×1080, 24 fps; idle is 240 frames, monitor clips 121 each, and shelf/diploma clips 73 each. The v129 12 fps study is not used on the website.

New media live in `public/room/v130/`; switch the room, shelf plates, and cursor mask to this revision together only after all assets pass validation. Previous assets remain available for rollback.

Shelf/diploma camera timing is separated from the ambient clock. Their approach is ambient frames 1–73, close-up still/background at 73, and return at 73–145. On returning, the idle movie should seek to six seconds (ambient frame 145). Monitor return ends at ambient frame 241, which matches idle time zero. Retain the decoded-frame gate and departing overlays to avoid loading flashes.

The renderer samples the authored camera into a separate, non-animated capture camera before changing the ambient frame. Directly overriding the animated camera is not sufficient: Blender reevaluates its animation at render time. Rejected timing-test frames are retained separately and are not shipped.

The hover mask must use effective object material slots, including v129 quick-flash materials. Clearing mesh materials alone would leave OBJECT-linked overrides active. Regenerate after geometry changes.

## Verification

- `audit_room_v130.py`: unchanged greeting, exact endpoint, straight-line error, chair clearance, lamp-height ratio, and lightning keys.
- `render_room_v130.py`: writes only new output directories; existing frames are resume points, so do not reuse them after changing render/animation settings.
- `encode_room_v130.ps1`: staged full-quality media; no app URL switch until ready.
- Source regression tests preserve deferred downloads, reduced motion, cursor glow, and return-frame retention.

Completed release checks: 97 tests pass and the production build succeeds. All seven H.264 clips decode without errors at 1920×1080/24 fps. The ten-second idle is 869,341 bytes, with a 78,520-byte greeting poster and 228,969-byte hover mask.

Browser checks confirm the v130 media/plates/mask are loaded together, all three destinations enter and return successfully, and every sampled return frame is covered by either its decoded movie or the retained departing view. Monitor returns seek idle to zero; project/diploma returns seek to six seconds. The project approach endpoint, still, and return start have identical source pixels; the project return endpoint matches the corresponding idle frame at SSIM 0.999994.

Work remains local; do not deploy automatically.
