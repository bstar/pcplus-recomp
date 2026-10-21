# DOS recovery after a software audio bridge stops

This campaign combines the current source-built terminal, source-built DOS
ASPECT compiler/runner, DOSBox-X's built-in Hayes modem, the pinned real
SIP/RTP/V.22-1200 software audio path and the unchanged owned stock Synchronet
server. The [current200ms run](../../docs/validation/current-synchronet-reconnect-audio-04.json)
passes all19 producer gates, the complete independent audit,7 official metadata
checks and31 damaged-evidence controls. The
[first retained failure](../../docs/validation/current-synchronet-reconnect-audio-01.json)
and subsequent helper/media counterexamples are preserved below.

One DOS process authenticates and starts the ordinary XMODEM download. The host
observer reads the actual partial file and requires an exact, incomplete source
prefix before sending SIGTERM to that call's owned Linux audio frontend. The
frontend shuts down its real SIP/audio session and closes its TCP connection.
Only that EOF closes the adapter's DOSBox connection, producing emulated DCD
loss. A test-only BIOS helper waits for the visible `RX carrier lost` notice
or persistent `Carrier lost`, then presses Alt-D. It waits for the old transfer
prompt to disappear before accepting a fresh download prompt. The fresh call
starts another frontend/VM and trains both
real DSPs again; the DOS ASPECT script authenticates and repeats the download.
The helper completes the receive and visits Files/Main before normal exit.

The adapter consumes only its own synthetic ATZ/ATD1 response prefix. Online
bytes cross the original audio frontend without translation, protocol replies,
or a direct DOS-to-BBS shortcut. A passive multi-connection relay records both
raw Telnet wire directions. Separate DOS helper tests reject premature keys on
incomplete menu/carrier text, verify exact redial/receive/exit keystrokes and
restore INT1C. Loopback fixture tests verify strict response-prefix isolation,
all 256 online byte values, successive raw captures and EOF cleanup.

```sh
./tools/dev --command python3 lab/bbs/check_audio_synchronet_reconnect_keys.py \
  --output build/bbs-lab/audio-reconnect-keys-NEW
./tools/dev --command python3 lab/bbs/check_audio_carrier_adapter.py \
  --output build/bbs-lab/audio-carrier-adapter-NEW
./tools/dev --command python3 lab/bbs/check_audio_reconnect_relay.py \
  --output build/bbs-lab/audio-reconnect-relay-NEW
./tools/dev --command python3 lab/bbs/check_reconnect_notice_watch.py \
  --output build/bbs-lab/reconnect-notice-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_reconnect_dos.py \
  --runtime build/bbs-lab/synthmodem-posttrain-runtime-01/runtime \
  --key-checks build/bbs-lab/audio-reconnect-keys-NEW/result.json \
  --notice-checks build/bbs-lab/reconnect-notice-NEW/result.json \
  --output build/bbs-lab/current-synchronet-reconnect-audio-NEW
```

After natural producer exit, run the independent reconnect serial ownership audit
and offline caller decoder on each `COHORT/call-1` and `COHORT/call-2`, then:

```sh
./tools/modem-dev --command python3 lab/bbs/audit_audio_reconnect_io.py CALL
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js RUNTIME CALL
./tools/modem-dev --command python3 lab/bbs/audit_synchronet_reconnect_audio.py COHORT
./tools/bbs-dev --command python3 lab/bbs/audit_synchronet_reconnect_metadata.py COHORT
./tools/modem-dev --command python3 lab/bbs/check_synchronet_reconnect_controls.py \
  COHORT --output build/bbs-lab/reconnect-controls-NEW
```

The interrupted first call must preserve exact upstream bytes and an independently
verified downstream source prefix. It deliberately cannot deliver the entire BBS
output once the bridge stops. The retry must preserve the complete downstream
stream, every CRC/source block, opposite ACK/EOT controls and post-transfer menu
input. Both calls require real training, SIP teardown, continuous recorded RTP,
clean serial ownership and VM retirement. The failure ordering, partial deletion
before the second call, two directory updates, and final DOS/UART/vector cleanup
remain mandatory. A producer pass alone is insufficient.

This is a test-only failure adapter. DOSBox asserts DCD when its TCP connection
opens, before the software DSP finishes training; ASPECT waits for the real
`CONNECT>` prompt. DCD loss is coupled to actual frontend shutdown EOF. This is
not a measured physical carrier signal or an audible analog handshake. Numeric
loopback network dialing belongs to this lab, not the Boca telephone profile.
The adapter's ATD1 is a synthetic frontend command, not a captured Boca command.

Each call owns a new Linux frontend and VM. The campaign targets bridge-process
failure/restart and DOS retry, not reuse of one production bridge, physical
DTR/CTS/IRQ behavior, analog waveform-loss detection, arbitrary network faults,
other protocols, sustained pressure or F01–F16 whole-application completion.
Those requirements remain alongside this test in the full plan.

The separately built200ms DISCARD_NONE candidate now passes
[controlled delay growth and shrinkage](../../docs/validation/synthmodem-buffered-timing.json).
Its normal runtime replaces only d-modem, with exact normal init/kernel/JavaScript
and no PCM exporter. Use the explicit stage receipt for a full DOS repeat:

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_buffered_runtime.py \
  --output build/bbs-lab/synthmodem-buffered-runtime-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_reconnect_dos.py \
  --runtime build/bbs-lab/synthmodem-buffered-runtime-NEW/runtime \
  --buffered-runtime-proof build/bbs-lab/synthmodem-buffered-runtime-NEW/result.json \
  --key-checks build/bbs-lab/audio-reconnect-keys-NEW/result.json \
  --notice-checks build/bbs-lab/reconnect-notice-NEW/result.json \
  --output build/bbs-lab/current-synchronet-reconnect-audio-NEW
```

These controlled audio and staging results do not accept the DOS reconnect
workflow. Retain all nineteen producer checks and the independent full byte,
CRC, loss-notice, metadata and cleanup audits on the actual new run.

The completed `current-synchronet-reconnect-audio-04` supplies that separate
normal-DOS acceptance. Its first call preserves113 authored online bytes across
DOS, independent caller audio, guest DATA_RX and the BBS input. Ten CRC source
blocks verify10240 bytes; the observer stops the actual bridge after an8192-byte
partial and a delivered ACK. The partial is removed before the second call.
Both DSPs train again, and all121 retry input bytes and the complete49675-byte
BBS display survive. Fourteen CRC frames yield11521 source bytes plus127 SUB
padding bytes, followed by the required two EOT responses, Files/Main input,
normal DOS exit and restored UART/PIC/vector/timer state.

The observer captures `Carrier lost` before `RX complete`; its raw loss row,
including a trailing `t`, is retained verbatim. Official FileBase counts are23
before both attempts and24 afterward, with one successful download log. Eight
new controls reject missing/reversed/disagreeing/truncated/invalid notice
captures in addition to the23 adapter/audio/protocol/boundary controls. The
independent positive audit reads the same notice validator. No missing notice
or other gate is waived.

This accepts one software bridge-process failure/restart with fresh per-call
VMs and emulated DCD. Long-lived bridge reuse, analog waveform-loss behavior,
broader timing/protocol/profile/UI coverage, ENiGMA and physical hardware remain
separate requirements.

## Guest audio diagnosis

`synthmodem_posttrain_trace_runtime.py` stages the normal pinned post-training
runtime with the existing PCM-export daemon. It verifies every runtime file and
every initramfs entry: the only changed existing archive body is the daemon's
init hook, and the only added entry is the exporter. JavaScript, kernel and modem
binaries retain their normal identities. The QEMU wrapper supplies a separate
export channel; it does not replace online serial bytes.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_posttrain_trace_runtime.py \
  --output build/bbs-lab/synthmodem-posttrain-trace-runtime-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_reconnect_dos.py \
  --runtime build/bbs-lab/synthmodem-posttrain-trace-runtime-NEW/runtime \
  --trace-runtime-proof build/bbs-lab/synthmodem-posttrain-trace-runtime-NEW/result.json \
  --key-checks build/bbs-lab/audio-reconnect-keys-NEW/result.json \
  --notice-checks build/bbs-lab/reconnect-notice-NEW/result.json \
  --receive-trace --diagnostic-watchdog 14400 \
  --output build/bbs-lab/synchronet-audio-integrity-trace-NEW
```

This mode always records `diagnostic: true` and `passed: false`, and exits
unsuccessfully even if every workflow check passes. Exporting PCM before SIP
shutdown changes failure timing. The shorter diagnostic watchdog also keeps each
raw PCM export within the existing 16 MiB per-file limit. Neither change belongs
to production compatibility acceptance.

After a call exits and exports its captures, analyze its actual `CALL` directory:

```sh
./tools/modem-dev --command python3 lab/bbs/analyze_receive_trace.py CALL
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js RUNTIME CALL
./tools/modem-dev --command node lab/bbs/diagnose_receive_pcm.js RUNTIME CALL
```

The analyzer binds the actual frontend receipt (`node-result.json` for nested
calls), its prefix-count log, host RTP/tunnel packets, guest PCM and byte captures.
Comparison with guest PCM separates a changed media waveform from later decoder
or framing errors. A clean diagnostic call does not resolve an intermittent
failure observed in a different call; retain both captures and their scope.

The [first current-terminal trace](../../docs/validation/synchronet-audio-integrity-trace-01.json)
exports successfully and exits naturally through its14400-tick keyboard
watchdog. DOS, all42 hardware bytes and the timer vector restore. It does not
receive a file or inject the intended bridge-stop/retry fault. The final screen
retains an ASPECT error3/D4/step106, and the adapter retains its error that the
frontend did not exit within15s after serial close. VM retirement/export still
finish; these observations do not waive either workflow or adapter acceptance.

All39,948 caller and tunnel RTP packets are identical and sequence/timestamp/SSRC
continuous, with no observed host arrival gap above35ms. The entire6,280,000-sample
guest waveform reconstructs exactly as three startup silence frames, the first
9067 RTP frames, one160-sample silence frame, two more RTP frames, another silence
frame, and the remaining RTP prefix through frame39244. These two in-call20ms
silences shift the audio delay from60ms to100ms. The caller decoder recovers
all101 authored bytes; the actual guest emits109 bytes and an independent native
decoder of the guest PCM emits110. Both corruptions occur at authored offset76.
The two decoders need not make identical decisions on a damaged waveform.

This proves a media discontinuity before decoded-byte framing in this call.
It does not yet identify the internal buffering/scheduling cause, prove the
earlier untraced event had the same cause, or resolve the ASPECT error. Controlled
delay growth is the next diagnostic; normal full DOS acceptance remains separate.

## Retained failure: second ASPECT invocation

Terminal `976ba8d0` passes fifteen of the nineteen producer gates. The first
call receives ten exact CRC-validated blocks (10,240 source bytes); DOS has
flushed an exact 8,192-byte partial when the observer stops the bridge. Actual
SIP session end precedes frontend EOF. DOS observes `RX carrier lost`, removes
the partial, redials, and updates the directory for both calls.

Both DSPs train at 1200 on the second call and its complete `CONNECT>` banner
arrives. No online byte leaves DOS on that call, and no second BBS connection
opens. The final captured screen reports:

```text
ASPECT: unsupported command or service (error 3, opcode D4, step 2)
```

The status label also shows `57600.ASX`. This is an observed label, not proof
of which file the runtime opened. The compiled `AUDIO.ASX` still matches the
maintained compiler output. The independent keyboard watchdog eventually exits
normally: all 42 UART/PIC/vector bytes and the original timer vector restore.
Retry completion, exact retry file, expected receive directory and second BBS
connection gates remain failed. No product-code fix has been made and the root
cause remains unidentified.

The first call's final ACK exists in DOS input and independent offline caller
audio, but is absent from the guest/BBS stream when shutdown cuts the call.
The guest and BBS input are exact authored prefixes with that one-byte tail
missing. The strict first-call full-input-identity condition therefore also
remains unaccepted; it is not hidden by trimming or waived because the first
login worked. A future interrupted-stream policy needs explicit failure-boundary
timing and negative controls before accepting an in-flight suffix loss.

The current producer instead waits until the passive BBS relay has received the
entire authored online prefix ending in ACK, while DOS still has an incomplete
source file. It records that boundary before stopping the bridge. Seven observer
checks retain the original in-flight-ACK mismatch, reject wrong/duplicate/missing
bytes, and release only the delivered prefix. The independent audit retains its
full upstream identity requirement and also verifies the recorded boundary's
hashes and ordering. This changes fault timing; it does not permit missing bytes.

Both serial ownership audits pass their byte/callback/error accounting with the
declared shutdown directions. On the interrupted call, the original JSON
snapshot was saved before its socket-close callback. The independent audit uses
the complete raw structured log, requires the JSON events to be its exact
prefix, and verifies SIGTERM -> shutdown -> EOF plus the final close in stopped
phase. The earlier snapshot-only failure and source are retained. The unchanged
ordinary close-before-shutdown auditor is not relabeled as a passing fault audit.

The [queue probe](diagnose_reconnect_script_queue.py) executes the linked
XMODEM owner and script queue with modeled hardware/DOS: both a completed
download and a carrier drop after ten ACKs queue the next script. It does not
run the second interpreter and does not reproduce or explain this live failure.
Next isolate the two-script/transfer path with a short captured-transport replay,
then observe the selected script path, command tail and directory/renderer state
across the first transfer. Fix only the demonstrated cause and repeat the actual
audio campaign with all failed gates retained. The complete positive auditor
and its corruption controls remain pending a passing campaign.

## Captured-transport diagnosis

`replay_reconnect_dos.py` replays the first call's captured online output and
waits for its recorded DOS input in causal order. It shortens transmission and
idle time; it is not a live BBS or audio acceptance test. `--flex-cpr` allows
bounded native cursor-position replies to differ on the second screen, recording
each difference. All other expected input and all remote output remain exact.
Without that option, a legitimate changed cursor position stops the fixture.

The isolated `build_renderer_rejection_diagnostic.py` builder starts from a
Git archive and retains every renderer rejection. Optional boundary, key and
ASPECT first-error traces identify foreground failure state. The production
terminal and runner stay untouched. Additional DOS logging changes timing and
code layout, so diagnostic binaries cannot count as production acceptance.

The replay exposed a keyboard-helper defect: after Alt-D, the old transfer
prompt can remain visible while the second script logs in. The helper accepts
that stale prompt and queues Alt-R. The traced parent receives raw key `1300`
(record `5300`, with the diagnostic key tag), and the child's first error is
unsupported3 during WAITQUIET/D5 at step13 with last key `1300`. Both interpreter
invocations receive `AUDIO.ASX`; the `57600.ASX` display observation in the older
run does not establish an opened filename. This identifies a replay failure
caused by the test helper, not an unsupported WAITQUIET opcode.

A [retained diagnostic receipt](../../docs/validation/reconnect-stale-prompt-diagnosis.json)
binds the trace, command lines, normal cleanup and regression artifacts.
A separate actual-DOS fixture retains the old transfer prompt after redial,
requires silence, clears it, and then presents a fresh prompt. The old helper
fails both carrier-notice variants; waiting for disappearance before rearming
passes both plus the independent watchdog/timer-restoration case. With unchanged
production terminal/ASPECT, the corrected helper completes both captured login
and partial-transfer sequences with exact input apart from one recorded native
cursor-position reply. Both intentionally interrupted captures contain113 input
and39,662 output bytes, and DOS/hardware/timer cleanup passes. This is not a
complete retry. The original audio campaign still requires a repeat with the corrected helper before its
failure can be attributed to the same cause or reconnect can be accepted.

To reproduce the instrumented build and replay:

```sh
./tools/dev --command python3 lab/bbs/build_renderer_rejection_diagnostic.py \
  --revision 8246dbb --boundary --keys --runner \
  --output build/bbs-lab/render-diagnostic-NEW
./tools/dev --command python3 lab/bbs/replay_reconnect_dos.py \
  --cohort build/bbs-lab/current-synchronet-reconnect-audio-01 \
  --terminal build/bbs-lab/render-diagnostic-NEW/source/build/terminal/TERMINAL.EXE \
  --runner build/bbs-lab/render-diagnostic-NEW/source/build/aspect-runner/ASPECT.EXE \
  --flex-cpr --output build/bbs-lab/reconnect-replay-NEW
```

The replay uses the current helper by default. The retained failure uses the
older helper identity recorded in its receipt. `--keys` accepts an isolated
helper under build storage to compare that identity against a candidate fix.
The real producer also accepts `--diagnostic-terminal` and a diagnostic-only
watchdog override; those runs always have `passed:false` regardless of other
checks, and cannot be promoted to production compatibility acceptance.

`RGUARD.BIN` contains 64-byte records. The first word is a policy source line,
`8000 | service` at a native unsupported boundary, or `4000 | raw-key` at key
dispatch. The next thirteen words record terminal ID, cursor row/column,
video/attribute offset, connection state, parser/wait/transfer owners and
program/ASPECT owners. Bytes28–43 retain the queued script, bytes44–56 its label.
`AERROR.BIN` contains thirteen-word records: magic4152, first error, prior error,
opcode, step, serial owner, render attachment, serial/pacing errors, RX count,
last key and the low/high BIOS tick words. `AARGS.LOG` records each invocation's
actual command-line arguments. These formats apply to the final builder's
optional instrumentation; earlier retained builds identify their own schema.

## Complete retry with a missing loss-notice capture

The [second normal-binary run](../../docs/validation/current-synchronet-reconnect-audio-02.json)
passes18 of19 producer gates. The partial file contains8,192 exact source bytes;
the audio contains10,240 verified source bytes before the first bridge stops.
Both calls preserve every authored upstream byte:113 on the interrupted call,
121 on retry. The retry validates fourteen CRC blocks, EOT NAK/ACK, the exact
11,521-byte source plus127 padding bytes, Files/Main and normal DOS/UART/timer
return. Both independent serial audits pass13 checks each. Official FileBase
metadata passes seven checks: both calls display download count21, the final
count is22, and exactly one successful download is logged. Twenty-three damaged
byte, audio, protocol, timing and stop-boundary variants reject.

This run remains `passed:false`. The footer-only timer recorded `RX complete`
but missed the loss notice on another row. The explicit `--diagnostic` audit
verifies the completed transport/protocol path only when that is the sole failed
producer gate. It writes a separate `reconnect-diagnostic-audit.json` with
`passed:false`; neither that audit nor diagnostic negative controls accepts
overall compatibility. The normal positive auditor still requires a passed
producer and independently parses ordered loss/completion frames.

The replacement observer scans every row for the complete `RX carrier lost`,
`Carrier lost` and `RX complete` prefixes, deduplicates retained rows and keeps
scanning after an old notice. An actual8086 DOS regression shows the old observer
missing row22 loss and accepting partial/wrong prefixes. The same probe with
the replacement passes all six checks, captures simultaneous row0 loss/row24
completion, leaves the keyboard untouched and restores all42 hardware/vector
bytes. The producer requires that tested observer's proof before execution.
A fresh real audio campaign remains mandatory.

The diagnostic audit's first recursive manifest also hashed its own redirected
CLI output before the final print. That stale-hash record and source are retained
in the cohort. CLI logs are now excluded from the protocol manifest; all actual
byte/event/JSON inputs remain hashed. The corrected86-file manifest is verified
after process exit. This repair does not waive the missing loss-notice gate.

## Repeat exposes an upstream integrity failure

The [next normal-binary repeat](../../docs/validation/current-synchronet-reconnect-audio-03.json)
never reached the planned interruption: its strict stop condition refused a
mismatched upstream stream. DOS authored119 online bytes, and independent caller
audio decoding recovers exactly those119 bytes. The guest DATA_RX records and
BBS input instead contain123 bytes. Four bytes, `3c d2 25 fc`, appear at authored
offset77 after `TJ` and before area selection. They arrive as four separate
one-byte guest data records. Both captured external RTP streams retain sequence,
timestamp and SSRC continuity, and all13 serial-ownership checks pass.

The first download still recovers the exact source plus padding. That does not
repair terminal-input integrity or make this a reconnect pass. No first-call
fault was injected and no second call started. The owned DOS test was stopped
after the complete first file established that the required partial-fault route
could no longer occur; normal DOS/UART/timer cleanup is not claimed. The stop
decision, actual signals and unchanged input identities are retained.

This localizes the first observed discrepancy after the caller waveform and
before BBS input. It does not distinguish guest media alteration, datapump
decoding or helper framing. This normal run has no guest PCM/arrival-timing
export, so the next investigation must retain those boundaries before blaming
packet loss, jitter discard or a DOS defect. The tested full-screen observer
still needs an actual loss/completion run. Overall audio integrity and reconnect
acceptance remain open alongside current ENiGMA and physical commissioning.
