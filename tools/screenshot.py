#!/usr/bin/env python3
"""Boot defMONV in asid-vice and render the seqED screen to a PNG.

Renders the live VIC text screen (screen codes + per-cell colour + the active
character bitmap + background/border) to a true-colour image, so docs show
exactly what the user sees (including the DEFMONV version stamp).

Requires Docker + asid-vice, defmon-driver / vice-driver on PYTHONPATH, and PIL.
Usage: python3 tools/screenshot.py [out.png] [defmonv.d64]
"""
import sys
import time
from pathlib import Path

from PIL import Image

from defmon_driver._smoke_support import smoke_session
from vice_driver.screen import parse_screen_response

# Pepto C64 palette.
PALETTE = [
    (0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189),
    (139, 63, 150), (85, 160, 73), (64, 49, 141), (191, 206, 114),
    (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80),
    (120, 120, 120), (148, 224, 137), (120, 105, 196), (159, 159, 159),
]
SCALE = 2
BORDER = 16  # chars-area border in pixels (pre-scale)


def render(snap, scale=SCALE):
    cols, rows = snap.cols, snap.rows
    bg = PALETTE[snap.bg_color[0] & 0x0F]
    border = PALETTE[snap.border_color & 0x0F]
    w, h = cols * 8, rows * 8
    img = Image.new("RGB", (w + 2 * BORDER, h + 2 * BORDER), border)
    px = img.load()
    for r in range(rows):
        for c in range(cols):
            sc = snap.screen[r * cols + c]
            fg = PALETTE[snap.color[r * cols + c] & 0x0F]
            glyph = snap.charset[sc * 8 : sc * 8 + 8]
            for y in range(8):
                bits = glyph[y]
                for x in range(8):
                    color = fg if (bits >> (7 - x)) & 1 else bg
                    px[BORDER + c * 8 + x, BORDER + r * 8 + y] = color
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    return img


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/defmonv-seqed.png")
    d64 = Path(sys.argv[2] if len(sys.argv) > 2 else "defmonv.d64").resolve()
    with smoke_session(d64, port=6502, prefix="shot-") as s:
        time.sleep(1.0)  # let the seqED screen settle
        snap = parse_screen_response(s.bm.screen_get())
        out.parent.mkdir(parents=True, exist_ok=True)
        render(snap).save(out)
        print(f"wrote {out} ({snap.cols}x{snap.rows} chars)")
        print(snap.text())


if __name__ == "__main__":
    main()
