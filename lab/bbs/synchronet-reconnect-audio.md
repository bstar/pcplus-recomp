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
loss. A test-only BIOS helper waits for the visible `RX carrier lost` notice,
then presses Alt-D. The fresh call starts another frontend/VM and trains both
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
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_reconnect_dos.py \
  --runtime build/bbs-lab/synthmodem-posttrain-runtime-01/runtime \
  --key-checks build/bbs-lab/audio-reconnect-keys-NEW/result.json \
  --output build/bbs-lab/current-synchronet-reconnect-audio-NEW
```

After natural producer exit, run the independent reconnect serial ownership audit
and offline caller decoder on each `COHORT/call-1` and `COHORT/call-2`, then:

```sh
./tools/modem-dev --command python3 lab/bbs/audit_audio_reconnect_io.py CALL
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js RUNTIME CALL
./tools/modem-dev --command python3 lab/bbs/audit_synchronet_reconnect_audio.py COHORT
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
