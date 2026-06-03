#!/usr/bin/env python3
"""Static verification of the assembled defMonV image: assert every Phase 1
patch site holds the expected bytes. Runs in CI with no emulator, so a bad or
drifted patch fails the build.

Usage: verify_image.py build/defmonv-static.prg
"""
import sys

# (label, address, expected bytes). "??" matches any single byte.
CHECKS = [
    ("clock-high: lda #$F8 / sta $DD01", 0x0B2E, "a9 f8 8d 01 dd"),
    ("clock-low: suppressed (3x NOP)", 0x0B46, "ea ea ea"),
    ("stop: lda #$FC / sta $DD01", 0x0CCA, "a9 fc 8d 01 dd"),
    ("play-from-start: jmp $E787", 0x81E5, "4c 87 e7"),
    ("defmonv_start: lda #$FA / sta $DD01 / jmp", 0xE787, "a9 fa 8d 01 dd 4c ?? ??"),
    ("version stamp: 'DEFMONV ' screen codes", 0x0FF2, "04 05 06 0d 0f 0e 16 20"),
]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: verify_image.py <static.prg>")
    p = open(sys.argv[1], "rb").read()
    load = p[0] | (p[1] << 8)
    body = p[2:]
    if load != 0x0800:
        sys.exit(f"unexpected load address ${load:04x} (want $0800)")
    ok = True
    for label, addr, expected in CHECKS:
        want = expected.split()
        got = ["%02x" % body[addr - load + i] for i in range(len(want))]
        match = all(w == "??" or w == g for w, g in zip(want, got))
        print(f"[{'OK' if match else 'FAIL'}] ${addr:04x} {' '.join(got)}  {label}")
        ok = ok and match
    if not ok:
        sys.exit("verify_image: patch sites do not match")
    print("verify_image: all Phase 1 patch sites OK")


if __name__ == "__main__":
    main()
