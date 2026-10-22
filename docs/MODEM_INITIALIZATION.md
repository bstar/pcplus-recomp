# Modem initialization result policy

The maintained terminal supports `/I:0..32767`, selecting how many seconds to
wait for each initialization result. Omitted or `/I:0` preserves legacy sending
without waiting for initialization acknowledgements. For example:

```dos
TERMINAL @TEST.PRM /D:5551234 /I:3
```

The number remains a modem dialing target; a Telnet hostname is entered at the
Linux bridge's CONNECT> prompt after carrier establishment. Initialization bytes
come from the configured PRM fields; no modern modem commands are synthesized.

With `/I` positive, each nonempty CR-terminated command must receive a complete
OK or numeric 0 before the next command or ATD. ERROR or numeric 4 aborts without
dialing. Matching ignores case and surrounding spaces; echo, unknown lines,
oversized lines and incomplete replies cannot acknowledge a command. Replies
arriving immediately after CR are retained even while final pacing completes.
CRLF and configured pause expansion are preserved. Nonempty unterminated commands
and embedded physical LF are rejected before serial side effects.

Each send uses the PRM dialing timeout; each acknowledgement uses `/I` seconds.
An empty physical command or retry synchronization separator drains responses for
the full `/I` interval before admitting a new command. This bounds stale-response
handling; it cannot correlate arbitrarily late replies beyond that interval.
Escape/Alt-X cancellation, DTR cleanup and the failed-online-hangup guard remain.
Direct lines and the existing initial-carrier setting can bypass initialization.
The configurable eleven-slot dialing-result matcher remains separate.

No-wait controls suppress initialization acknowledgements while still supplying
CONNECT for dialing. They do not prove fully silent Q1 automatic dialing.
Physical Boca command support and timing are unverified.

## Accepted component evidence

[Independent receipt](validation/modem-init-policy.json) binds 74 linked
normal/mouse groups, nine actual 8086 DOS cases and four DOS cancellation/retry
cases. It also binds existing connection/startup/carrier/hangup regressions,
2,025 compiler cases, 2,015 first-pass cases, 2,043 checked-stack cases and thirteen
attached PROGRAM workflows. Normal, mouse and DOS compiler products reproduce
byte-identically in a fresh build from 418 declared source files with originals
absent. The [compiler memory correction](COMPILER_MEMORY.md) preserves nested
compilation after the new resident code increased conventional-memory pressure.

A separate [current-product BBS receipt](validation/bbs-initialization-compat.json)
now accepts four actual DOS Synchronet/ENiGMA record/replay sessions with explicit
`/I:3`. The auditor checks the captured invocation, physical ATZ/ATD prefix,
recorded source, DOS compilation, exact navigation bytes, server routes and
42-byte UART restoration. Synchronet's synthetic account exemption returns to
its original zero flags. Its final serial socket reports peer reset during
normal shutdown, within one second of runner completion; the audit records this
and requires completed navigation, exact shutdown bytes and successful DOS exit.
ENiGMA closes with serial EOF. No earlier transport error is admitted.

The first Synchronet attempt failed before DOS launch because the BBS-only shell
lacked NASM; its exemption was restored. The accepted replacement uses the full
Nix development toolchain for DOS execution. Raw failed and accepted cohorts
remain separate under ignored build storage.

A separate [software audio receipt](validation/recording-init-wait-audio.json)
now accepts the current parent/compiler with `/I:3` on one ENiGMA V22/1200 route
at 38400 DTE: 26 producer, 35 independent and 12 serial checks pass. All 77
online guest bytes decode independently from caller RTP and match serial input.
Recording, actual DOS compilation/replay, subsequent manual Search and
hardware/timer/SIP/VM cleanup complete. The unchanged seven-case BIOS helper and
14-check TCP control are bound through a separate
[preparation receipt](validation/recording-init-wait-audio-preparation.json).

[Current normal/mouse packages](validation/modem-init-packages.json) contain the
validated terminal, sibling helpers and updated DOS compiler, plus authored
examples and initialization instructions. Both packages pass actual 8086 DOS
compilation, bytecode execution and source compile/run of the example. Rebuild
with `./tools/build package` or `./tools/build package-mouse`. To stage already
built products, `./tools/dev --command python3 standalone/package_dos.py
--stage-current` checks their binary and source identities before copying;
add `--mouse` for the mouse package. This does not prove complete terminal/mouse
interaction or full distribution acceptance.

Broader editor/transfer and audio routes remain required. The initialization
component receipt predates these BBS/audio receipts and retains its explicit
unaccepted BBS/audio field. Physical Boca/SPA2102, V.8/14.4 compatibility and full
F03 remain open.

# Historical baseline

[Four independently audited actual DOS cases](validation/modem-initialization-baseline.json)
reproduce an open initialization policy on parent3b453f2b. The maintained
controller completes transmission of the configured initialization string and
immediately starts the dial sender. Initialization-state RX is consumed without
an initialization result parser. No application change is accepted here.

| Owned peer policy | Actual DOS outcome | Interpretation |
| --- | --- | --- |
| Immediate OK | Connects and answers ANSI queries | Existing control passes. |
| Quiet-ready, no initialization reply | Connects and answers ANSI queries | Valid compatibility case; silence alone is not a defect. |
| Explicit initialization ERROR | Still sends ATD; peer rejects it with NO CARRIER | Initialization failure is not acted upon. |
| Ready after750ms | Starts ATD before OK; peer rejects a command started while unready | The sender finishes bytes without waiting for modem readiness. |

The delayed peer declares a750ms readiness interval for a deterministic test.
It does not measure a Boca modem, Wi-Fi modem, firmware reset duration or
physical connection. In that case the first dial byte precedes OK even though
the complete ATD line arrives later. The independent auditor checks this first
byte's time from the raw receive transcript, rather than treating the command
completion time as the beginning of the dial. Response timestamps identify
host-peer writes, not the time each byte was consumed by the guest UART. The
source inspection establishes initialization-state handling; the captured wire
establishes the command/readiness ordering under this declared transport.

Every case retains exact configured ATZ/dial bytes, actual UART/IRQ/controller
execution, peer responses, expected abort or configured hangup, ordinary DOS
exit and42-byte UART/PIC/vector restoration. Only the two control cases connect;
no credentials or external BBS are involved. `passed=true` means the declared
gap/control outcomes are reproduced. `initialization_policy_accepted=false`
remains explicit.

~~~sh
./tools/dev --command python3 standalone/test_modem_initialization_dos.py \
  --output build/modem-initialization/dos-new
./tools/dev --command python3 standalone/audit_modem_initialization_dos.py \
  build/modem-initialization/dos-new \
  --output docs/validation/modem-initialization-new.json
~~~
