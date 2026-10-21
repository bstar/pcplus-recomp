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
./tools/modem-dev --command python3 lab/bbs/check_synchronet_audio_recipe.py \
  --reference build/bbs-lab/synchronet-audio-reference-NEW \
  --output build/bbs-lab/synchronet-audio-recipe-check-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-posttrain-runtime-01/runtime \
  --reference build/bbs-lab/synchronet-audio-reference-NEW/result.json \
  --key-checks build/bbs-lab/audio-synchronet-keys-NEW/result.json \
  --recipe-checks build/bbs-lab/synchronet-audio-recipe-check-NEW/result.json \
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


## Corrected raw-token run

Both bulletin needles now stop at the opening bracket before ANSI highlight
codes. The [recipe proof](../../docs/validation/synchronet-audio-recipe-02.json)
compiles and matches all13 remote wait tokens against their corresponding raw
reference phases. The producer requires `--recipe-checks`, validates every
recorded source/capture hash and freezes that prerequisite alongside the
reference and observer checks.

The [completed audio02](../../docs/validation/synthmodem-synchronet-audio-02.json)
passes all65 producer, independent and ownership checks with the unchanged DOS
binary, timer/key-framing runtime, DTE, DSP and BBS listener/config/account
policy. Exact81 online bytes,26919 display bytes,6000ms minimum, real native
replies/input and the complete read-only route validate. All27128 frontend
bytes complete with no skipped/failed/pending bytes. The official archived ELF,
877 code/config/menu files, loaded libraries and message bodies preserve, while
message/mail/transfer counters remain unchanged. Normal DOS/UART/PIC/IRQ/timer/
SIP restoration passes. The independent offline caller matches every byte.

The first failed audio capture, reports and raw-token diagnostic stay unchanged
(source checkpoint d03c179). Acceptance is limited to this captured navigation
workflow; editor/transfer, sustained pressure/loss, arbitrary-peer, physical and
F01-F16 application gates remain open.


Seal a fully audited navigation run after all independent checks:

```sh
./tools/modem-dev --command python3 lab/bbs/record_synchronet_audio.py COHORT \
  --output docs/validation/synthmodem-synchronet-audio-NEW.json
```

The recorder requires exact frozen source/runtime/tool/server inputs, unchanged
message bodies/counters, all original acceptance checks, raw recipe/reference/
observer prerequisites, full independent offline decode and native/guest/BBS/
caller identity. Its positive result grants no broader application or hardware
acceptance. The sealed first failure remains separate.

## Unsaved editor workflow

The separate editor recipe uses the owned Local General area. It enters the
stock FSEditor with subject KEYTEST, clears any prior synthetic line, types
ABCDE, then exercises Home/End/Left/Delete/Insert/Tab/PgUp/PgDn/Ctrl-Y. It types
UNSAVED and sends Ctrl-Q, dismisses the abort pause and returns to Main. No
editor save command is sent. Page keys cover one-line boundary responses only.

The reference records raw responses and checks actual cursor/erase/mode/bell
behavior. The BIOS helper requires both the visible subject and Insert Mode;
neither marker alone can start its input sequence. Its independent DOS probe
reads every BIOS key and verifies timer restoration and the watchdog path.
Raw ASPECT wait tokens must match independent captures before the audio run.

```sh
./tools/bbs-dev --command python3 lab/bbs/audio_synchronet_editor.py \
  --output build/bbs-lab/synchronet-audio-editor-reference-NEW
./tools/modem-dev --command python3 lab/bbs/check_audio_synchronet_editor_keys.py \
  --output build/bbs-lab/audio-synchronet-editor-keys-NEW
./tools/modem-dev --command python3 lab/bbs/check_synchronet_editor_audio_recipe.py \
  --reference build/bbs-lab/synchronet-audio-editor-reference-NEW \
  --output build/bbs-lab/synchronet-editor-audio-recipe-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_editor_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-posttrain-runtime-01/runtime \
  --reference build/bbs-lab/synchronet-audio-editor-reference-NEW/result.json \
  --key-checks build/bbs-lab/audio-synchronet-editor-keys-NEW/result.json \
  --recipe-checks build/bbs-lab/synchronet-editor-audio-recipe-NEW/result.json \
  --output build/bbs-lab/synthmodem-synchronet-editor-audio-NEW
# After natural producer exit:
./tools/modem-dev --command python3 lab/bbs/audit_synchronet_editor_audio_dos.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py COHORT
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js RUNTIME COHORT
# Only after all acceptance checks pass:
./tools/modem-dev --command python3 lab/bbs/record_synchronet_editor_audio.py COHORT \
  --output docs/validation/synthmodem-synchronet-editor-audio-NEW.json
```

The editor audit preserves keyboard CSI sequences while removing only native
DA/CPR replies, requiring the complete exact application input. It retains the
whole-caller/guest/Telnet, RTP/SIP, server/message/counter and native cleanup
gates from the navigation audit. Successful unsaved editing grants no transfer,
multiline editor, sustained pressure/loss or physical hardware acceptance.

The [first editor audio run](../../docs/validation/synthmodem-synchronet-editor-audio-01.json)
passes every measured editing operation and Ctrl-Q abort. Its fixed20-second
final delay exits before the complete Main menu arrives at1200bps: the caller
preserves an exact prefix, missing1011 display bytes. The final DOS screen and
complete-display gates fail, and the frontend read ECONNRESET remains retained.
All130 upstream native/offline/guest/Telnet bytes match; no message is saved.
Normal DOS/UART/PIC/IRQ/timer/SIP restoration passes. This grants no acceptance.
The original captures/audits are unchanged; checkpoint5fe8fac contains their
frozen test sources, before the observer correction.

The corrected observer waits for both the rendered Read/Post Messages title and
Local-area footer before its final drain and Alt-X. The shortened DOS probe
requires normal completion before120ticks, below its180tick watchdog, so fallback
cannot hide failed observation. A partial Main title emits no exit key. The
independent watchdog and original INT1C restoration remain verified.

The [corrected editor audio02](../../docs/validation/synthmodem-synchronet-editor-audio-02.json)
passes all81 checks:30 producer,39 independent whole-stream/editor/cleanup and
12 frontend ownership. Every130 upstream byte matches the native sender,
independent offline decode, actual guest and Telnet input. All23529 BBS display
bytes match the complete caller stream after the exact187-byte bridge preamble.
The minimum hold is6000ms. All23738 frontend bytes complete with zero skipped,
failed or pending bytes; there are no gateway errors. All nine editor semantics,
the exact key sequence, Ctrl-Q abort, final rendered Main and normal DOS/UART/
PIC/IRQ/timer/SIP restoration pass. Code/config/menu/library/message bodies and
message/mail/transfer counters preserve. The DOS application binary is unchanged.

This accepts this captured one-line editor/abort workflow only. The first failed
drain remains preserved. Multiline scrolling, Synchronet audio transfers,
sustained pressure/carrier loss, other profiles/peers, physical Boca/SPA2102 and
F01-F16 whole-application gates remain open.
