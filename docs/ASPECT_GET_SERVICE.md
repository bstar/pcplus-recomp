# GET keyboard and connection service

The opt-in `ASPECT_GET_SERVICE` path adds an exclusive field keyboard lease to
the actual WHEN runtime. It is not enabled in the maintained compiler, opcode49
table or reviewed application package. The earlier [typed owner](ASPECT_GET.md)
and this service checkpoint still need composition with the real parent display
and native interpreter lifetime.

`runtime_when_get_begin` admits a foreground field only with an active serial
session and no existing GET/ALARM, deferred service, monitor, abort confirmation
or parent modal window. `runtime_when_get_poll` calls ordinary WHEN service and
then the existing receive owner for at most64 leads or one BIOS tick. Raw ASIO
keeps bytes queued unless an active WHEN pattern needs them; an attached parent
can consume translation/match/display input. This is maintained scheduling,
not a recovered claim about the original field's blocking loop.
The poll revalidates ownership and serial state after native service returns,
before receiving more data or returning control to the field.

While leased, native key-ready reports no key and transport polling leaves all
BIOS keys intact, including Escape behind ordinary typeahead. Direct nested
WHEN key reads, key dispatch and abort confirmation are rejected. GET and ALARM
exclude each other. Reset, file reset and finish refuse to erase a live GET
owner. End requires ordinary foreground ownership with no borrowed/deferred
service or monitor, but permits cleanup after an ordinary service error.

This API deliberately cannot clear abandoned native frames after a nonlocal
abort. The future interpreter integration must prove stack restoration and
retire the field/display owner before releasing that case. A live modal frame
also needs a parent protocol that distinguishes GET's own field from competing
windows; generic modal-window admission is not that protocol.

## DOS and wire checks

[get_when_uart_diagnostic.c](../standalone/get_when_uart_diagnostic.c) composes
the actual WHEN C gates, source field model, recovered BIOS keyboard routines,
UART ISR and serial platform. Native WHEN action bodies and the parent receive/
renderer entry remain explicit modeled services. No original application or
private configuration is a build input.

The [independent TCP peer](../standalone/test_get_when_uart.py) exercises36
actual DOS8086 scenarios, with FPU disabled and fixed6000 cycles:

- COM1/COM2 and no/software/hardware/combined flow selections.
- Raw ASIO with standard BIOS, and a modeled attached receive entry with
  enhanced BIOS; these are two specific combinations, not a full independent
  BIOS-by-renderer matrix.
- Enter after typing `12`, and cancellation after typing `7` before Escape.
  F1 remains queued for the next owner; canceled edits never commit.
- Four service-error cases retain Escape/F1, leave the field uncommitted and
  allow explicit lease retirement without clearing another owner's work.

Each case checks508 exact bytes. Raw cases keep all508 queued until the field
lease ends. Attached cases drain all508 through the modeled receive entry using
actual UART reads. A second `READY!` exchange verifies continued use of the
same open UART; final checks restore the interrupt vector, PIC mask, divisor,
IER, LCR and MCR. The complete peer wire is checked, including software XON/XOFF.
Nullmodem holds CTS ready and does not enforce peer RTS; this is not a modem or
hardware backpressure test. The observed maximum attached burst is one lead
under this paced input; the64-lead cap is not a saturated-burst acceptance claim.

Admission checks also cover nested GET/ALARM, missing/quarantined serial state,
deferred callbacks, monitor ownership, competing windows, reset/file-reset/
finish attempts and forbidden nested readers/dispatch. The controlled serial
state fault does not emulate a physical DCD transition. Real carrier-loss,
native WHEN CALL/DISCONNECT/TRANSMIT actions, real parent screen/cursor behavior
and native abort/dispatcher cleanup during GET remain open.
Additional transition checks create a window, deferred owner, monitor or
quarantined serial state inside the modeled native callback. GET refuses to
continue until the competing owner retires; admission before the callback
alone would not catch these transitions.

A23-input clean public-source export rebuilds the exact diagnostic EXE and
repeats normal, enhanced cancellation and service-error wire cases, without
originals, private files, old objects or ancestor Git metadata. Three existing
ALARM wire regressions also pass. A separate comparison rebuilds the ALARM
diagnostic using the pre-GET WHEN source at `f2fd97b`; with GET disabled, its
EXE is byte-identical. That comparison does not claim a whole application
rebuild. [The receipt](validation/aspect-get-service.json) binds these checks.

```sh
./tools/dev --command python standalone/build_get_when_uart.py \
  --output build/my-get-uart
./tools/dev --command python standalone/test_get_when_uart.py \
  --build build/my-get-uart --output build/my-get-uart-tests
./tools/dev --command python standalone/prove_get_when_source.py \
  --build build/my-get-uart --output build/my-get-uart-source
```

Next integration work is the parent field/cursor/attribute protocol, native GET
abort checkpoints and lifetime, typed runtime bindings and floating runtime,
then both compilers/opcode49, connected scripts and application memory/package
gates. The reviewed package, deployment selector and physical PC are unchanged.
