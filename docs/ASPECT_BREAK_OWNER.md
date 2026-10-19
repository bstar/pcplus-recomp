# ASPECT child BREAK transport owner

This document records the initial transport checkpoint at7ff697c. The command,
parent configuration and native UI are now connected; see
[the current runtime integration](ASPECT_BREAK_RUNTIME.md). The ownership and
transport checks below remain independently scoped. Historical69-slot/eleven-SET
and132-output counts in that checkpoint are not the current application counts.

## Ownership and timing

`serial_backend.asm` supplies three nearcdecl DS=SS operations. Reserve requires
an active, healthy lease, no existing reservation and neither BREAK nor DLAB
in LCR. It holds ordinary and queued flow transmission. Assert requires an owned
reservation and actual LSR TEMT, rather than THRE alone. Release clears only bit40
for an asserted pulse, preserves current framing/DLAB and leaves a foreign
BREAK untouched when assertion never succeeded. These transitions briefly save
FLAGS and disable interrupts, without a wait, DOS call, PIC or MCR operation.
They restore entry IF and preserve callee registers. Both C and assembly close
paths release before flow draining or hardware restoration. Opening a UART also
rejects foreign BREAK/DLAB before the native hardware saver first writes LCR.

`runtime_serial_break(units)` rejects IF0, reserves before servicing any queued
flow, and uses the existing IRQ-live calibrated6B72 service. RX interrupts and
hardware flow remain available during calibration/draining/pulse. A TEMT drain
has a19-BIOS-tick limit plus an independent65535-poll limit for a stopped clock.
Malformed tick values fail explicitly. A zero duration asserts/releases without
calibration. All nonzero raw16-bit durations are split into chunks of at most999
units; normal source SET will separately enforce the original0..32767 bounds.
Cancellation, UART errors and pacing failures converge on owned release.

This is a deliberate maintained policy. Original0401 has no TEMT, ownership,
cooperative cancellation or error cleanup. Native7956 calibration masks PIC
interrupts; the maintained timing service keeps them enabled and documents its
quantization. See [native recovery](ASPECT_BREAK_NATIVE.md),
[calibrated delay](ASPECT_TXPACE.md) and the distinct parent
[Alt-B owner](LIVE_BREAK.md). No exact physical pulse duration is claimed.

The recovered UART combined-flow branch gives software handling priority over
hardware high-water handling. Tests verify RX and queued XOFF in combined mode,
and RTS separately in hardware mode; they do not claim combined RTS was fixed.

## Verification

```sh
./tools/build test-aspect-break-native test-aspect-break-compiler
./tools/build test-aspect-break-owner test-aspect-break-linked
```

The owner checker executes the actual linked `aspect-serial/SERIAL.EXE`, including
its recovered ISR, maintained API and both close paths. It checks all256 LCR
values under both IF states, TEMT/THRE, foreign changes, register/DS=SS preservation,
held TX with continuing RX, hardware RTS, queued software flow, fatal cleanup
and idempotence. Every owner port write must occur with IF0 and target LCR only.

The linked checker executes the actual production `aspect-runner/ASPECT.EXE`
service and native delay instructions. It checks0/1/350/999/1000/32767/32768/65535
unit counts; cancellation and overflow across chunk boundaries; drain timeout
including midnight and a stopped BIOS clock; delayed TEMT; foreign LCR before
calibration and after reservation; IF0 and missing UART admission. The full-word
count tests explicitly set calibration count1 after real preparation. A separate
350-unit case uses the actually measured count74. UART, BIOS ticks and keyboard
inputs are modeled. Reports retain executable/checker hashes under
`build/aspect-serial/break-owner-checks.json` and
`build/aspect-runner/break-linked-checks.json`.

These proofs do not establish actual DOS scheduling, physical UART timing,
parent duration inheritance, native UI integration or command dispatch. The subsequent
[application proof](ASPECT_BREAK_RUNTIME.md) covers those integration requirements
separately.

The7ff697c checkpoint application regressions passed six actual DOS UART lease cases,
the878-case interpreter suite and both local BBS script/editor workflows.
Synchronet uses its established immediate forwarding path. ENiGMA uses the
established network keyboard profile and explicit30ms modem buffering. An
additional enigma-editor-profile attempt failed Home/Insert semantics and is
retained alongside that successful comparison; immediate-forwarding ENiGMA
compatibility remains open. These are application regressions, not execution of
the then-unwired BREAK command. Public bound summaries are in
[validation/aspect-break-owner.json](validation/aspect-break-owner.json).
