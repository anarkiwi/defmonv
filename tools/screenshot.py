#!/usr/bin/env python3
"""Boot defMONV in asid-vice and render the seqED screen to a PNG.

Uses vice-driver's DISPLAY_GET framebuffer grab: VICE's own rendered
bitmap (border, sprites, any video mode) recoloured through the live
PALETTE_GET palette, so docs show exactly what the emulator draws
(including the DEFMONV version stamp). PNG writing is pure stdlib via
vice_driver.display.write_png — no Pillow dependency.

Requires Docker + asid-vice and defmon-driver / vice-driver on PYTHONPATH.
Usage: python3 tools/screenshot.py [out.png] [defmonv.d64]
"""
import sys
import time
from pathlib import Path

from defmon_driver._smoke_support import smoke_session
from vice_driver.display import parse_display_response, parse_palette_response
from vice_driver.screen import parse_screen_response


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/defmonv-seqed.png")
    d64 = Path(sys.argv[2] if len(sys.argv) > 2 else "defmonv.d64").resolve()
    with smoke_session(d64, port=6502, prefix="shot-") as s:
        time.sleep(1.0)  # let the seqED screen settle
        snap = parse_display_response(s.bm.display_get())
        palette = parse_palette_response(s.bm.palette_get())
        out.parent.mkdir(parents=True, exist_ok=True)
        w, h = snap.save_png(str(out), palette)
        print(f"wrote {out} ({w}x{h} px)")
        print(parse_screen_response(s.bm.screen_get()).text())


if __name__ == "__main__":
    main()
