# Normal recorder workflow over the software modem

The [carrier-build checkpoint](../../docs/validation/recording-abort-carrier-audio.json)
accepts parent7b6ded5c/runnerdfee1e95 on the normal recorder route. All26
producer,34 independent and12 serial checks pass:60,926 BBS display bytes
plus187 bridge bytes arrive exactly, with78 online bytes independently
waveform-decoded. Normal hardware/timer/SIP/VM cleanup passes.
[Fresh direct BBS recorder/replay](../../docs/validation/bbs-abort-carrier-compat.json) and
[stock-window checks](../../docs/validation/bbs-abort-carrier-window.json) also pass.
This does not cover script-time windows over audio, full parent carrier/status,
other profiles or physical hardware. Older checkpoints keep their identities.

The [confirmation-build run](../../docs/validation/recording-abort-owner-audio.json)
accepts parent7b6ded5c/runner12d40249 and24KB compilerfc200c8c on this normal
route. All26 producer,34 independent and12 serial checks pass. All60,389 BBS
display bytes plus187 bridge bytes arrive exactly, and independent caller
waveform decoding matches77 online bytes. No gateway errors or failed, skipped
or pending writes remain; hardware/timer/SIP/VM cleanup passes.
[Preparation](../../docs/validation/recording-abort-owner-audio-preparation.json)
binds the unchanged seven BIOS probes/56 assertions and a fresh13-check
DOS/Telnet control to these products. Script-time windows over audio, other
routes/profiles, physical hardware and full application gates remain open.
The earlier checkpoints below retain their recorded product identities.

The `recording` route exercises the application's normal File/C recording and
File/A explicit ASP compilation/replay on the existing owned ENiGMA fixture.
It uses the source-built terminal, ASPECT and DOS ASPCOMP. The selected route is
File Base → Search → File Base; after replay, manual input opens Search again.
No generated recording is edited or compiled by the host before replay.

The [current PAUSE-build run](../../docs/validation/recording-pause-audio.json)
accepts parent0eff2348/runner2c80e45c for this selected route:26 producer,
34 independent and12 serial checks pass. All60,929 display bytes plus187 bridge
bytes arrive exactly, and independent caller decoding matches77 online bytes.
Normal hardware/timer/SIP/VM restoration passes without gateway errors or failed,
skipped or pending writes. [Fresh preparation](../../docs/validation/recording-pause-audio-preparation.json)
binds seven BIOS probes/56 assertions and13 actual DOS/Telnet checks to the same
helper/runtime/products. Other peers/profiles, script-time windows over audio,
physical hardware and full application gates remain open. Older runs below
retain their exact earlier binary identities and scopes.

The [accepted run03](../../docs/validation/recording-audio-03.json) passes26
producer,34 independent and12 serial-evidence checks. Its complete60,383-byte BBS
display plus187-byte bridge prefix survives the DSP path exactly; independent
caller waveform decoding matches77 online bytes. Recording, DOS compilation,
replay and manual Search finish normally, with no gateway errors or failed,
skipped or pending frontend writes. DOS/UART/PIC/IRQ/timer/SIP/VM restoration
passes. This is one selected owned stock ENiGMA V22/1200 software-audio workflow;
other peers/profiles, physical hardware and full application gates remain open.
Preparation and failed attempts below remain historical evidence.

The BIOS helper waits for visible shell/BBS markers and inserts real BIOS key
words. Startup first requires the actual ASPECT script to emit `RECORDER READY`
after its final wait and success-log close. Visible File Base alone cannot admit
Alt-Z. The helper never writes product state, serial bytes, terminal replies or a
success file. A private report distinguishes completion from its watchdog. The
replay's Search heading is latched before accepting the returned File Base
footer, so stale pre-script text cannot finish replay. The heading is observed
early because the final Search footer can be transient on a fast connection.

The [preparation record](../../docs/validation/recording-audio-ready-preparation.json)
binds six actual8086 BIOS probes and a complete actual DOS/Telnet BBS control.
The probes cover missing/stale markers, initial/final watchdogs and a full BIOS
keyboard queue. The control verifies source/payload, DOS compilation, the exact
record/replay/manual route, serial bytes, normal exit and timer restoration.
The [first audio failure](../../docs/validation/recording-audio-early-menu-failure.json)
retains an intentional diagnostic stop, exact transport audits and a VGA text
snapshot. The former File Base trigger delivered Alt-Z while startup ASPECT
still owned WAITQUIET/D5; the snapshot shows typed error3 and private helper state
shows one delivered key, phase1. A controlled dump preserved this evidence; it
was not an unexplained emulator crash. Temporary extracted cores were deleted.
The new BIOS counterexample displays File Base without readiness and requires
watchdog retirement without opening the menu. Unsupported local UI during an
ASPECT child remains an application gap; this driver respects its ownership.
Earlier driver/probe/fixture failures remain retained. Preparation does not
establish software-audio acceptance.

The [second audio failure](../../docs/validation/recording-audio-final-page-failure.json)
completed recording, DOS compilation/replay, manual Search and normal hardware
restoration. It remains unaccepted: the received display is an exact 60,456-byte
prefix of the 60,929-byte BBS display, and the gateway reports `read ECONNRESET`.
The helper exited after the Search footer before 473 late form bytes arrived.
Local write callbacks do not establish that DOSBox consumed those bytes; the
kernel unread count was not traced.

The corrected final gate requires the late `advanced search` and `-ALL-` fields,
the focused input cursor at row 12, column 38, and 180 BIOS ticks of unchanged
screen characters, attributes and cursor before exiting. Seven BIOS probes now
include a visible footer without the late form and a changing final screen that
must restart the quiet interval. These checks supplement the mandatory complete
byte-stream and zero-gateway-error audits; they cannot replace them.

Use fresh labels and outputs:

```sh
./tools/dev --command python3 lab/bbs/check_audio_recording_keys.py \
  --output build/bbs-lab/recording-audio-keys-NEW
./tools/dev --command python3 lab/bbs/check_audio_recording_tcp.py \
  --keys build/bbs-lab/recording-audio-keys-NEW/result.json --label recording-control-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-buffered-runtime-01/runtime \
  --buffered-runtime-proof build/bbs-lab/synthmodem-buffered-runtime-01/result.json \
  --route recording \
  --recording-key-checks build/bbs-lab/recording-audio-keys-NEW/result.json \
  --recording-tcp-checks build/bbs-lab/results/enigma/recording-control-NEW/recording-checks.json \
  --output build/bbs-lab/current-enigma-recording-audio-NEW
```

Only numeric ATD1 starts the call. The inherited login script waits for the real
CONNECT> prompt and supplies the loopback BBS destination as online data. All
online bytes cross the originating/answering DSPs, PCMU/RTP, SIP, guest helper
and Telnet path. The existing200ms buffered runtime and250ms input framer remain
unchanged. Workstation test configuration is distinct from Boca initialization.

After the run completes, audit the actual bytes and cleanup:

```sh
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js \
  build/bbs-lab/synthmodem-buffered-runtime-01/runtime \
  build/bbs-lab/current-enigma-recording-audio-NEW
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py \
  build/bbs-lab/current-enigma-recording-audio-NEW
./tools/modem-dev --command python3 lab/bbs/audit_synthmodem_audio_dos.py \
  build/bbs-lab/current-enigma-recording-audio-NEW
```

The producer and independent audit require the generated source and bytecode,
complete recording-helper progress, exact BBS route/user bytes and manual Search.
Existing whole-stream guest/serial/Telnet/caller identity, RTP continuity, SIP
teardown, hardware/timer restoration and source-custody checks still apply.
The helper bounds the full workflow to32000 BIOS ticks; the outer process limit
is1900 seconds. Failed prerequisites remain failures. This lab does not test the
physical Boca/SPA2102, promise14.4 negotiation or close any full F01–F16 gate.
