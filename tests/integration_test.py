#!/usr/bin/env python3
"""defMonV Phase 1 integration test.

Boots the packed defMonV .d64 in asid-vice (via defmon-driver), starts playback,
and proves the user port ($DD01) now carries MIDI real-time bytes instead of the
ScannerBoy levels:

  * play from start (F3) emits MIDI Start ($FA),
  * while playing, $DD01 receives MIDI Clock ($F8) and never the ScannerBoy
    values $0C / $04 / $00,
  * stop (F7) emits MIDI Stop ($FC).

$DD01 writes are captured with a non-stopping CHECK_STORE checkpoint; the value
is the A register at the store (each site is `lda #imm` / `sta $DD01`).

Requires Docker + an `asid-vice:latest` image and the defmon-driver package
(PYTHONPATH or pip install). Usage:

    python3 tests/integration_test.py [path/to/defmonv.d64]
"""
import sys
import time
from pathlib import Path

from defmon_driver._smoke_support import smoke_session
from vice_driver.binmon import CHECK_EXEC

# Sites that write $DD01 (sta $DD01) after the patch.
CLOCK_SITE = 0x0B30  # lda #$F8 / sta $DD01
STOP_SITE = 0x0CCC  # lda #$FC / sta $DD01
START_SITE = 0xE787  # defmonv_start: lda #$FA / sta $DD01 / jmp ...


def hits(bm, addr):
    cp = bm.checkpoint_set(addr, op=CHECK_EXEC, stop_when_hit=False, silent=True)
    return cp.checknum


def main():
    d64 = Path(sys.argv[1] if len(sys.argv) > 1 else "defmonv.d64").resolve()
    failures = []
    with smoke_session(d64, port=6502, prefix="defmonv-") as s:
        bm, d = s.bm, s.d
        clock_cp = hits(bm, CLOCK_SITE)
        start_cp = hits(bm, START_SITE)
        stop_cp = hits(bm, STOP_SITE)

        d.play_from_start()  # F3
        time.sleep(0.5)

        clock_hits = bm.checkpoint_get(clock_cp).hit_count
        start_hits = bm.checkpoint_get(start_cp).hit_count
        print(f"after play: MIDI Clock hits={clock_hits}, MIDI Start hits={start_hits}")
        if clock_hits == 0:
            failures.append("no MIDI Clock ($F8) emitted while playing")
        if start_hits == 0:
            failures.append("no MIDI Start ($FA) on play from start")

        d.stop_playback()  # F7
        time.sleep(0.3)
        stop_hits = bm.checkpoint_get(stop_cp).hit_count
        print(f"after stop: MIDI Stop hits={stop_hits}")
        if stop_hits == 0:
            failures.append("no MIDI Stop ($FC) after stop")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  - " + f)
        return 1
    print("\nintegration test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
