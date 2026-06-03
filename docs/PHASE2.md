# defMonV Phase 2 — external MIDI clock (Vessel as slave)

Phase 1 makes defMON a MIDI clock **master** (it sends Clock/Start/Stop). Phase 2
is the inverse: drive defMON's playback from an **incoming** MIDI clock via
Vessel's NMI-on-MIDI-clock feature, the way
[M64 SID Wizard](https://github.com/M64GitHub/sid-wizard-vessel) does. This is a
larger, riskier change and is scoped — not implemented — here.

## What it requires

1. **Configure Vessel for NMI sync** (the SID Wizard sequence), once at startup
   or when sync mode is enabled:
   * `FD 00` (Reset), `FD 06 FF FF` (status mask = all real-time messages),
     `FD 04 09` (config flags: NMI enabled + NMI-status-only),
   * CIA2 ICR `$DD0D <- $90` to enable the `/FLAG`-driven NMI on the C64 side.
2. **Re-point the interrupt.** defMON is internally clocked by **CIA2 Timer-A**
   (tick rate = `(cia2_timer_lo|hi) × sub_frame_count`). For external clock, the
   timer NMI must be disabled and Vessel's `/FLAG` NMI used instead; the handler
   reads the buffered MIDI bytes (input mode: count, then bytes), advances the
   player on `$F8`, and starts/stops on `$FA`/`$FC`.

## The hard part

defMON's player NMI does **sub-frame** SID updates — several NMIs per musical
tick, paced by the timer, to spread SID register writes across the frame for
timing precision. An incoming MIDI clock is 24 PPQN at musical rate, a
completely different cadence than the sub-frame rate, so the timer NMI cannot
simply be swapped for the `/FLAG` NMI without losing sub-frame rendering. Two
options:

* **Hybrid (recommended):** MIDI clock advances only the transport / row timing,
  while an internal timer keeps driving sub-frame SID rendering. Accurate, but
  the most code — it has to reconcile two clocks.
* **Per-clock player tick:** drive the whole player once per MIDI clock. Much
  simpler, but loses sub-frame precision and degrades sound timing.

SID Wizard gets away with the simple per-clock approach because its player is
one-tick-per-clock; defMON's sub-frame model makes Phase 2 materially harder.

## Relationship to Phase 1

Master (Phase 1) and slave (Phase 2) are mutually exclusive at run time — defMON
is either the clock source or follows an external clock. A finished defMonV would
expose them as a mode switch rather than running both at once.

## Effort / risk

| | Phase 1 (master) | Phase 2 (slave) |
|---|---|---|
| Scope | ~4 byte-size-preserving patch sites + a stub | NMI source rework + handler + clock/tempo reconciliation |
| Risk | low (verified) | high (timing, sound quality, interrupt rework) |
| Status | implemented | scoped only |
