# Actual DOS through audio to Synchronet

The owned official archived Synchronet snapshot remains on127.0.0.1:23231.
The independent reference route logs in with the synthetic account, reads
bulletin1, visits Files, returns to Main, reads the empty Local General/Notices
area and dismisses its pause. No messages, mail, doors or file transfers are
requested. The exact official ELF is verified against its pinned archive.

[Preparation evidence](../../docs/validation/synchronet-audio-preparation.json)
passes seven reference checks and six actual DOS BIOS-observer checks. The
first reference reached every prompt but incorrectly treated ctrl/dsts.ini as
immutable configuration. Official getstats.c/logon.cpp identify it as daily
runtime statistics; the corrected reference tracks it separately, requiring
message/mail/transfer counters to stay unchanged. Original diagnostic artifacts
remain preserved. Code/config/menu files, loaded library files and message-body
bytes stay exact. No server reinstall, restart or configuration change occurs.

The observer watches actual visible File -> empty-message -> fresh Main/footer
phases. Old main text behind the message pause cannot trigger exit. It inserts
only one BIOS Alt-X after the final screen; its separate watchdog provides no
workflow acceptance. Tests verify both paths and original INT1C restoration.
The source-built ASPECT script supplies the observed read-only navigation.

The first audio cohort ran with the pinned monotonic minimum-hold/key-framing
runtime, unchanged DOS binary,38400 DTE and V22/1200 DSP. A passive explicit-port
loopback relay preserves both complete wire directions and event offsets. All
source/runtime/tool inputs, server code/config/menu/library files, official log
boundary, statistics and message bodies are recorded. Inputs/auditors remain
frozen through producer exit and every same-run independent audit.

```sh
./tools/bbs-dev --command python3 lab/bbs/audio_synchronet.py \
  --reference-output build/bbs-lab/synchronet-audio-reference-NEW
./tools/dev --command python3 lab/bbs/check_audio_synchronet_keys.py \
  --output build/bbs-lab/audio-synchronet-keys-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-posttrain-runtime-01/runtime \
  --reference build/bbs-lab/synchronet-audio-reference-NEW/result.json \
  --key-checks build/bbs-lab/audio-synchronet-keys-NEW/result.json \
  --output build/bbs-lab/synthmodem-synchronet-audio-NEW
# After natural producer exit:
./tools/modem-dev --command python3 lab/bbs/audit_synchronet_audio_dos.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py COHORT
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js RUNTIME COHORT
```

The independent audit requires exact full guest/serial/Telnet/caller streams,
minimum hold, real native terminal replies, ordered server prompts and exact
read-only commands, official login evidence, hardware/timer restoration,
continuous RTP, SIP teardown and frozen inputs. This grants no audio acceptance
until all gates pass. Editor/transfer workflows, sustained pressure/loss,
physical Boca/SPA2102 and F01-F16 whole-application requirements remain open.


## First actual failure

[Audio01](../../docs/validation/synthmodem-synchronet-audio-01.json) reaches the
real bulletin menu. The recipe incorrectly waits for the visible text
`Enter number of bulletin or [Quit]` as a literal raw token. Actual bytes insert
SGR escapes inside Quit; the [raw recipe diagnostic](../../docs/validation/synchronet-audio-recipe-01.json)
finds both such waits absent from independent raw captures. All other generated
remote wait tokens are present and the ASPECT recipe compiles.

All57 upstream online bytes match the native sender, independent caller decode,
actual guest and target-plus-BBS stream. All10542 display bytes survive, plus an
exact source-defined remote-close/menu suffix after the BBS inactivity timeout.
The original complete-caller gate remains failed, and no navigation acceptance
is granted. Native25;80 CPR, rendered bulletin content, official login, unchanged
server/message bodies and normal DOS/UART/PIC/IRQ/timer/SIP cleanup are retained.
The configured watchdog ends this failed test; no running input was changed.

Fix both waits to a stable raw prefix and require every generated wait token to
appear in its independent raw phase capture before a fresh audio run. Keep
all original acceptance gates and the first failed report/captures unchanged.
