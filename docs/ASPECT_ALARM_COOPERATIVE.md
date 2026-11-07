# Cooperative ALARM adapter

The recovered93-byte shared alert now runs through a bounded foreground service
adapter. It retains the native controller's duration/paired-tone/keyboard flow
while replacing its blocking service calls. This component is not yet an
ASPECT opcode. The subsequent [real DOS platform](ASPECT_ALARM_DOS.md) supplies
BIOS/DOS/UART/PIT component coverage; parent policy and VM binding remain open.

`alarm_coop_run` borrows explicit clock, key, service and exclusive-tone
callbacks. It services the caller during every tone/pause wait and native key
poll. Any available key ends the alert normally and consumes one key; a service
or clock error ends native flow without fabricating a keyboard event. Quiet
mode still services the caller while the duration runs.

The two880Hz/duration15 native requests become3-BIOS-tick tone requests, matching
the existing maintained connect alert's nominal150ms scheduling. Native1/6-tick
pause requests retain the original count-plus-one transition convention.
A key may stop a tone early. These are explicit maintained scheduling changes,
not proof of identical acoustic timing or real UART receive performance.

Each run has a finite service-call budget, so a frozen clock cannot leave it
waiting indefinitely. A failed release keeps the active owner and callback
storage borrowed for an explicit `alarm_coop_recover` retry; a new run cannot
reuse it. Reentrant run or recovery requests return busy. The caller's platform
adapter must preserve context, bound its own receive work, leave keys for this
owner and release only the speaker generation it acquired.

## Evidence

```sh
./tools/dev --command python standalone/test_alarm_cooperative_dos.py \
  --output build/my-cooperative-alarm
./tools/dev --command python standalone/prove_alarm_cooperative_source.py \
  --test build/my-cooperative-alarm --output build/my-cooperative-alarm-source
```

The [receipt](validation/aspect-alarm-cooperative.json) binds94 actual DOS8086
cases and1701 checks to the source and linked native controller. Cases cover
ordinary/extended/Escape keys, zero-duration late keys, clock wrap/stalls,
service failures, sound contention, invalid clock values, reentry, failed
release and context-loss recovery. Vector state, DS=SS and IF/DF are checked.
The platform callbacks model clock/keyboard/receive-service/sound behavior;
the native controller and C/RET2/RET4 bridge execute as real DOS instructions.

The first test incorrectly expected a zero-duration alert to wait for keys
arriving after its two native polls. Its four failed assertions were corrected;
the controller's behavior was retained. Additional testing protects against
reentrant recovery clearing an owner still executing a callback.

An empty8-file source export rebuilds the exact DOS executable and repeats
the full suite without originals, private files, previous objects or Git
metadata. The existing [native baseline](ASPECT_ALARM_NATIVE.md) remains120
exact bytes with348 separate CPU cases.

The optional original compiler probe also records39 authored sources:
17 accepted,22 rejected. `ALARM` emits an absent-operand byte; `ALARM value`
emits a presence byte then an atomic integer. Commas, parenthesized/compound
operands and wrong types reject. Constants32768 and65535 reject, while
negative16-bit constants compile but remain subject to the native0..32767
runtime bound. `forever` is an ordinary integer builtin operand here, rather
than WAITFOR's special timeout marker. This grammar was not implemented at this component checkpoint. The subsequent
[compiler checkpoint](ASPECT_ALARM_COMPILER.md) supplies host/DOS emission.

## Remaining integration

Bind the recovered operand wrapper and compiler emission; add checked current
parent duration/sound policy access; integrate the real DOS speaker backend with VM
foreground receive rendering that leaves ALARM's keys alone. Preserve the
existing six-stream/nested-child memory gate and test carrier/WHEN/window/error
cleanup through the real VM before selecting a package. Full parity and the
Boca/SPA2102/SynthModem physical acceptance gates remain open. The installed
Chat/Help release and its settings/history are unchanged.
