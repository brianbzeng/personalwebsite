# Brian Zeng — Portfolio

An interactive room portfolio for Brian Zeng's data products and modeling work,
with a desktop terminal, live Spotify widget, project vinyls, a data science
report book, and photographs. Built with React, TypeScript, vinext, and Three.js.

## Local development

Requires Node.js 22.13 or newer and pnpm.

```bash
pnpm install
pnpm dev
pnpm build
```

The room entry point is `app/page.tsx`; the computer view is `/desktop`.
Staging and review routes live under `app/review`. Visual changes are reviewed
before production release; see `AGENTS.md` and `docs/production-release.md`.

Production uses `wrangler.production.jsonc` for `brianbzeng.com`. Local bindings
also use `.openai/hosting.json`; that file is not the production deployment target.
Keep credentials in ignored local environment files or production secret storage,
never in Git. Spotify setup is documented in `docs/spotify-widget.md`.

Optimized assets in `public/room`, `public/review`, and `public/books` are required
by the website. Blender authoring scripts are included, but raw renders and local
source assets under `blender/outputs` and `blender/assets` stay outside Git,
apart from the small approved-cover and scene-audit fixtures used by tests.

Run the regression suite with `node --test tests/*.test.mjs`.
