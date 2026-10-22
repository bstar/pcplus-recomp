# Normal recorder workflow over the software modem

The `recording` route exercises the application's normal File/C recording and
File/A explicit ASP compilation/replay on the existing owned ENiGMA fixture.
It uses the source-built terminal, ASPECT and DOS ASPCOMP. The selected route is
File Base → Search → File Base; after replay, manual input opens Search again.
No generated recording is edited or compiled by the host before replay.

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
