# Delayed log writes and paced serial traffic

The optional call-log controls image now has three delayed-write workflows
with a real UART, actual DOS file writes and a flow-aware synthetic peer.
The application image is unchanged. These checks extend selected logging and
transport evidence; full sustained/protocol, rendering and hardware acceptance
remain open.

## Workloads and independent checks

Each case starts with an existing synthetic log and sends three text frames:
16 positioned rows per frame, 79 printable characters per row and a real cursor
query after each row. All 48 actual cursor replies must arrive in order. The
final 24-row screen must match all 1,920 glyphs and all 1,920 attributes; real
keyboard input must still reach the peer afterward. The original log prefix
must survive exactly, followed by one original-timestamp START/END pair.

- **SOFT, nine BIOS ticks:** the first log write is held while interrupts stay
  enabled. After observing XOFF, the peer allows one 356-byte in-flight burst
  and then stops scheduled data until XON. The UART receive ring must grow
  during the delay without dropping data.
- **BOTH, 36 BIOS ticks:** the longer hold uses the same bounded burst and
  software pause. A real read of the UART MCR additionally verifies RTS is low
  while the write is held. Peer flow follows XOFF/XON; this does not prove that
  physical RTS reaches or controls a real modem.
- **NONE, 36 BIOS ticks:** the paced stream completes without software flow.
  Online commit samples must remain zero. The first append is delayed only
  during shutdown, after UART restoration, and the ring stays empty there.
  Both records must then save with normal exit.

The delayed data write must return its real full 64-byte result. Entry and wait
FLAGS must show interrupts enabled, observed tick progress must reach the
requested delay, and the exact parent DS must match the independently observed
application segment. Receive-drop counters must remain zero. The healthy
cases require exactly two append attempts and no retry acknowledgements.

The peer records each observed flow byte and each send timestamp. An independent
check reconstructs paused intervals from those observations and rejects any
scheduled send during a pause. The one explicitly bounded in-flight burst must
be sent while paused. A byte-exact outgoing oracle checks initialization, dial,
initial terminal reports, every cursor reply, keyboard text and hangup. A
separate payload artifact binds every byte the peer sent.

## Delay-fixture boundary

`phone_log_slow_write.asm` tracks only the exact owned log handle. It delays
that handle's first nonzero write, reads UART counters and then chains to the
real DOS write. It does not patch product state, synthesize terminal replies,
consume UART input or write UART registers. The existing passive observer
separately reads stable call state and verifies vector restoration.

The hold enables interrupts only when the original caller had them enabled,
uses a finite iteration bound and records actual BIOS tick progress. It models
an IRQ-friendly application stall before the real DOS write. It does not model
a disk driver masking interrupts, arbitrary media latency or power-loss
behavior. The bounded burst is below the driver's high watermark: watermark
ownership collisions and larger in-flight buffers still need dedicated tests.

## Reproduction

The [receipt](validation/phone-log-slow-io.json) binds the final three native
cases and a clean public-source rebuild. That export repeats them plus 36
previous menu, existing-file, startup, write-failure and access workflows:
39 DOS cases. Source-only inputs reproduce the exact terminal; original
executables, installations, previous objects and REA databases are excluded.
The earlier glyph-only probe/draft is outside the final acceptance receipt.

Image: `build/terminal-phone-log-bank-3d164fda0202/TERMINAL.EXE`.
SHA256: `2c5f5fc4dd4b9948b897db6499e920f694f30fbbbcdf3d1fb0596cbc921027f7`.

```sh
./tools/dev --command python3 standalone/test_phone_log_slow_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 --label slow-check-01
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/terminal-phone-log-bank-3d164fda0202 \
  --output build/phone-log-slow-public-repeat-01 \
  --commit 1759b2a --extended --permissions --slow
```

Use fresh lowercase labels/output directories. This is paced ASCII/ANSI
traffic with selected final-screen and every-query checks, not every-frame
BBS rendering or file-transfer acceptance. Larger buffers, sustained throughput,
carrier/child/ASPECT/exception composition, broad feature combinations and full
F01–F16 behavior remain open, alongside physical Boca/SPA2102 and deployment.
The published BBS package, card, live BBS, installed bridge, ATA and host network
were not changed.
