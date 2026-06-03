# Using defMONV

defMONV is [defMON](https://defmon.vandervecken.com) with Vessel MIDI-clock
support. Load `defmonv.d64` (or the packed `.prg`) on a C64 with a
[Vessel](https://github.com/anarkiwi/vessel) on the user port and it runs as the
normal defMON tracker — but playing now transmits MIDI Clock / Start / Stop out
of the Vessel. The seqED status line reads **`DEFMONV`** (instead of defMON's
build date) so you can tell at a glance you're on the Vessel build.

![defMONV seqED screen](defmonv-seqed.png)

The screen above is the **seqED** (pattern) view: three voice columns
(`VOC0`/`VOC1`/`VOC2`) of per-step notes, the arranger column on the right, and
the `DEFMONV` stamp on the status line at the bottom.

## Transport keys — what they send over Vessel

These are defMON's normal transport keys; the right column is what defMONV adds.

| Key | defMON action | MIDI sent via Vessel |
|-----|---------------|----------------------|
| **F3** | Play from song start | **Start** (`$FA`), then **Clock** (`$F8`) every tick |
| **F1** | Play from cursor | **Clock** (`$F8`) every tick (no fresh Start) |
| **F7** | Stop | **Stop** (`$FC`) |
| **F5** | Toggle follow-play | — |
| **SHIFT+F1/F3/F5/F7** | Multispeed ×1/×2/×4/×8 (player tick rate) | changes the **Clock** rate |

MIDI **Clock** streams continuously while the player runs, at defMON's tick
rate, so the multispeed keys change the outgoing clock tempo. (defMON's old
ScannerBoy sync used the same sites; defMONV emits real MIDI instead.)

## Everyday editor keys

defMONV does not change the editor — these are stock defMON. See
[`USER_GUIDE.md`](https://github.com/anarkiwi/undefmon/blob/main/USER_GUIDE.md)
in undefmon for the full keychord reference.

| Key | Action |
|-----|--------|
| **RUNSTOP** | Toggle focus between seqED (pattern) and seqLIST (arranger) |
| **LEFTARROW** | Open sidTAB (instrument table); exit it |
| **CRSR up/down** | Move the step cursor (SHIFT reverses) |
| **CRSR left/right** | Move between voice columns |
| **SPACE** | Write "no note" / step through a prompt |
| **[ / ] / =** | Mute / unmute voice 1 / 2 / 3 |
| **LSHIFT+X** | Open the disk menu (load / save) |
| **CTRL+G** | Cursor to step 0 |

## Hooking up

1. Connect a Vessel to the C64 user port and a MIDI cable from the Vessel to the
   device you want to sync (drum machine, synth, DAW interface, …).
2. Set the slave device to **external MIDI clock**.
3. Load defMONV and press **F3** — the slave receives Start + Clock and follows
   defMON's tempo; **F7** stops it.
