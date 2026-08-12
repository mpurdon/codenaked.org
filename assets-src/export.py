#!/usr/bin/env python3
"""Export every web asset from assets-src/poster-original.png.

Run from the project root:  python3 assets-src/export.py

The poster is DIE-CUT: ~18% of its pixels are fully transparent and the outline
is irregular (the neon bloom fades out to nothing). Two rules follow:

  1. Never .convert("RGB") it. That drops the mask and exposes the arbitrary RGB
     data stored underneath the transparent pixels as a rectangular background.
  2. Resize premultiplied. PIL resamples colour and alpha independently, so on a
     straight-alpha image those hidden colours bleed into the edge pixels and
     leave a halo around the cut.

JPEG and the iOS icon cannot carry alpha, so those two are explicitly composited
onto the page background colour instead.
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets-src" / "poster-original.png"
IMG = ROOT / "public" / "images"
PUB = ROOT / "public"

BG = (8, 6, 13)  # --raw-ink #08060d, the page background

poster = Image.open(SRC).convert("RGBA")
W, H = poster.size


def resize_rgba(im, size):
    """Premultiply -> resize -> unpremultiply, so the cut edge stays clean."""
    a = np.asarray(im, dtype=np.float64)
    alpha = a[..., 3:4] / 255.0
    prem = np.concatenate([a[..., :3] * alpha, a[..., 3:4]], axis=-1)
    small = np.asarray(
        Image.fromarray(prem.round().astype(np.uint8), "RGBA").resize(size, Image.LANCZOS),
        dtype=np.float64,
    )
    sa = small[..., 3:4] / 255.0
    rgb = np.divide(small[..., :3], sa, out=np.zeros_like(small[..., :3]), where=sa > 0)
    out = np.concatenate([rgb.clip(0, 255), small[..., 3:4]], axis=-1)
    return Image.fromarray(out.round().astype(np.uint8), "RGBA")


def flatten(im):
    bg = Image.new("RGB", im.size, BG)
    bg.paste(im, mask=im.getchannel("A"))
    return bg


def webp(im, out, q):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as t:
        im.save(t.name)
        subprocess.run(["cwebp", "-q", str(q), "-alpha_q", "100", "-m", "6",
                        "-quiet", t.name, "-o", str(out)], check=True)
    Path(t.name).unlink(missing_ok=True)
    print(f"  {out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB  {im.size}  alpha preserved")


print(f"source {W}x{H} RGBA")

# --- poster: alpha preserved, native width needs no resample --------------
webp(poster, IMG / "poster.webp", 82)
webp(resize_rgba(poster, (640, round(640 * H / W))), IMG / "poster-640.webp", 80)

# --- og card: JPEG has no alpha, composite on the page background ---------
band = flatten(resize_rgba(poster.crop((0, 40, W, 580)), (1200, 630)))
band.save(IMG / "og-card.jpg", quality=86, optimize=True, progressive=True)
print(f"  images/og-card.jpg  {(IMG / 'og-card.jpg').stat().st_size // 1024} KB  flattened on #08060d")

# --- icons: crop of the two characters ------------------------------------
# This crop is NOT fully opaque, so the favicon keeps its alpha. FASTOCTREE is
# the one PIL quantizer that survives an alpha channel; it takes the icon from
# ~170 KB to ~40 KB, and the lost colour depth is invisible at tab size.
icon = poster.crop((296, 436, 736, 876))
resize_rgba(icon, (256, 256)).quantize(
    colors=128, method=Image.Quantize.FASTOCTREE).save(PUB / "favicon.png", optimize=True)
# iOS composites apple-touch-icon onto black regardless, so match the site.
flatten(resize_rgba(icon, (180, 180))).save(PUB / "apple-touch-icon.png", optimize=True)
print(f"  favicon.png  {(PUB / 'favicon.png').stat().st_size // 1024} KB  alpha preserved")
print(f"  apple-touch-icon.png  {(PUB / 'apple-touch-icon.png').stat().st_size // 1024} KB  flattened")
