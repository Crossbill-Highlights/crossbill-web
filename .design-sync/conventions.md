## Building with Crossbill

Crossbill is a **Material UI (MUI v6) + Emotion** design system for a book-reading / highlights / flashcards app. Its look is a warm editorial theme: **Lora serif** type on a light stone background, with an **amber-brown** primary. You compose MUI components and the Crossbill components below, and you style with MUI's `sx` prop and theme tokens — **there are no utility CSS classes**.

### Setup — wrap everything in `DSProvider`
Every screen MUST be wrapped in `DSProvider` (exported from the package). It supplies the MUI `ThemeProvider` with the Crossbill theme (Lora typography, amber palette, 12px radius) plus `CssBaseline`. Without it, components fall back to unstyled MUI defaults and the wrong font.

```jsx
import { DSProvider, SectionTitle, HighlightCard, SearchBar, CommonDialog } from 'crossbill-frontend'

export default function Screen() {
  return (
    <DSProvider>
      <SectionTitle showDivider>Highlights</SectionTitle>
      <SearchBar onSearch={(q) => {}} placeholder="Search highlights…" />
    </DSProvider>
  )
}
```

### Styling idiom — MUI `sx` + theme tokens (no class names)
Style with the `sx` prop, referencing theme tokens by string — never invent CSS classes or hex codes when a token exists:
- **Palette:** `primary.main` (#43311E), `primary.light` (#685A4B), `secondary.main` (#78716c), `text.primary`, `text.secondary`, `background.default` (stone #fafaf9), `background.paper`.
- **Spacing:** numeric `sx` units are ×8px — `sx={{ p: 2, mt: 3 }}`.
- **Type:** use MUI `<Typography variant="h1..h6 | body1 | body2">`; the family is Lora serif app-wide. Headings via `SectionTitle`.
- **Radius/shadow:** `shape.borderRadius` is 12; buttons are pill-shaped (radius 24, `textTransform: none`). Use `sx={{ boxShadow: 2 }}` for the standard card elevation.

```jsx
<Box sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 3, boxShadow: 1 }}>
  <Typography variant="h3" sx={{ color: 'primary.main' }}>Chapter 3</Typography>
  <Typography variant="body2" sx={{ color: 'text.secondary' }}>12 highlights · 3 notes</Typography>
</Box>
```

### Components available (import from `crossbill-frontend`)
- **buttons:** `AIActionButton` (text + AI sparkle), `IconButtonWithTooltip` (pass an `icon`), `UnlinkButton`, `ScrollToTopButton`
- **inputs:** `SearchBar` (debounced), `TagInput` (multi-select chips), `RHFTextField` (react-hook-form field — needs a `FormProvider`)
- **cards:** `HighlightCard` (takes a `highlight` object), `HoverableCardActionArea`, `MetadataRow` (bullet-separated `items[]`)
- **typography:** `SectionTitle` (`showDivider`, `component`)
- **dialogs:** `CommonDialog`, `CommonDialogTitle`, `ConfirmationDialog`, `DialogTabs`, `DialogToolbar`, `ProgressBar`, `CommonDialogHorizontalNavigation`
- **layout:** `AppBar` (needs router + auth context), `PageContainer`, `ContentWithSidebar`
- **animations:** `Collapsable`, `FadeInOut`, `Spinner`

Icons are re-exported with semantic names (`EditIcon`, `DeleteIcon`, `CopyIcon`, `TagIcon`, `BookmarkIcon`, `AIIcon`, …) — use them for `IconButtonWithTooltip`/`DialogToolbar` so they inherit the theme.

### Where the truth lives
Read each component's `<Name>.d.ts` (its props contract) and `<Name>.prompt.md` (usage) before composing. The theme tokens above are the styling source of truth — prefer them over hard-coded values.
