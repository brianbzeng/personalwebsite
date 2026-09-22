# Shelf close sequence and speaker draft

Local preview only. Blender source and approved room media remain v150/v149.

## Shelf changes

- Returning an opened report rewinds every completed spread at 160 ms per leaf, closes the cover, then returns the closed book. Its inspection position is held during closure. Room exit uses the same sequence before its camera handoff.
- Desktop wheel/trackpad gestures and mobile vertical swipes navigate the three cubbies. Wheel down/swipe up moves lower; the reverse moves higher. A gesture triggers only one move; momentum, boundaries, multitouch, horizontal drags, and inspection mode are guarded.
- Reduced motion skips the page rewind and closes/returns without tweening.

## Music effect awaiting approval

- `/review/speaker-loop` shows a separately composited grayscale loop of notes and waves at both projected woofer centers. Normal homepage room has no music overlay until approval.
- Wave revision: 18 distinct smooth closed irregular rings, independently shuffled per speaker with no repeats until each pool is exhausted. Rings expand concentrically from the visible large-woofer front caps, without sideways drift. Shape changes occur at invisible emission boundaries; notes and playback fades remain unchanged.
- Preview loop/pause controls are explicitly simulated. Live Spotify uses the existing read-only `/api/spotify` integration and existing backend cache/authorization; no new scopes or playback controls.
- Playing requires a ready, active, fresh feed with a song. Paused, disconnected, failed, hidden, or stale states disable it. Opacity fades for 600 ms, then child loops freeze. Room Pause motion and reduced-motion preference disable the effect.
- Existing refresh limits remain: one minute active, five minutes idle. Consequently live changes are polling-based, not instantaneous or beat-synchronized.
- Real endpoint reported paused/idle during verification. A mocked live playing→paused response test verified the opacity transition and cleanup, without changing Spotify playback.

Verified browser book sequence, forward/back desktop wheel navigation, actual emulated-touch swipes at 390px, no shelf navigation during vinyl inspection, simulated loop fades, and live response handling. All 145 tests and production build pass.
