# Safari Hub staging

Built and approved September 29, 2026. Deployed to brianbzeng.com with the accompanying Hub bridge; see production-release.md for version and rollback IDs.

## Review

- Room launch: http://127.0.0.1:3001/review/safari-room?hubPreview=local
- Hub desktop: http://127.0.0.1:3001/review/safari-desktop?app=hub&hubPreview=local
- Normal monitor: http://127.0.0.1:3001/review/safari-desktop?hubPreview=local
- Local Hub must run on port 4178. Without the loopback-only preview query, Safari uses gallery.brianbzeng.com.

New opens Safari above Terminal above Notes. As of November 16, 2026, normal monitor visits open only Terminal; other applications remain available on demand. Production home and desktop enable the feature.

The November 16 investigation found the deployed gallery bundle missing the `bz-hub-v1` bridge. The gallery returns HTTP 200, but Safari's handshake times out. Repair belongs in the separate gallery deployment; this website release does not overwrite that project.

## Behavior

Safari includes window controls, route-aware history and reload, sidebar favorites, session reading list, copy-link sharing and page zoom. Its single toolbar centers the read-only address against the entire window; tab UI is removed. The embedded page is the actual Hub, not a recreated page.

The Hub bridge lives in the separate report-gallery repository. It accepts the exact parent origins https://brianbzeng.com, http://127.0.0.1:3001 and http://localhost:3001 only, checks parent/source identity, and requires embed=safari. Both sides validate messages. The iframe cannot navigate the top window. Featured/report links open https://gallery.brianbzeng.com/featured in a new browser tab directly from the click gesture. The dedicated repository link opens https://github.com/brianbzeng/f1-stewarding-analysis similarly. Both use noopener,noreferrer; other external links remain blocked. The sandbox permits popups to escape its restrictions so these standalone destinations function normally.

The app is named Safari throughout its desktop icon, Dock, menus and window controls. The embedded Hub alone is rendered with grayscale(1); the actual Hub site and newly opened tabs retain their original colors.

## Validation

- Website: 280 tests passed; TypeScript and production build passed.
- Hub: 17 tests passed; production build passed.
- Browser: local iframe handshake/content, sidebar navigation, back/forward across reload, reading list, overview, fullscreen/minimize, normal monitor window order, and landscape phone layout checked.
- Browser automation could not activate targets inside the cross-origin iframe. New-tab report and repository handling is covered by executable Hub tests, but needs a manual browser check.

## Approval / release

Review the staging appearance and manually click a greeting photo, Featured and an index report. After approval, deploy the Hub bridge and promote the website staging feature through the normal release process. Do not publish these changes merely because the build passes.
