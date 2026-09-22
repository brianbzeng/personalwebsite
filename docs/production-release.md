# Production release workflow

Brian approved the current room site and v158 shelf-motion staging on 2026-09-11.
The main site now uses the same approved playback and return animations; review mode still suppresses automatic project redirects.

## Verified destination

- Domain: https://brianbzeng.com
- Existing Cloudflare Worker: `brian-zeng-portfolio`
- Explicit config: `wrangler.production.jsonc`
- The `.openai/hosting.json` Sites demo is separate and has no custom domain attached. Do not publish the demo as a substitute for brianbzeng.com.
- Previous production version (rollback reference): `97cd41b9-1e54-4035-ac80-f9668cb1259f`.
- Published approved room version: `c5cde935-90f8-4089-86c3-5d7ed2e51e04` (2026-09-11). Cloudflare confirmed successful upload and custom-domain deployment.

## Future changes

Vinyl cue close-up anchoring fix (2026-09-16): Brian requested a fix and direct production publication. Selection clears old projected bounds before changing context, and inspection targets are withheld until extraction/opening/gallery motion has settled. This prevents stationary cues from freezing over the original shelf slot. Stationary layout, immediate input dismissal and two-second idle fades remain unchanged. Version: `668c479a-79ed-42ba-8434-483e93ffa2a2`; rollback reference: `0bb2362a-5bb7-4680-8e15-905e67570327`. All 85 focused checks, build and dry run passed. Browser screenshot verified Drag above the final cover, Flip at its edge and Redirect beside the exposed disc. Home/desktop return 200, live principal JS/CSS hashes match local build, Spotify remains ready. Existing production configuration preserved.

Stationary cues and immediate interaction dismissal (2026-09-16): Brian explicitly requested direct production publication. Removed cue rocking/floating/bouncing, froze each scene's complete settled layout, and stopped geometry polling once placed. Pointer/touch presses, wheel gestures, navigation/activation keys, and resize dismiss immediately and consume the cue visit; idle two-second fade timing remains unchanged. Version: `0bb2362a-5bb7-4680-8e15-905e67570327`; rollback reference: `d6a239df-3499-4cec-a237-227a850ea87c`. All 81 focused checks, build and dry run passed. Typecheck reports only the two pre-existing VinylPortfolio Vector2 errors. Live home/desktop return 200, current JS/CSS hashes match local build, and Spotify remains ready. Domain, bindings, vars and secrets preserved.

Approved cue fade-in (2026-09-16): promoted `cueFadeIn` to production home after explicit approval. Cues now use matching 450ms intro/outro fades and a 1100ms hold, for exactly 2000ms active visible lifetime after the existing invisible settling delay. Version: `d6a239df-3499-4cec-a237-227a850ea87c`; rollback reference: `2679504d-cbfb-40e5-bc15-b03ae1674f5b`. All 72 focused checks, build, and dry run passed. Home/desktop return 200, live home includes the promoted flag, and the three principal client bundles match local SHA-256 hashes. Spotify remains ready; production redirect behavior, domain, bindings, vars and secrets are preserved.

Approved cue refinements and top-cubby consistency (2026-09-16): promoted `refinedCues` and `coherentBooks` after explicit approval. Includes half-length arrow tails, slower/subtler motion, two-second cue holds, fixed right-side enlarged scroll guidance, corrected photo labels, visit/learned-navigation memory, stable book cue, and six v160 still/pan assets. Version: `2679504d-cbfb-40e5-bc15-b03ae1674f5b`; rollback reference: `de1da3d6-5c98-4a5c-bd8e-c205ddfecf61`. All 67 focused checks, build, and dry run passed. Home/desktop return 200; live home contains both promoted flags; all six v160 media and three principal client bundles match local SHA-256 hashes. Spotify status remains ready. No review redirect suppression or replay controls enabled on production; domain, bindings, vars and secrets preserved.

Approved mobile layout and Manic activity cues (2026-09-16): Brian requested reversing the book close-up swipe arrows and then publishing the approved staging work. Previous-page cue now points left; next-page cue points right, without changing gesture behavior. Main room and direct desktop routes enable the approved responsive layout; room/shelf cues are enabled, workstation cues remain removed, and replay controls remain review-only. Published version: `de1da3d6-5c98-4a5c-bd8e-c205ddfecf61`; rollback reference: `ceebd94b-74dc-490b-8917-b7709934a311`. All 57 focused tests, build, and explicit production dry run passed. Live home/desktop return 200, all four Manic fonts and the three principal client bundles match local SHA-256 hashes, and Spotify reports ready. Production redirects, existing vars/secrets, D1 binding, and custom domain are preserved.

Approved photo-consistency update (2026-09-15): promoted v159 photo still/background and direct/adjoining camera pans from the corrected sleeve/player scene. Published version: `ceebd94b-74dc-490b-8917-b7709934a311`; rollback reference: `0d230168-f146-4d29-b4ca-5af2b4feb38f`. All 26 focused tests, production build and dry run passed; six live asset hashes match local, home/desktop return 200, Spotify remains ready. Existing vars/secrets, D1 binding and custom domain preserved. Review-only redirect suppression is separate from corrected-media selection.

Latest approved update (2026-09-15): full-width camera/still/shelf framing, matching handoff crop, viewport-safe book navigation, progress-only centered desktop boot screen, and decorative Spotify equalizer without listen-along hover/link. Record popup behavior retained as requested. Published version: `0d230168-f146-4d29-b4ca-5af2b4feb38f`; previous version: `1c55baf7-3524-4541-a441-7ea08cced0d0`. All 44 focused tests, production build, and Wrangler dry run passed. Deployment preserved existing vars/secrets and D1 binding.

1. Implement candidate changes in local review/staging routes, keeping the approved main experience unchanged.
2. Show Brian the staging result and obtain explicit approval.
3. Promote only approved changes, build, and check the production artifact.
4. Deploy with the explicit production config only when publishing is requested. Verify Cloudflare's terminal status and domain responses.

The deployment consists of `dist/server` and `dist/client`. Preserve raw Blender authoring and rendered frames locally; do not upload the `blender/outputs` directory. Runtime files beneath `public/review` are required by the live record player and photos and must not be excluded just because their path contains `review`.

## Spotify production support

Brian explicitly requested production live Spotify support on 2026-09-11. The dedicated D1 binding and canonical HTTPS OAuth flow are configured, with owner-only credential writes and production disconnect blocked. The room uses the real live feed for the approved speaker loop. See `spotify-widget.md` for setup and safeguards. Brian must register the HTTPS callback in the Spotify app and complete the production authorization; do not migrate local tokens automatically.
