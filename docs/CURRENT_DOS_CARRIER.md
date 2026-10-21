# Current DOS carrier recovery and source rebuild

[This receipt](validation/current-DOS-carrier-retry.json) validates terminal
`976ba8d0`, production ASPECT `aef146fd` and DOS compiler `3470c718` against the
owned loopback ENiGMA fixture. One DOS process logs in, begins a ZIP download,
loses its first network connection after a verified 4,096-byte partial write,
observes carrier loss, redials and logs in again. The partial is gone before
the second login. The retry receives all 34,169 ZIP bytes, confirms protocol
finish, opens the NFO page and exits with restored hardware state. Both directory
connection updates and unchanged source/configuration/message gates pass.

This is DOSBox-X's built-in modem with emulated DCD and the fixture's RTS/CTS
initialization, through a Telnet-only relay. The ENiGMA instance has its declared
patched keyboard parser and synthetic users/data. It does not establish physical
Boca/SPA2102 behavior, SIP/audio carrier recovery or an unmodified server pass.
The laboratory's network-dial syntax is not a Boca telephone dialing profile.

All sixteen producer gates, five relay unit gates and thirteen capture-negative
checks pass. The unchanged positive oracle requires exact CRC/source/finish
controls and post-retry NFO. Its original negative mutated one NFO title while a
second valid redraw remained. That failure is preserved; the new title/body
negatives remove every qualifying copy. Original captures and the earlier
auditor remain unchanged.

The same checkpoint reproduces 31 DOS products byte-for-byte from 576 declared
source files, with no originals, prior project objects or REA databases in the
fresh tree. The canonical command now establishes its own diagnostic fixture:

```sh
./tools/build test-terminal-mouse-source
```

Before the target fix, the ordinary experimental CLI manifest omitted
`aspect_process_diagnostic.c`, so the clean rebuild stopped at that missing
source. The target now explicitly builds the required diagnostic, matching the
non-mouse source-proof path. The failed and passing Make runs are both retained.

Refreshing stale helpers also exposed a five-byte overflow in the fault
diagnostic. Its repeated interrupt-number expressions are now one equivalent
constant table: INT 0, 23h and 24h, plus 1Bh for the guarded Break owner. No
fault or cleanup checks are removed. The new `_TEXT` body is 65,509 bytes and
its linked end is 65,525, within 64 KB. Seventeen ordinary and five guarded
actual DOS cases verify first-error propagation, cleanup and a second real
ASPECT/PROGRAM invocation on the same UART/renderer.

With the declared owned fixture running, use fresh labels:

```sh
./tools/dev --command python3 lab/bbs/enigma_carrier_dos.py \
  --candidate build/bbs-lab/owned-enigma-cancel-01/candidate --label FRESH_LABEL
./tools/dev --command python3 lab/bbs/check_enigma_carrier_current_audit.py \
  --candidate build/bbs-lab/owned-enigma-cancel-01/candidate --label FRESH_LABEL
```

The production terminal, ASPECT runner and compiler bytes are unchanged by the
diagnostic/source-target fixes. All F01–F16 whole-feature gates remain open;
this source proof and carrier workflow do not replace full language, UI,
protocol, DOS-kernel or hardware acceptance.
