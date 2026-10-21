# DOS recovery after a software audio bridge stops

This campaign combines the current source-built terminal, source-built DOS
ASPECT compiler/runner, DOSBox-X's built-in Hayes modem, the pinned real
SIP/RTP/V.22-1200 software audio path and the unchanged owned stock Synchronet
server. The [first retained run](../../docs/validation/current-synchronet-reconnect-audio-01.json)
fails reconnect acceptance; the failure is described below. Neither the producer
nor the complete independent acceptance audit has passed this campaign.

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
