# Minimum post-training hold

The actual retry01 logs5999ms against the unchanged6000ms minimum. Its exact
client transfer/recovery workflow passes, but overall acceptance stays false.
The retained CallSession method also attaches when a modeled timer callback
arrives at5999ms. Timer delivery alone does not establish elapsed hold time.

The separate candidate uses monotonic `process.hrtime.bigint()` for minimum,
quiescence and cap measurements. Both callback paths check elapsed minimum;
an early timeout leaves the100ms interval active to finish the wait. The
minimum dominates an attach cap configured below it. Elapsed logging uses an
integer floor. Config defaults and external protocol behavior are unchanged.

[Stage/component evidence](../../docs/validation/synthmodem-posttrain-runtime.json)
passes14 modeled boundary cases and one real default6000ms Node timer run.
They execute the actual candidate method, modeling timer/clock and DSP/Telnet
boundaries without starting SIP/VM/audio. Cases cover early/exact/late callbacks,
interval-first order, shorter cap, quiescence, sustained-data cap, inactive and
duplicate callbacks, wall-clock jumps, zero and fractional boundaries.

The stager validates every input of the accepted framed runtime and copies it
to fresh ignored storage. Exactly one source file changes: CallSession.js.
Kernel, initrd, DSP/helper/backend/Telnet code, defaults and original runtime
remain byte-identical. The validator requires the candidate's exact sealed file
set and hashes. No installed service is changed.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_posttrain_runtime.py \
  --output build/bbs-lab/synthmodem-posttrain-runtime-NEW
./tools/modem-dev --command node lab/bbs/check_posttrain_hold.js \
  build/bbs-lab/synthmodem-posttrain-runtime-NEW/runtime \
  build/bbs-lab/posttrain-hold-checks-NEW
```

This accepts the isolated stage and component scope only. A fresh complete
SIP/audio/DOS/BBS retry run must keep all original byte, CRC/control/storage,
closing ownership, source/stat, post-transfer input and cleanup gates. Receiver
temporary cleanup, pressure/loss, other peers, physical Boca/SPA2102 and F01-F16
application requirements remain open.


## Fresh audio retry

The [fresh board preparation](../../docs/validation/audio-posttrain-retry-preparation.json)
passes navigation/isolation and binds the sealed component runtime. The
[completed retry02](../../docs/validation/synthmodem-audio-upload-retry-02.json)
passes all81 producer and independent workflow gates. The explicit profile includes the existing key framing;
the DOS binary, source size, DTE, DSP and receiver helper are unchanged.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --posttrain-hold --route upload --upload-cancel-retry \
  --upload-key-checks build/bbs-lab/audio-upload-retry-keys-01/result.json \
  --fixture-lab build/bbs-lab/enigma-posttrain-retry-candidate-NEW \
  --runtime build/bbs-lab/synthmodem-posttrain-runtime-01/runtime \
  --output build/bbs-lab/synthmodem-audio-upload-retry-NEW
```

Use a fresh prepared board and cohort. After natural producer exit, run the
independent complete byte/cleanup, ownership, offline caller, v2 retry, control-
time and final relay-closure audits. Passing cohorts use the timing verifier
without `--protocol-only`; failed cohorts retain any separate failure. Inputs
stay frozen through all audits. Retry02 logs6002ms, preserves exact14361 online
DOS and78322 display bytes, completes12 unreplayed data packets and the exact
11521-byte official file, then resumes real search/list with normal hardware/
timer restoration. All78531 frontend bytes complete without skipped/failed/
pending bytes. Final OO reaches the relay before helper exit, with both
premature-control mutants rejected under full passing transfer audit. Stock
helper/upload and prior captures remain unchanged.

This accepts this explicit timer/receiver candidate audio workflow. It does not
close unmodified-stock behavior, receiver partial cleanup, broader sustained
pressure/cancel/loss, Synchronet audio, physical or F01-F16 gates.
