# ALARM real DOS platform checkpoint

The cooperative native alert now has a real DOS/BIOS/PIT platform adapter.
The standalone diagnostic passes 50 DOS8086 cases and 46,120 checks while
receiving 508 exact bytes per case during the alert. A cold export of 29
declared source files reproduces the exact executable and repeats three
selected cases. This is component validation; the ALARM command has not yet
been added to the interpreter. The subsequent
[compiler checkpoint](ASPECT_ALARM_COMPILER.md) supplies host/DOS emission.

`alarm_dos_run` uses DOS function 2Ch for seconds, atomically reads BIOS ticks,
preserves the selected standard/enhanced BIOS keyboard mode, and borrows the
existing banked speaker owner. The caller supplies bounded foreground service
and a finite poll budget. A service error is retained separately from the
adapter result. The service callback must leave keys for the alert owner.

The adapter records its speaker generation. A replacement generation cannot
be silenced by stale cleanup. Instead, the run retains ownership and borrowed
callback context until the foreign owner retires and explicit recovery succeeds.
The caller must keep that context alive while `alarm_dos_active` is true.
A busy speaker gate is preserved. The recovered native controller, cooperative
bridge, real UART ISR and real speaker bank execute in the diagnostic.

## Coverage and evidence

The [receipt](validation/aspect-alarm-dos.json) binds the executable, current
sources, all matrix captures and cold reconstruction to the earlier
[cooperative/native baseline](ASPECT_ALARM_COOPERATIVE.md).

The main matrix tests COM1 and COM2 with no flow control, software flow control,
hardware flow control and both, in each of these paths:

- Normal paired-tone completion and quiet completion.
- Key completion: Escape ends normally; the following F1 remains available.
- Foreground service failure, with its typed status retained and sound released.
- Preexisting busy gates, which the adapter must leave alone.

Eight additional key cases use enhanced BIOS mode. Two cases replace the
speaker generation during the alert, require cleanup quarantine, reject recovery
while the foreign owner is active, and recover after that owner explicitly
stops. All cases require the complete 508-byte payload to be consumed inside
the alert, a subsequent READY exchange, exact outgoing wire bytes and restored
UART registers, interrupt vector and PIC state. Callback/sound-poll counts
measure servicing, not the number of audible beeps.

DOSBox runs an 8086 with no FPU, a muted mixer and an independent raw TCP peer.
The actual PIT instructions execute; acoustic waveform and physical timing
remain untested. Nullmodem holds CTS ready and does not enforce RTS, so hardware
flow selection here is not a physical CTS/RTS stress test. Software cases send
explicit XOFF/XON. This speaker is the PC speaker, separate from the analog
modem speaker and its handshake audio.

## Reproduction

Each output directory must be new. Use the pinned Nix environment:

```sh
./tools/dev --command python standalone/build_alarm_dos_uart.py \
  --output build/my-alarm-platform
./tools/dev --command python standalone/test_alarm_dos_uart.py \
  --build build/my-alarm-platform --output build/my-alarm-matrix
./tools/dev --command python standalone/prove_alarm_dos_source.py \
  --build build/my-alarm-platform --output build/my-alarm-cold
./tools/dev --command python standalone/record_alarm_dos.py \
  --build build/my-alarm-platform --matrix build/my-alarm-matrix \
  --cold build/my-alarm-cold --output build/my-alarm-receipt.json
```

`make test-aspect-alarm-dos` builds and runs all 50 cases;
`make test-aspect-alarm-dos-source` also performs the cold reconstruction.
The cold proof needs the caller's pinned toolchain environment, without original
binaries, private configuration, previous objects or Git metadata. It repeats
normal COM1 I/O, enhanced-key COM2/software flow and replacement-owner recovery;
it does not repeat all 50 cases.

## Remaining application integration

Bind the checked operand wrapper to the now-emitted compiler format and current
parent duration/sound policy. Integrate foreground WHEN/receive rendering with exclusive key ownership
so Escape completes ALARM normally rather than aborting the script. Fund the
extra code without reducing stacks, streams or buffers, then repeat six-stream,
nested-child, carrier and BBS gates. The installed connection package remains
unchanged. Physical Boca/SPA2102/SynthModem acceptance and full parity remain open.
