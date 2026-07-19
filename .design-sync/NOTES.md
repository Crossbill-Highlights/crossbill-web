# design-sync notes — crossbill-frontend

Repo-specific gotchas for future syncs. Read this before re-running.

## What this DS is
- `crossbill-frontend` is a **Vite app**, not a packaged component library — there is **no `dist/`** and **no Storybook**. The sync runs in the **package shape, synth-entry mode**.
- The synced "design system" is a **hand-scoped** set of ~24 reusable primitives under `frontend/src/components/` (buttons, inputs, cards, typography, dialogs, layout, animations). It is NOT every component in the app.
- UI stack: **MUI (`@mui/material`) + Emotion (CSS-in-JS)** with a custom theme at `frontend/src/theme/theme.ts`. Styles are injected at runtime → `[CSS_RUNTIME]` is expected and non-blocking.

## Build wiring (why the config looks the way it does)
- **Custom entry**: `frontend/.ds-sync-entry.mts` (committed, referenced via `cfg.entry`). It re-exports the scoped components + a `DSProvider` (MUI `ThemeProvider` + `theme` + `CssBaseline`) + `export * from '@/theme/Icons'` (so authored previews can use themed icons). Written with `createElement` (no JSX) so it needs no tsconfig discovery. Component set is pinned via `cfg.componentSrcMap`; with a real `--entry` there is no auto-scan, so the map IS the component list.
- **PKG_DIR must resolve to `frontend/`** — that's why the entry file lives under `frontend/` (the `--entry` walk stops at the first named `package.json`). Root `package.json` is an npm **workspace** (`workspaces: ["frontend"]`); deps are **hoisted to repo-root `node_modules`** and `frontend/node_modules` is empty → pass **`--node-modules ./node_modules`** (repo root), not the frontend one.
- **`cfg.provider` = `DSProvider`** — every preview needs the MUI theme or it renders unstyled/blank.
- **Fonts**: the brand font **Lora** is a remote Google Font (loaded via `<link>` in `index.html`). `cfg.cssEntry` → `frontend/.ds-sync-fonts.css` (committed) mirrors that `@import` so it reaches the styles.css closure and previews render in Lora. This means designs load Lora at runtime from `fonts.googleapis.com` (accepted `[FONT_REMOTE]`-style pattern) — not shipped in the bundle.

## Preview authoring rules (learned in the verify loop)
- Previews import components/icons **only from `'crossbill-frontend'`**. **Never import `@mui/material` / `@mui/icons-material` directly** in a preview — that bundles a second, theme-less MUI copy and the preview renders unstyled. Use plain `<div>` + inline styles for layout glue.
- Themed icons come from the bundle via the entry's `export * from '@/theme/Icons'` (semantic names: EditIcon, DeleteIcon, CopyIcon, TagIcon, etc.).
- Theme reference colors for glue: ink/primary `#43311E`, amber base `#685A4B`, muted `#78716c`, border `#e7e5e4`. Brand font: `"Lora", Georgia, serif`.
- **Overlay/wide components need `cfg.overrides`** (already set): dialogs (`CommonDialog`, `ConfirmationDialog`) → `cardMode: single` + viewport; wide/layout (`ContentWithSidebar`, `PageContainer`, `HighlightCard`, `TagInput`, `ProgressBar`, `CommonDialogHorizontalNavigation`) → `single`/`column`.

## Floor-card components (intentionally NOT authored — "presentational only" scope)
- **RHFTextField** — needs a `react-hook-form` FormProvider context; can't render standalone.
- **AppBar** — needs `@tanstack/react-router` + `AuthContext`.
- **ScrollToTopButton** — self-hides at `scrollY 0` (`Zoom in={false}` → unmounts), so it renders **nothing** statically. Genuinely un-authorable as a static card. Left as floor card.
- **FadeInOut** — a `motion.div` **enter animation** (`initial={{opacity:0}}` → `animate`). `package-capture.mjs` freezes the page clock (`page.clock.setFixedTime`), so the time-driven tween never advances and the content stays at `opacity:0` (blank). Cannot be fixed from preview glue. (Contrast `Collapsable`, same motion lib, which uses `AnimatePresence initial={false}` and mounts children at their visible target values, so it captures fine.) Left as floor card. To author it later: unfreeze/advance the capture clock, or give the component an `initial={false}` path.
These pass the gate as deliberate floor cards. Authoring RHFTextField/AppBar later would require wiring their providers (react-hook-form / router+auth) into `cfg.provider` — the "all ~22 best effort" scope, which the user declined.

## Known render warns (triaged as legitimate)
- `[RENDER_THIN]` on **Spinner** (`Sizes` cell) — confirmed benign: three amber `CircularProgress` (24/40/64) render fine; the check trips because thin SVG arcs with no text collapse the measured output. Graded `good`.
- Any `[RENDER_THIN]` on small/icon components (icon buttons, `ProgressBar` bars) — inherent to the element, not a defect.
- All authored previews use `cardMode: column` (see `cfg.overrides`) — they compose at fixed widths wider than the default grid cell, so column mode (one story per full-width row) is required to avoid `[GRID_OVERFLOW]`.
- Lora shows as `[FONT_REMOTE]` (loads at runtime from Google Fonts) — expected, see build wiring above.

## Re-sync risks (watch-list)
- **Remote font dependency**: Lora is fetched at runtime from Google Fonts. If claude.ai/design CSP ever blocks it, designs fall back to serif. No local font is shipped.
- **Synth-entry `.d.ts` are weaker**: props come from the TS checker over app source, not a published types package. Generics (e.g. `RHFTextField`) may emit thin `.d.ts`.
- **Mock data in `HighlightCard`/`TagInput` previews** is inlined and shaped against `frontend/src/api/generated/model` (Highlight/TagInBook). If those models change materially, re-check those previews.
- **`.ds-sync-entry.mts` re-exports specific paths** — if a scoped component moves or is renamed, update both `cfg.componentSrcMap` and the entry file.
- The whole scope is hand-curated; new reusable primitives added to the app are NOT auto-included — extend `componentSrcMap` + the entry to add them.
