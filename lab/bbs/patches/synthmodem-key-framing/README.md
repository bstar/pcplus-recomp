# Optional serial key framing

This isolated SynthModem candidate builds on the accepted carrier runtime at
upstream commit `b1752e4d0039e0cff72735924e03aa99922723a8`. PCPlus continues to
send its ordinary ANSI key sequences over the serial modem. The Linux bridge
can retain an incomplete sequence and send its complete bytes in one TCP write.
No DOS keyboard mapping, BBS code, installed service or modem binary changes.

The stock ENiGMA decoder's per-input-event parsing is a known separate defect.
Single-byte Home/End/Insert aliases were previously rejected because the compose
controller binds Ctrl-A to subject editing. This candidate keeps the complete
keyboard recipe, rather than substituting a subset of supported keys.

`config.telnet.inputSequenceTimeoutMs` explicitly enables framing when it is an
integer from1 through2000. An unset/zero value retains immediate forwarding.
The actual DOS experiment uses250ms. Plain CP437 text and control keys forward
immediately. ESC-prefixed keys, CSI/SS3 sequences, DA/CPR responses, Linux console
function keys and X10 mouse packets are retained until complete. Invalid input
and the128-byte retention limit flush the exact accumulated bytes. A lone Escape
flushes at an absolute first-byte deadline; later bytes do not extend it.
An incomplete sequence at connection teardown is retired with that connection,
never delivered to a replacement socket. The existing Telnet codec still owns
BINARY/NVT and IAC escaping after this framing step.

No byte is translated, filtered or generated. Enabling this option can delay an
ESC-containing binary payload by up to the configured deadline, and it is not a
file-transfer acceptance claim. Keep the option disabled for general raw-byte
use until transfer tests establish the desired timing behavior. The default
remains disabled. Framing is selected for the whole lab call; automatic
transfer-mode switching and per-destination configuration are not implemented.

TCP does not preserve write boundaries. Sending a complete key in one write
helps the observed local server but cannot guarantee arbitrary remote ENiGMA
behavior. A server decoder that retains incomplete sequences remains the robust
end-to-end solution. This candidate must pass the actual DOS/audio editor test
and byte-integrity audit before even that local workflow is accepted.

## Reproduction

Use fresh ignored output directories and the pinned Nix toolchain:

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_key_framing_runtime.py \
  --output build/bbs-lab/key-framing-new
./tools/modem-dev --command node lab/bbs/patches/synthmodem-key-framing/check.js \
  build/bbs-lab/key-framing-new/runtime > build/bbs-lab/key-framing-new/checks.json
./tools/modem-dev --command node lab/bbs/patches/synthmodem-key-framing/check_loopback.js \
  build/bbs-lab/key-framing-new/runtime build/bbs-lab/key-framing-new/loopback.json
./tools/modem-dev --command python3 lab/bbs/synthmodem_audio_dos.py \
  --key-framing --route editor \
  --runtime build/bbs-lab/key-framing-new/runtime \
  --output build/bbs-lab/audio-key-framing-new
./tools/modem-dev --command python3 lab/bbs/audit_synthmodem_audio_dos.py \
  build/bbs-lab/audio-key-framing-new
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js \
  build/bbs-lab/key-framing-new/runtime build/bbs-lab/audio-key-framing-new
./tools/modem-dev --command python3 lab/bbs/analyze_audio_integrity.py \
  build/bbs-lab/audio-key-framing-new
./tools/modem-dev --command python3 lab/bbs/record_synthmodem_key_framing.py \
  --cohort build/bbs-lab/audio-key-framing-new --staging build/bbs-lab/key-framing-new
```

The DOS driver validates the staged runtime against the checked-in staging
receipt; it requires identical runtime file identities. Staging changes exactly
TelnetProxy.js and adds InputSequenceFramer.js. Config defaults, boot archive,
kernel, backend, DSPs, helper and all other source files retain their accepted
carrier identities. Staging validation alone is not runtime acceptance.

The deterministic checks cover every two-part split and singleton1200-baud
delivery of supported keys/replies, immediate plain input, lone Escape,
absolute timeout under trickle input, malformed/oversize input, all256 byte
values at all two-part splits and singleton boundaries, close and reconnect,
default-off behavior, actual proxy integration and the real codec's IAC escaping.
The real loopback control/candidate comparison records paced Home arriving as
three separate application events with framing off and one with framing on;
both preserve259 bytes of exact duplex data including all256 values.

## Actual audio result: failed prerequisite

The first DOS/audio candidate, `synthmodem-audio-editor-03`, never reaches the
editor. The server logs an authenticated Main Menu, but ASPECT exhausts its
main-menu wait and writes `FAIL-MAIN`. The owned emulator is then explicitly
stopped because its test-only BIOS helper is still waiting for KEYTEST. The
stop is recorded; normal DOS exit and UART/vector restoration are **not** claimed.
No post is saved and the actual SIP/VM cleanup completes without gateway errors.

All63 authored online DOS bytes are independently decoded from the caller
waveform. The guest instead emits72 bytes: an insertion of
`8b32f7c7a30dc800ff` at authored offset60. Its entire stream equals the Telnet
application input, so these extra bytes precede the framing/proxy output. The
full35173-byte BBS display plus187-byte bridge prefix survives downstream exactly.
There is no guest PCM/timing capture for this normal-image call; the cause of
the insertion, and its relation to the missed script prerequisite, remain unproven.

The [combined receipt](../../../../docs/validation/synthmodem-key-framing.json)
keeps11 passing component checks, the actual TCP comparison, the failed23-check
producer,32-check independent audit, offline decoder and negative integrity
diagnosis. Actual editor behavior is **not reached**, not accepted. This remains
an opt-in lab candidate; it replaces no accepted runtime. Next collect PCM/timing
with this candidate and make login-ready detection tolerate asynchronous art
callbacks while retaining actual main-menu/editor entry requirements. Do not
trim the extra bytes, patch the stock BBS or shorten its art to obtain a pass.

The patch contains excerpts of GPL-2.0-or-later SynthModem source. Original
notices are retained in [the shared upstream notice file](../synthmodem-telnet/UPSTREAM-NOTICES.txt).
Maintained candidate and test JavaScript is GPL-2.0-or-later.
