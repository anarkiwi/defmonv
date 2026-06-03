#!/usr/bin/env python3
"""Apply the defMonV Phase 1 (MIDI clock master) patch to a vendored defMON
Kick Assembler source.

defMON's "ScannerBoy" sync bit-bangs CIA2 port B ($DD01) from the player tick:
$0C/$04 while playing (PB2=run, PB3=clock), $00 on stop. With a Vessel on the
user port, every byte written to $DD01 in output mode is transmitted as MIDI, so
those writes are replaced with MIDI real-time messages:

  $0B2E  clock-high (per main tick)  ->  send MIDI Clock ($F8)
  $0B46  clock-low  (per sub-frame)  ->  suppressed (no stray MIDI byte)
  $0CCA  stop (stop_playback)        ->  send MIDI Stop ($FC)
  $81E5  play-from-start (F3) tail   ->  jsr-free redirect to a stub that sends
                                         MIDI Start ($FA)

Why this shape:
  * defMON already sets $DD03=$FF (port B all-output) and PA2=1 at cold boot, so
    no port setup is needed.
  * Clock and Stop are patched in place (`lda #imm`), needing no extra RAM. They
    are plain stores, safe in any banking — including the boot-time stop_playback
    call that runs before defMON banks KERNAL out.
  * defMON keeps KERNAL banked out ($01=$35) in the editor, so the Start stub can
    live just above the image at $E787 (RAM there) and is reached only from the
    F3 play handler, never from the KERNAL-in boot path.

The patch is exact string replacements (each must match once) plus an appended
stub, so it fails loudly if the base drifts.
"""
import sys

REPLACEMENTS = [
    (
        "clock-high $0B2E: MIDI Clock ($F8)",
        "l_5:                       lda  #$0C    // $0B2E",
        "l_5:                       lda  #$F8    // $0B2E  [defMonV: MIDI Clock]",
    ),
    (
        "clock-low $0B46: suppress ScannerBoy write",
        "                           sta  CIA2_PRB    // $0B46",
        "                           .byte $EA, $EA, $EA    // $0B46  [defMonV: suppress clock-low]",
    ),
    (
        "stop $0CCA: MIDI Stop ($FC)",
        "                           lda  #$00    // $0CCA",
        "                           lda  #$FC    // $0CCA  [defMonV: MIDI Stop]",
    ),
    (
        "play-from-start $81E5: redirect to MIDI Start stub",
        "                           jmp  statusline_print_bare_return    // $81E5",
        "                           jmp  defmonv_start    // $81E5  [defMonV: MIDI Start]",
    ),
    (
        # splash_build_date_string ($0FF2): post_load_startup prints the first 8
        # screen codes to the seqED status line (the build date '20201008').
        # Replace those 8 with 'DEFMONV ' so the user sees the variant name;
        # leave the (undisplayed) 6 build-time digits.
        "version stamp $0FF2: show DEFMONV on the seqED status line",
        "        .byte $32, $30, $32, $30, $31, $30, $30, $38, $32, $32, $30, $31, $34, $33    // $0FF2",
        "        .byte $04, $05, $06, $0D, $0F, $0E, $16, $20, $32, $32, $30, $31, $34, $33    // $0FF2  [defMonV: 'DEFMONV ' version stamp]",
    ),
]

# Appended at the end, in RAM just above the image ($0800-$E786). Reached only
# from the editor (KERNAL banked out), so this address is RAM when it runs.
APPEND = """

// ──────────────────────────────────────────────────────────────────────
// defMonV Vessel support (Phase 1: MIDI clock master)
// ──────────────────────────────────────────────────────────────────────
// Tail of the F3 "play from start" handler: emit MIDI Start, then continue to
// the original status-line repaint.
*=$E787
defmonv_start: {
                           lda  #$FA          // MIDI Start
                           sta  CIA2_PRB
                           jmp  statusline_print_bare_return
}
"""


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: patch_vessel.py <in.asm> <out.asm>")
    base = open(sys.argv[1]).read()
    if "defmonv_start" in base:
        sys.exit("patch error: base already patched")
    src = base
    for desc, old, new in REPLACEMENTS:
        n = src.count(old)
        if n != 1:
            sys.exit(f"patch error: {desc!r}: expected 1 match, found {n}")
        src = src.replace(old, new)
    src += APPEND
    open(sys.argv[2], "w").write(src)
    print(f"patched {sys.argv[1]} -> {sys.argv[2]} ({len(REPLACEMENTS)} sites)")


if __name__ == "__main__":
    main()
