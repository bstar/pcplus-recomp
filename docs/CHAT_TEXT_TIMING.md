# Serviced Chat TEXT timing

The optional API0103 Chat module now owns BIOS pauses and calibrated native
pacing. `build_chat_module.py --timing` implies TEXT/presentation;
`build_terminal.py --chat-timing` selects the matching loader and frontend ABI
and requires the funded physical-TX adapter. **The ten foreground shortcuts
remain refused until original echo is integrated.** This is an integration
checkpoint, not a replacement selected for the physical machine.

The module uses448 caller-owned far bytes: the previous430 plus an18-byte timing
owner. Its request stays50 bytes. File7260/image7212 bytes, three self-relocations,
no private DGROUP/stack/CRT/extra allocation, SHA
`5b6892e71dfb6054cc5e1ff04b9cfac380af1a5e530da11dc2780325a8d45622`.
It fits the existing8192-byte executable window, leaving980 bytes. The matching
experimental parent SHA is
`5ecf87743f55c97e83a334c3a5ef9e049dc4de1558ec4d482a529cf215092846`;
minimum allocation479392 bytes, still below the preceding479408-byte foreground.
Stacks, streams, heap quantum and feature capacities are unchanged.
An initial odd code ending required one extra DOS paragraph; the final assembly
adds one alignment byte and retains the builder's zero-minalloc guard.

## Service behavior

TEXT operation8 retains its previous field contract. Operation9 services timing
internally; external callbacks still supply actual TX completion and original
echo. It no longer forwards BIOS-wait/pacing effects to that callback. Before a
nonzero-paced TEXT emits any effect, it aligns to a BIOS tick and calibrates.
Alignment returns0 while pending; callers must use `text.active` to determine
completion and keep servicing receive/session work. Budget0, absent sink or
inactive TEXT does not start calibration. Calibration persists within a Chat
session and whole-session abort resets it.

The one-unit primitive retains the exact eleven-byte inner loop from recovered
6B72: SUB/ADC/ES-memory CMP/JNE, including count0's65536 iterations. Calibration
uses the maintained ASPECT model: count completed512-iteration chunks in one
BIOS interval, then `floor(chunks*512/55)`, with4..7039 chunks admitted. A single
measurement occupies one tick interval; it does not yield inside that interval.
IRQs stay enabled, and missing/invalid/coarse timing produces a typed sticky
fault. The7039-chunk ceiling bounds a stopped clock; it is not a millisecond
deadline. No IRQ mask/PIC changes or DOS/UART/key calls occur in the timing owner.

An ordinary pacing effect executes at most one calibrated unit per callback
attempt. Its full16-bit unit count remains pending until all units complete;
zero units completes without a unit loop. BIOS argument9 waits ten elapsed BIOS
ticks, with full-day and low-word wrap handling. Missed observations do not add
extra intervals. The native argumentFFFF wraps its target to one observed change;
the maintained elapsed-time equivalent also waits one tick. Mismatched pending
kind/value refuses without replacing the owner. Abort discards pending timing.

These are deliberate cooperative adaptations: the recovered tick helper spins
and executes STI, whereas this owner requires IF already enabled and preserves
it. Calibration follows the maintained ASPECT model, not a claim to recover
original7956 calibration. Unit scheduling, helper overhead and other foreground
work change elapsed wall time. Native arguments are not relabeled milliseconds,
and physical timing accuracy has not been established.

## Verification

The CPU fixture executes actual module instructions and compares the inner loop
with the hash-pinned recovered pace source. It covers count0/1/2/512/65535,
IF/register/stack ABI, calibration4..7039, stalled/invalid/coarse clocks, sticky
faults, ten-tick waits, midnight/low-word wrap, zero/seven pacing units, pending
full-word count, mismatch/reset and two relocated module contexts. A BIOS-wait
fault also surfaces through operation9 when pacing0 bypasses calibration.
Time edges and external sink effects are modeled. Full65535-unit pacing duration
is not executed; the pending65534 decrement is checked.

Actual DOS8086 loads through4B03 at two addresses while all remaining DOS memory
is reserved. Real BIOS ticks drive pauses and calibration; host callbacks record
TX/echo, refuse B three times and check module reentry/unload protection. Incoming
F0 renders and reaches history/log while a pause is pending. Unfinished local
input survives. A real50-row font change quarantines the owner; returning to
mode3 permits full4000-byte frame restoration and retirement. Stale API/file,
budget0/no-sink, abort, canaries, CRC and unchanged PSP/JFT/free memory are checked.
The host contains no statically linked Chat implementation.

A separate linked CPU composition runs the actual parent UART/IRQ, queue,
history/log and recorder with API0103. CTS/queued replies cannot start pacing.
One physical grant emits one user byte; FF becomes wireNUL without pacing.
RX continues during the ten-tick pause, the original local line survives and
the recorder contains only actual user-wire bytes. Calibration/time edges are
modeled and echo is explicitly disabled in that composition; this does not
verify original echo rendering or foreground keyboard ownership for TEXT.

Normal8086 main and the pending-prefix Chat-return regression pass with the
matching parent/module. The26 nested ASPECT checks pass. API0100's568 full frames
and1071 effects and API0102's runtime TEXT fixture pass unchanged. A clean689-file
public source export reproduces parent/module/header and the timing host EXE;
nine build/runtime commands repeat without originals/private settings/prior
objects, with ancestor Git discovery disabled. BIOS-dependent check counts and
captures are not claimed byte-identical. Timing-disabled parent remains exact
5c4f5c94; disabling the TX adapter also restores exact5875536a.

Synchronet's25 editor/external-viewer checks pass on the new parent through the
actual proxy. Enigma's16 carrier-loss/redial/clean-staging/exact65539-byte retry
checks pass with the established150-second transfer allowance. No product timing
fix or diagnosis of the earlier unrelated redial miss is claimed.
These ordinary BBS workflows leave Chat inactive. No production bridge/server
configuration, selected package, private DOS files or physical PC was changed.

Next recover original0610 echo context/rendering and bind all ten shortcuts with
fair pre-read/RX ownership, then Help/Alt-Z/send-mode UI and broader Chat failure,
geometry and sustained-traffic gates. Final package/deployment/hardware and full
original parity remain open. See [TEXT](CHAT_TEXT.md),
[funding](CHAT_TEXT_FUNDING.md) and [foreground](CHAT_FOREGROUND_CORE.md).
The [checkpoint receipt](validation/chat-text-timing.json) binds these checks.

The next [echo-context checkpoint](CHAT_ECHO_CONTEXT.md) verifies the cached
cursor hazard and exposes an existing position service without executable
growth. The echo sink/parser and live TEXT shortcuts remain unfinished.
