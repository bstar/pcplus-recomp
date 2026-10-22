# Peer flow state across script ownership

The [later v6 carrier checkpoint](MODEM_RECONNECT.md) retains this50-byte
layout and adds a bound MODEM/known-DCD bit. It prevents XOFF/XON teardown from
contaminating command-mode initialization after carrier loss. Legacy v5 pause
handoff remains supported and tested. The v5 checkpoint below retains its
original identities, defined bits and scope.

[Independent validation](validation/aspect-flow-handoff.json) covers parent
a4c377c9 and runner ec93148f. The previous source-built pair loses a received
XOFF when a script times out or is cancelled. Keyboard input queued after the
child returns reaches the peer before its XON. The new pair preserves that
pause; cancellation and timeout still return normally, but queued application
bytes wait for XON. This is a maintained handoff correction.

The baseline and corrected fault runs have identical64-byte serial streams.
Their ordering against the peer's XOFF/XON events distinguishes the defect:
the old parent sends `ready` and a query response too early. Total-byte equality
alone would miss this. The passive timer sees no retained parent pause in the
old runs and37/61 paused parent ticks in the corrected timeout/cancel runs.
SOFT and BOTH are tested; DOSBox-X keeps CTS asserted.

ASIOv5 extends the existing48-byte v4 descriptor to50 bytes:

| Offset | Input before child entry | Output before returned=1 |
| --- | --- | --- |
| 0..47 | Existing v4 identity, ring, policy and renderer fields | Existing checked publication |
| 48 | Peer software TX pause:0 clear,1 paused | Current peer software TX pause:0 or1 |

The input word participates in the existing guard. Unknown flag bits are
rejected; a paused input requires S or B software flow. The child installs the
input pause during raw preload, before its UART ISR is installed. A modeled
native-ISR test observes that ordering and real XON/XOFF updates. An actual DOS
entry fixture sends XOFF with CONNECT, observes the parent's v5 input flag and
the child's20 paused ticks, then releases two exact2,048-byte transmissions.

On close, the child first quiesces its UART IRQ and restores the parent's quiet
baseline. It publishes raw RX, status/count and the final pause word, then
returned=1 last. Parent completion validates the original input guard using its
unchanged quiet UART state, validates the returned flag, then adopts it before
restoring the parent IRQ. The output may differ from the guarded input. An
invalid flag leaves the prior pause intact and reports a failed script return.
This flag is scalar state; it introduces no child pointer or borrowed buffer.

The child continues accepting legacy ASIOv1/v2/v3/v4. A v4 tail sentinel stays
unchanged. Renderer capabilities12/13 and the renderer RPC operations are
unchanged. The source-built earlier child rejects v5 as argument status1 before
any UART write or renderer request. Distribute matching parent/child executables;
the old child cannot provide the new handoff behavior.

Validation includes16 linked child cases,13 linked parent cases and the earlier
child rejection control; four actual DOS timeout/cancel cases, two entry cases
and two successful resume cases;104 existing Script-owner inputs;108 legacy
serial-owner inputs;64 parent carrier/status groups; four modem-drop cases and
a separate parent-state capture. Ten confirmation workflows,56 COM/flow/process
cases and13 attached PROGRAM cases pass. Fresh original-free trees reproduce
26 application and23 diagnostic products. The diagnostic's pure cleanup checks
now reside in PROCESSDIAG so the near code ends at65456, leaving80 bytes. No
assertion was removed. Normal/mouse data spare remains112/64 bytes; near-code
spare is190/42 bytes. Memory segmentation remains unfinished application work.

[Four fresh recorder/replay sessions](validation/bbs-flow-handoff-compat.json)
and [two stock-window sessions](validation/bbs-flow-handoff-window.json) pass on
owned stock Synchronet/ENiGMA. [Normal software audio](validation/recording-flow-handoff-audio.json)
passes26/34/12 checks on one ENiGMA V22/1200 recorder route. [Two independent
emulated CTS cases](ASPECT_CTS_DOS.md) also pass short HARD/BOTH stalls. These
workflows do not supply physical flow timing.

Run the new checks through Nix:

```sh
./tools/build test-aspect-flow-handoff test-parent-flow-handoff
./tools/build test-aspect-flow-return-dos test-aspect-flow-entry-dos
./tools/build test-aspect-flow-fault-dos
```

The first baseline fixture sampled cancellation for only4 ticks while demanding
more than8; it remains unaccepted. The corrected baseline delays Escape400ms
and samples12 ticks. The first parent linked checker used the wrong harness
attribute for port writes; its corrected run executes those assertions. Both
attempts remain preserved alongside the accepted raw captures and source copies.

The sender still has a36-BIOS-tick per-byte pending bound. This change preserves
flow ownership when that bound expires; it does not make long BBS pauses usable.
A configurable longer-stall policy, longer CTS stalls/fault return, RTS and sustained RX pressure,
carrier reconnect and reset of flow state on genuine carrier loss remain
required. Software-audio flow pressure, physical Boca/SPA2102 and every full
F01–F16 application gate remain open.
