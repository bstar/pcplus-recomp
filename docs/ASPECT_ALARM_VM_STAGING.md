# ALARM VM integration staging — not accepted

The subsequent [numeric-bank checkpoint](ASPECT_ALARM_NUMERIC.md) now executes
ALARM through the actual parent and WHEN/renderer. Its release still awaits
the held-stream capacity and other acceptance gates. The evidence below
describes this earlier failed staging attempt.

The opt-in interpreter now links opcode01 to the recovered ALARM operand
wrapper, cooperative alert, real DOS/PIT platform and exclusive WHEN key lease.
A matching opt-in parent publishes capability19 and current sound/duration
policy. Both source builds link, and the ordinary interpreter remains exact.
This staging has not passed runtime acceptance and must not be selected for a
release or installed as a replacement.

The [staging record](validation/aspect-alarm-vm-staging.json) deliberately records
`runtime_accepted:false`. The actual parent/child test now reaches dialing and
attempts ASPECT, but the passive observer captures DOS EXEC carry/error8:
insufficient memory. No child exit or KEYREADY is observed. ALARM itself has
not executed in this test. The observer occupies conventional memory, so this
does not establish the same failure without that observer or its sole cause.

The linked child requires133680 bytes including its PSP, compared with131312
for the preceding matched clock child:2368 additional bytes. The new parent
requires479680 bytes including its PSP. These are MZ minimum process extents,
not a measurement of all live DOS allocations or available largest blocks.
Preserve all existing stacks, stream slots, buffers and native operand capacity
while funding the new code and then repeat the actual capacity gates.

## Linked design

`build_aspect_process.main(..., alarm_vm=True)` requires the existing snapshot
lease and sound-enabled profile. It adds `ASPECT_ALARM_VM` and
`ASPECT_ALARM_SERVICE`; the ordinary build does not enable them. The new
`--aspect-alarm-policy` parent flag requires snapshot/sound configuration.
Capability19 prevents a new child from assuming older parents support the new
selectors. Existing capability18/default builds retain their original path.

Operation13 selector0 retains FF00/FF01 sound policy. Selectors1/2 return
FF00|low/high duration byte, reading the current parent setting without writes
or receive callbacks. The child validates the lease/context and all responses
before publishing defaults. Raw ASIO without an attached policy owner returns
a typed state error instead of guessing a profile. Full raw-profile parity
remains a separate requirement.

The native command saves duration, checks optional presence through the
existing native option reader and uses PAUSE's bounded0..32767 integer reader.
Its alert call enters the cooperative service and restores duration on normal
return, before dispatch checks service errors. A key completes normally;
transport and WHEN keep their key lease until sound cleanup succeeds. Failed
speaker cleanup retains static callback context and ownership for recovery.
Application-level quarantine recovery/teardown still needs integration tests.

The original native flat builds remain120 exact bytes and pass348 CPU cases.
The ordinary interpreter rebuild remains91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b.
These checks do not prove the new linked path executes correctly.

## Test corrections and remaining work

The older shared fixture first failed display/directory selection before
serial ownership, including with the accepted parent. Supplying explicit
supported display fields resolved that fixture failure. Its peer append hook
was updated locally to preserve the newer software-flow block. The passive
observer's older launch-kind restriction was replaced with active-PROGRAM
admission and capture of the actual DOS EXEC carry/error, retaining DOS flags.
The acceptance command now exits nonzero when its report fails.

The no-TSR nested probe also stopped before a useful script run with its older
fixture. It is not memory acceptance or evidence of ALARM behavior. Retain
these failed attempts; do not promote or rerun them as if they passed.

Next measure/fund memory and repair the no-TSR production fixture, then run
actual VM tests for absent/explicit/negative operands, default restoration,
quiet/sound and key completion; native WHEN CALL/TRANSMIT/DISCONNECT ordering;
real translation/renderer/query responses; service/error recovery; six streams
and nested children. Repeat Enigma/Synchronet/carrier/transfer gates before
packaging. Physical Boca/SPA2102/SynthModem acceptance and full parity remain
open. No selected package, installed files, private state, BBS or bridge changed.
