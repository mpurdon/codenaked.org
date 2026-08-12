# codenaked.org

Single-poster landing page. Astro 6 static site, **zero JavaScript shipped**,
no Tailwind — custom-property design tokens, system font stack. Mirrors the
matthewpurdon.me / chuckstalker.com stack, minus everything that page doesn't
need (no fonts to self-host, no inline scripts, no theme switcher).

The entire site is the poster art plus a one-line footer. Resist growing it.

## Stack facts

- Astro 6, static output to `dist/`, `inlineStylesheets: 'always'` — CSS ships
  inside `<head>`, so first paint needs only the HTML document.
- Styles: `src/styles/tokens.css` (two-layer tokens: raw palette → semantic
  aliases; build UI against the semantic layer only), `base.css` (reset + the
  whole site). Palette values are eyedropped from the poster.
- Fonts: system UI stack. Nothing self-hosted, no CDNs. The only text on the
  site is one uppercase letter-spaced footer line.
- JS: none. The copyright year is stamped at build time in `Layout.astro`, so
  it refreshes on every deploy without a client script.
- Icons: the footer's GitHub mark is inline SVG (octicons `mark-github-16`)
  filled with `currentColor`, so it inherits the link colour and hover state
  and costs no extra request. Keep it that way — the page should fetch nothing
  but the HTML document and the poster.

## The height chain

The poster fills the viewport minus the footer. That only works because every
ancestor has a resolvable height — if you touch this, re-check all three:

1. `body { height: 100svh }` — a *definite* height, not `min-height`. With
   `min-height` the poster's `max-height: 100%` has nothing to resolve against
   and the footer gets pushed below the fold.
2. `.stage { flex: 1; min-height: 0 }` — `min-height: 0` lets the flex child
   shrink below its content size.
3. `.stage { grid-template: minmax(0, 1fr) / minmax(0, 1fr) }` — bare `auto`
   tracks size to the poster's 1024×1536 max-content and overflow narrow
   viewports, which makes the image's `max-width: 100%` look broken.

`100svh` (small viewport height) is deliberate: mobile browser chrome must not
be able to push the footer off-screen.

## The poster is die-cut — do not flatten it

`assets-src/poster-original.png` is RGBA with a real mask: ~18% of its pixels
are fully transparent and the outline is irregular, because the neon bloom
fades out to nothing rather than stopping at a rectangle. Two consequences,
both of which have already been gotten wrong once:

- **Never `.convert("RGB")` it.** PIL drops the alpha channel rather than
  compositing, which exposes the arbitrary RGB data stored *underneath* the
  transparent pixels — it renders as a rectangular background that looks
  deliberate but isn't.
- **Never give the poster `box-shadow` or `border-radius`.** Those trace the
  rectangular bounding box and draw a visible edge in empty space. Glow comes
  from `filter: drop-shadow()`, which follows the alpha channel.

Resizing must be premultiplied — PIL resamples colour and alpha independently,
so on straight alpha the hidden colours bleed into edge pixels and halo the
cut. `resize_rgba()` in the export script handles this.

## Asset drop-in contract

`assets-src/` holds the original art (git-tracked, NOT shipped);
`public/images/` holds the optimized exports. To swap in new poster art,
overwrite `assets-src/poster-original.png` and run `python3
assets-src/export.py` from the project root — it derives every other asset from
that one file. Needs `pillow`, `numpy`, and `cwebp` on PATH.

| Output | What | Alpha |
|---|---|---|
| `public/images/poster.webp` | 1024w, cwebp q82 `-alpha_q 100` | **preserved** |
| `public/images/poster-640.webp` | 640w, cwebp q80 | **preserved** |
| `public/images/og-card.jpg` | 1200×630 q86, crop of source rows 40–580 (the title band) — the poster is 2:3 and cannot letterbox into a social card | flattened on `#08060d`; JPEG has no alpha |
| `public/favicon.png` | 256², FASTOCTREE 128-colour, crop `(296, 436, 736, 876)` | **preserved** — that crop is not fully opaque |
| `public/apple-touch-icon.png` | 180², same crop | flattened; iOS composites on black regardless |

`FASTOCTREE` is the only PIL quantizer that survives an alpha channel — the
default `MEDIANCUT` silently drops it. It takes the favicon from ~170 KB to
~30 KB with no visible loss at tab size.

There is deliberately no PNG poster fallback; it cost 1.7 MB and WebP is
universal. If the art changes aspect ratio, update the `width`/`height`
attributes and the `sizes` value in `src/pages/index.astro` to match.

## Local verification

`npm run build && npm run preview`. Note that headless Chrome on macOS
**clamps its window to a 500px minimum width** and silently crops the
screenshot to whatever `--window-size` asked for — so a narrow screenshot
looks like a horizontal-overflow bug when the layout is fine. To check real
phone widths, load the preview URL inside a fixed-width `<iframe>` in a
throwaway HTML file and screenshot that instead.

## Deploy

Push to `main` → GitHub Actions → Cloudflare Pages (project `codenaked-org`).
Manual fallback: `npm run deploy`. Repo secrets required by the workflow:
`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
