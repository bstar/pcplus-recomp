# Actual DOS through audio to Synchronet

## Current terminal download repeat

The [current-build receipt](../../docs/validation/current-synchronet-download-audio-01.json)
validates terminal `976ba8d0` with source-built ASPECT `aef146fd` through the
normal, untraced SIP/RTP/V.22-1200 runtime and unchanged owned stock Synchronet.
All 25 producer, 34 independent, 12 serial ownership, six official metadata and
four control-timing checks pass. The received 11,521 source bytes plus 127 SUB
padding bytes are exact; fourteen integrity-checked blocks and the two-EOT
NAK/ACK finish precede return through Files/Main and normal DOS cleanup.
All 121 upstream online bytes and 47,237 BBS display bytes match across their
independent stream checks. Offline caller decoding independently matches DOS
input. This current-version result does not extend historical upload/cancel/retry
or ENiGMA results to the current terminal, nor establish loss/reconnect, sustained
pressure or physical modem compatibility.

The [retained environment diagnosis](../../docs/validation/current-audio-metadata-environment.json)
records the first read-only metadata command's exit 127: the modem shell lacks
`libmosquitto.so.1` for the official Synchronet `jsexec`. Run that check with the
BBS shell; the protocol/audio producer remains in the modem shell:

```sh
./tools/bbs-dev --command python3 lab/bbs/audit_synchronet_download_metadata.py COHORT
```

The original literal-count auditor still rejects its known EOT-count assumption;
the existing corrected auditor passes the complete wire/control accounting.
Both reports and the failed environment command remain retained. The central
[audio ledger](../../docs/validation/synthmodem-audio-dos.json) distinguishes
these current and historical acceptance scopes.

## Original preparation and navigation

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

## Native Escape cancellation

The cancellation cohort uses a fresh unique SXCAN001.BIN payload and unchanged
stock board/helper. Its reference sends one valid1024-byte CRC block, receives
the real ACK, then sends CAN/CAN before EOT and returns through Files/Main. Stock
retains/indexes that partial. Preparatory success is separate from server cleanup.
The [preparation receipt](../../docs/validation/synchronet-audio-cancel-preparation.json)
also binds the fresh official target/source preflight,15 raw ASPECT prompt
matches and six actual DOS helper checks. The first synthetic helper probe wrote
its progress digit using the BIOS timer's ES; its failed artifacts and checker
source are retained. The corrected probe selects video memory explicitly.

The test-only BIOS helper drives ordinary Alt-S and the actual filename field.
Zero displayed ACKed blocks cannot trigger Escape. After a visible acknowledged
block, it presses Escape, requires the local TX canceled notice, waits for the
real remote pause, then exercises Files/Main and normal Alt-X restoration. The
independent audit must separately prove a complete source/CRC frame and received
ACK before CAN. It accounts for any exact source-derived partial next frame
before CAN, excludes EOT/full-source success, checks all bytes through DSP and
requires real subsequent menu input. Source identity and all existing server
files preserve. No product state or UART/protocol bytes are injected.

Use the cancellation counterparts of the upload commands: `audio_synchronet_cancel.py`,
`prepare_synchronet_audio_cancel.py`, `check_audio_synchronet_cancel_keys.py`,
`check_synchronet_cancel_audio_recipe.py` and `synthmodem_synchronet_cancel_audio_dos.py`.
The producer takes the same runtime/reference/key-checks/recipe-checks/preflight/
fresh-output arguments. After its natural exit run
`audit_synchronet_cancel_audio_dos.py`, `audit_serial_io_evidence.py`,
`diagnose_audio_caller.js`, `audit_synchronet_cancel_metadata.py` (BBS Nix shell)
and `check_synchronet_cancel_controls.py`. These preserve exact partial bytes and
official metadata. The recorder must distinguish client cancellation/menu/
teardown from retained/indexed server partials; partial cleanup cannot pass
merely because client recovery does. Fresh output names never authorize
overwriting an existing reference or server payload.

The [completed cancellation01](../../docs/validation/synthmodem-synchronet-cancel-audio-01.json)
is **not accepted for responsive cancellation or server cleanup**. Its87
producer/independent/ownership/partial-accounting/negative-control checks verify
exact1238 upstream bytes,37896 display/control bytes, real ACK before CAN, no
EOF/full-source publication, eventual Files/Main and normal DOS/UART/PIC/IRQ/
timer/SIP restoration. The hold is6001ms; all38105 frontend bytes complete with
zero skipped/failed/pending bytes and no gateway errors. Source identity,
existing files and server code/config/library/message bytes preserve.

The failure is concrete: Escape follows the first ACK by27ms, but78bytes of the
next frame have already been transmitted before CAN/CAN. The source/CRC-checked
first1024bytes remain officially stored/indexed; the stock receiver reports E
and10errors, and takes66.192seconds after CAN to return its pause. Five negative
counterexamples reject false ACK/CAN/menu timing, corrupt source and EOF posing
as cancellation. Eventual interaction does not establish responsive recovery.
The passive boundary diagnosis and exact original captures are sealed in the
receipt; no files or metadata are deleted and no failing outcome is waived.

The [linked-native regression](../../docs/validation/terminal-upload-cancel-boundary-01.json)
fails16cases at second-frame header/payload/checksum/CRC edges against the exact
same binary. The peer checks actual physical TX bytes; Escape is injected only
through modeled BIOS keys, with real native/UI/file/UARTISR code. Most cases
leave an incomplete packet before CAN; trailer edges can produce bad CRC/data.
Run `./tools/dev --command python3 standalone/check_terminal_upload_cancel_boundary.py`.

The required repair was to defer local ordinary-XMODEM Escape through
its checksum/CRC trailer, then emit CAN at the control boundary. Maintain bounded
service and immediate physical/carrier/deadline fault handling. Verify header,
payload, trailer, checksum/CRC, CTS stalls, loss, source ownership, next-session
state and a fresh actual audio run before granting cancellation acceptance.

### Verified packet-boundary repair

The maintained sender now tracks the native first-header-byte and final
checksum/CRC callbacks. Escape becomes pending while that frame is transmitted;
the owner then cancels at a control boundary. Admission and every exit reset
the pending state. Alt-X, carrier loss, real ISR overflow, CTS/THRE stalls and
the independent progress deadline still abort immediately and boundedly.
The recovered flat native instructions remain unchanged. The Nix source build
preserves DS=SS/64832bytes; the new terminal SHA256 is
54d53c72acc15a406a203fcf3a41e983916b308a0671093c693daf34b7e67e2e.

The [linked regression](../../docs/validation/terminal-upload-cancel-boundary-fixed.json)
passes37cases:16 checksum/CRC edges,18 pending-Escape fault cases across clock
wrap/midnight and three next uploads retaining a late ACK without resetting the
application. Existing54upload/44receive/23YMODEM/78ZMODEM and five ZMODEM cancel
cases pass. The boundary regression is included in `test-terminal`.

The [fresh audio test](../../docs/validation/synthmodem-synchronet-cancel-fixed-audio-01.json)
verifies two complete CRC-valid frames before CAN, with zero incomplete next
frame bytes. The peer pause arrives11.525seconds after CAN, versus66.192seconds
in the preserved baseline. This is within the15-second scope budget (one full
1029-byte8N1 frame at1200bps plus6seconds for response). All89 byte/control/
ownership/partial-accounting checks pass:2189 upstream bytes,34160 display/control
bytes,34369 completed frontend bytes with no skipped/failed/pending bytes,
6001ms hold, no gateway errors, real Files/Main and normal native hardware/timer/
SIP cleanup. The old midframe cancellation pattern now rejects.

Responsive **client** cancellation is accepted for this captured workflow.
Stock retains/indexes the expected2048-byte prefix and reports E/3startup errors;
there is no full-file success claim or server cleanup acceptance. The overall
receipt remains `passed:false` for that separate retained-partial gate. Both the
original1024-byte/66-second failure and all previous captures are preserved.
The fresh-case helpers use SXCAN002.BIN and the `cancel_fixed` counterparts of
the baseline tools; `record_synchronet_cancel_fixed_audio.py` validates the paired
baseline and measured response budget. Same-call retry, actual carrier loss/
reconnect, sustained pressure, other profiles and physical hardware remain open.
Earlier audio receipts retain their original frozen executable identities; this
new binary's audio proof covers the cancellation workflow described here.

The [current-build preparation](../../docs/validation/current-synchronet-cancel-preparation.json)
preserves that history and selects unused remote slot3, `SXCAN003.BIN`.
`--slot` accepts registered eight-character names and binds the chosen name into
the preflight, recipe, deterministic payload and audits. The unchanged helper
still types local `D:\SEND\SXCAN002.BIN`; XMODEM carries no filename, so only the
BBS-side name changes. Default slot2 behavior remains exact. Existing reference
and BIOS-key proofs remain valid by their unchanged input identities. The fresh
selected recipe checks15 raw prompts and the preflight confirms disk/API absence.
The [current976 run](../../docs/validation/current-synchronet-cancel-audio-01.json)
uses the validated200ms runtime and now passes89 checks. Its2189 online bytes
and35634 BBS display bytes remain exact; two complete CRC frames precede CAN
with zero split-frame bytes. The remote pause arrives11.685seconds after CAN,
within the15-second response budget; actual Files/Main and normal DOS/UART/IRQ/
PIC/timer/SIP cleanup pass. All35843 frontend bytes complete without failed,
skipped or pending writes. Seven controls include the old midframe pattern and
timing/corruption/false-EOT mutants, all correctly rejected. The official API and
helper E record account for the exact2048-byte retained/indexed partial.
Responsive client cancellation is accepted; server cleanup and overall receipt
stay false. No earlier file is removed or overwritten. Same-call retry and
physical hardware require separate current-build tests.

```sh
./tools/bbs-dev --command python3 lab/bbs/prepare_synchronet_audio_cancel_fixed.py \
  --slot 3 --output build/bbs-lab/current-synchronet-cancel-preflight-01
./tools/modem-dev --command python3 lab/bbs/check_synchronet_cancel_fixed_audio_recipe.py \
  --slot 3 --reference build/bbs-lab/synchronet-audio-cancel-reference-01 \
  --output build/bbs-lab/current-synchronet-cancel-recipe-01
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_cancel_fixed_audio_dos.py \
  --slot 3 --runtime build/bbs-lab/synthmodem-buffered-runtime-01/runtime \
  --buffered-runtime-proof build/bbs-lab/synthmodem-buffered-runtime-01/result.json \
  --reference build/bbs-lab/synchronet-audio-cancel-reference-01/result.json \
  --key-checks build/bbs-lab/audio-synchronet-cancel-fixed-keys-01/result.json \
  --recipe-checks build/bbs-lab/current-synchronet-cancel-recipe-01/result.json \
  --preflight build/bbs-lab/current-synchronet-cancel-preflight-01/result.json \
  --output build/bbs-lab/current-synchronet-cancel-audio-01
```

These commands document the current cohort, whose outputs must not be rerun or
overwritten. Later tests require fresh output paths and an unused remote slot.
After natural exit, use the `cancel_fixed` byte/metadata/control auditors, serial
audit, independent caller decoder and boundary diagnosis before recording client
acceptance. Any retained or indexed partial keeps server cleanup unaccepted.

## Current-build same-call early-start retry

The [preparation record](../../docs/validation/current-synchronet-retry-preparation.json)
binds unused actual slot4 (`SXRCN004.BIN` then `SXRUP004.BIN`) and a fresh stock
TCP reference (`SXQRF007.BIN` then `SXQRF008.BIN`). Reference cancellation/full
retry, exact storage/padding and original partial preservation pass11 checks.
Both actual destinations are absent from disk and the official FileBase API.
The selected script compiles and15 raw wait tokens match captured prompts.

The BIOS helper now accepts `AUDIO_SYNC_RETRY_SLOT`1..9 for its remote retry
name and numeric key. Default slot3 assembles byte-identically to the prior
helper; slot4 changes exactly three filename/key bytes. Six actual8086 BIOS
checks cover the selected name/confirmation, partial-menu guards, no second
Escape, watchdog and timer restoration. The local source path remains
`D:\SEND\RETRY.BIN`. Early-start timing is preserved: second Alt-S follows N by
three BIOS ticks, without waiting for the complete receiver-ready banner.
The selected control selfcheck passes a synthetic baseline and rejects twelve
timing/source/finish/menu counterexamples; these are not actual audio results.

The actual producer accepts an explicit `--startup-component-proof` and binds
its binary, nested source and captured DOS evidence. The current proof is
[current-terminal-upload-startup-01.json](../../docs/validation/current-terminal-upload-startup-01.json);
the older3b proof remains the default for historical recipes. The normal200ms
runtime requires its explicit stage proof. The current cohort was launched as:

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_retry_startup_audio_dos.py \
  --slot 4 --runtime build/bbs-lab/synthmodem-buffered-runtime-01/runtime \
  --buffered-runtime-proof build/bbs-lab/synthmodem-buffered-runtime-01/result.json \
  --startup-component-proof docs/validation/current-terminal-upload-startup-01.json \
  --reference build/bbs-lab/current-synchronet-retry-reference-01/result.json \
  --key-checks build/bbs-lab/current-synchronet-retry-keys-01/result.json \
  --recipe-checks build/bbs-lab/current-synchronet-retry-recipe-01/result.json \
  --preflight build/bbs-lab/current-synchronet-retry-preflight-01/result.json \
  --output build/bbs-lab/current-synchronet-retry-audio-01
./tools/bbs-dev --command python3 lab/bbs/observe_synchronet_retry_startup_partial.py \
  build/bbs-lab/current-synchronet-retry-audio-01 --slot 4
```

Start the read-only observer after the producer creates its output directory
and before retry completion. It requires the retry to remain unindexed while
capturing the first partial's exact bytes, inode, size, timestamp and official
metadata. The final audit requires those to survive the full retry unchanged.
After natural exit, run the `retry_startup` full byte, official metadata and
control auditors, independent caller decode and serial-write audit before the
recorder. Full CRC/ACK/two-EOT finish, exact online/display streams, Files/Main
and DOS/UART/IRQ/PIC/timer/SIP cleanup remain mandatory. Both actual run and
observer are currently in progress; preparation grants no actual same-call
audio acceptance. Retained/indexed stock partials keep overall/server cleanup
false even if the client workflow succeeds. These occupied output paths are
documentation, not commands to overwrite or restart the current cohort.


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

## Stock XMODEM-CRC download

The download route uses the existing owned PCPlus Lab area and unchanged stock
Synchronet/sexyz. It selects directory11, PCXTEST.BIN and protocol1, declines
hangup with a single N, then releases ASPECT ownership. A BIOS-only helper opens
the native Alt-R prompt and supplies D:\RECV\SYNC.BIN. It waits for actual
Receiving XMODEM, completion and the remote pause before Space, requires the
File menu and PCPlus Lab footer before Q, and waits for complete Main/footer
before Alt-X. The watchdog cannot grant workflow acceptance.

The source is11521 synthetic bytes including NUL/SUB/IAC/XON/XOFF. Stock XMODEM
has no original-length field: the verified reference delivers11648bytes in
eleven1024-byte and three128-byte blocks, including127SUB padding. The DOS file
must preserve that padding; it must not claim exact unpadded length from this
protocol. All frame CRCs, sequence/complements, opposite ACKs and final EOT/ACK,
the exact receive file, complete audio streams, post-transfer interaction and
cleanup are independently audited. A separate read-only official FileBase audit
checks hashes, the server success log and one download-count advancement from
the displayed pre-transfer count. No messages, mail or uploads are requested.

```sh
./tools/bbs-dev --command python3 lab/bbs/audio_synchronet_download.py \
  --output build/bbs-lab/synchronet-audio-download-reference-NEW
./tools/modem-dev --command python3 lab/bbs/check_audio_synchronet_download_keys.py \
  --output build/bbs-lab/audio-synchronet-download-keys-NEW
./tools/modem-dev --command python3 lab/bbs/check_synchronet_download_audio_recipe.py \
  --reference build/bbs-lab/synchronet-audio-download-reference-NEW \
  --output build/bbs-lab/synchronet-download-audio-recipe-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_download_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-posttrain-runtime-01/runtime \
  --reference build/bbs-lab/synchronet-audio-download-reference-NEW/result.json \
  --key-checks build/bbs-lab/audio-synchronet-download-keys-NEW/result.json \
  --recipe-checks build/bbs-lab/synchronet-download-audio-recipe-NEW/result.json \
  --output build/bbs-lab/synthmodem-synchronet-download-audio-NEW
# After natural producer exit:
./tools/modem-dev --command python3 lab/bbs/audit_synchronet_download_audio_dos.py COHORT
# Preserve the original audit; its single-EOT input assumption fails this native receiver.
./tools/modem-dev --command python3 lab/bbs/audit_synchronet_download_audio_dos_v2.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py COHORT
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js RUNTIME COHORT
./tools/bbs-dev --command python3 lab/bbs/audit_synchronet_download_metadata.py COHORT
./tools/modem-dev --command python3 lab/bbs/check_synchronet_download_control_timing.py COHORT
# Only after all gates pass:
./tools/modem-dev --command python3 lab/bbs/record_synchronet_download_audio.py COHORT \
  --output docs/validation/synthmodem-synchronet-download-audio-NEW.json
```

The raw recipe check caught ANSI highlights splitting both Which/Quit and
Protocol/Batch. Stable raw prefixes correct these before the first audio run;
the original failed token-check artifacts remain retained. Every remote wait
must pass its independent raw-capture check. Preparatory results grant no actual
audio/DOS download, upload, other-protocol or physical acceptance.

The [completed download audio01](../../docs/validation/synthmodem-synchronet-download-audio-01.json)
passes81 checks:25 producer,34 independent,12 ownership, six official metadata
and four control-timing checks. All121 upstream bytes and49730 display/binary
bytes survive exactly. All49939 frontend bytes complete with zero skipped,
failed or pending bytes. The observed minimum hold is6100ms. Fourteen unreplayed
CRC-valid blocks preserve the exact source plus127SUB padding; native final
ACK follows publication. The actual Files/Main return and normal DOS/UART/PIC/
IRQ/timer/SIP restoration pass. No gateway errors, message/mail/upload writes
or code/config/library/source/message-body changes occur. Official FileBase
hashes match and its download count advances once,19 to20; the stock server log
reports the successful11521-byte download. The area has DIR_NOSTAT, so global
transfer counters do not provide this per-file evidence.

The original independent audit's only failure is its incorrect literal input
assumption of15ACKs. Existing native receiver regressions exercise EOT NAK/ACK;
this capture contains14 block ACKs, NAK to the first EOT and ACK to the second.
The separate v2 audit requires that exact sequence and preserves every original
CRC, control-timing, full-stream, file and cleanup gate. Original report and
frozen auditor at e498ec5 remain unchanged and are hashed in the receipt. Three
timing-only mutants (early block ACK, early final ACK and final ACK after menu
input) reject; this correction does not waive the mandatory final ACK.

Acceptance is limited to this stock XMODEM-CRC download over the explicit
monotonic-hold/key-framing audio runtime, with unchanged DOS binaries. Uploads,
other Synchronet audio protocols, sustained pressure/carrier-loss/reconnect,
physical Boca/SPA2102 and F01-F16 application gates remain open.

## Stock XMODEM-CRC upload

The upload recipe uses the same owned stock area/server/helper. It supplies a
fresh filename, confirms that destination, supplies a synthetic description,
selects protocol1 and declines hangup with N alone. The BIOS helper drives the
actual Alt-S filename UI with D:\SEND\SXAUDIO1.BIN, observes sending/completion,
dismisses the remote pause, returns through Files/Main and restores INT1C.
No product state, UART data, protocol responses or success files are injected.
Fresh target absence is checked through both disk and the official FileBase API
before launch. The deterministic11521-byte payload is unique per target name;
the original DOS inode/size/mtime and all existing server files must preserve.
XMODEM's127SUB padding remains part of the official11648-byte stored file.

The [current-build preparation](../../docs/validation/current-synchronet-upload-preparation.json)
uses a fresh `SXAUDIO2.BIN` destination and `SXAUREF3.BIN` TCP reference, retaining
the earlier stored fixtures. `--slot` selects registered eight-character test
basenames; target absence on disk and in FileBase remains mandatory. The local
BIOS-helper path stays `D:\SEND\SXAUDIO1.BIN`, containing the selected target's
deterministic payload. XMODEM transmits data without a filename, so its BBS-side
name can differ from the local source alias. Default slot1 payloads and the
ASPECT recipe remain exact, and the existing BIOS-key proof is still valid.

The normal200ms runtime is selected through `--buffered-runtime-proof`. The
[current source-built976 DOS upload](../../docs/validation/current-synchronet-upload-audio-01.json)
passes all92 producer/audit checks:11849 exact online bytes,38172 exact BBS
display bytes,14 unreplayed CRC blocks, exact11521-byte source plus127SUB padding,
two-EOT NAK/ACK, official storage/metadata and post-transfer Files/Main. Normal
DOS/UART/IRQ/PIC/timer/SIP cleanup, all earlier files and frozen source/runtime
identities preserve. All38381 frontend bytes complete without skipped/failed/
pending writes. Four CRC requests account for three stock initial no-input
timeouts, with no data-block errors. Both timing oracles reject early/late ACKs.
The original zero-total-errors failure is retained alongside the source-backed
interpretation. Seven [attribution mutants](../../docs/validation/current-synchronet-upload-attribution-negative.json)
refresh relevant hashes in separate ignored copies and reject at the intended
policy gates: higher/lower DSZ count, failed receive status, missing CRC request,
data NAK, replayed frame and another failed metadata gate. Original captures
remain exact. This grants one current DOS/audio upload acceptance; cancellation,
retry, sustained pressure and physical hardware still require their own tests.

The [first reference](../../docs/validation/synchronet-audio-upload-reference-01.json)
misread a C within the CRC banner as the standalone CRC startup signal. It
transmitted one valid block, then misread remaining text as ACK and closed.
The1024-byte partial and all original captures remain intact; source checkpoint
3c7c26a preserves this failed parser. The corrected reference consumes the exact
stock startup banner first, then waits for C. A fresh reference filename avoids
overwriting the partial and prevents duplicate-content rejection. It passes all
14CRC-valid blocks, two-EOT NAK/ACK, exact storage/metadata and Files/Main return.

The [partial-publication diagnostic](../../docs/validation/synchronet-upload-partial-publication.json)
confirms that this failed reference's1024-byte partial is officially indexed,
and has an upload-success entry despite the helper's E/one-error record. Thus
storage, metadata and U+ alone cannot establish full transfer success. Actual
acceptance additionally requires complete wire frames/CRC/sequence, all opposite
ACKs and final EOT finish, exact full known source/padding, and a successful
helper receive with any reported errors explained by complete wire evidence.
Cancellation/loss cleanup remains open;
the diagnostic does not remove or replace the partial or its metadata.

```sh
./tools/bbs-dev --command python3 lab/bbs/audio_synchronet_upload.py \
  --slot 3 \
  --output build/bbs-lab/synchronet-audio-upload-reference-NEW
./tools/bbs-dev --command python3 lab/bbs/prepare_synchronet_audio_upload.py \
  --slot 2 \
  --output build/bbs-lab/synchronet-audio-upload-preflight-NEW
./tools/modem-dev --command python3 lab/bbs/check_audio_synchronet_upload_keys.py \
  --output build/bbs-lab/audio-synchronet-upload-keys-NEW
./tools/modem-dev --command python3 lab/bbs/check_synchronet_upload_audio_recipe.py \
  --slot 2 \
  --reference build/bbs-lab/synchronet-audio-upload-reference-NEW \
  --output build/bbs-lab/synchronet-upload-audio-recipe-NEW
./tools/modem-dev --command python3 lab/bbs/synthmodem_synchronet_upload_audio_dos.py \
  --runtime build/bbs-lab/synthmodem-buffered-runtime-01/runtime \
  --buffered-runtime-proof build/bbs-lab/synthmodem-buffered-runtime-01/result.json \
  --slot 2 \
  --reference build/bbs-lab/synchronet-audio-upload-reference-NEW/result.json \
  --key-checks build/bbs-lab/audio-synchronet-upload-keys-NEW/result.json \
  --recipe-checks build/bbs-lab/synchronet-upload-audio-recipe-NEW/result.json \
  --preflight build/bbs-lab/synchronet-audio-upload-preflight-NEW/result.json \
  --output build/bbs-lab/synthmodem-synchronet-upload-audio-NEW
# After natural producer exit:
./tools/modem-dev --command python3 lab/bbs/audit_synchronet_upload_audio_dos.py COHORT
./tools/modem-dev --command python3 lab/bbs/audit_serial_io_evidence.py COHORT
./tools/modem-dev --command node lab/bbs/diagnose_audio_caller.js RUNTIME COHORT
./tools/bbs-dev --command python3 lab/bbs/audit_synchronet_upload_metadata.py COHORT
# If only the zero-total-errors gate fails, retain it and diagnose startup-only retries.
./tools/bbs-dev --command python3 lab/bbs/audit_synchronet_upload_metadata_v2.py COHORT
./tools/modem-dev --command python3 lab/bbs/check_synchronet_upload_control_timing.py COHORT
./tools/modem-dev --command python3 lab/bbs/check_synchronet_upload_control_timing_indexed.py COHORT
# Only after every gate passes:
./tools/modem-dev --command python3 lab/bbs/record_synchronet_upload_audio.py COHORT \
  --output docs/validation/synthmodem-synchronet-upload-audio-NEW.json
```

Choose unused reference/actual slots; the example pairing records the current
preparation. Existing uploads are retained. A new output label does not
authorize replacement of server files. The selected destination is bound into
the payload, preflight, script and exact-input/storage oracle while local helper
keys remain unchanged. Preparations alone grant no actual
audio/DOS upload, cancellation/loss or physical acceptance. The source-backed
startup audit now requires the reported DSZ error count to equal captured CRC
startup requests minus one, with fourteen valid unreplayed blocks and no data
NAK. It preserves the failed zero-total-errors record and accepts no other
failed metadata gate; it does not assume a fixed count for future calls.

The [completed audio upload01](../../docs/validation/synthmodem-synchronet-upload-audio-01.json)
passes87 checks:25 producer,35 independent,12 ownership,11 source-backed metadata
and four ACK-timing checks. All11849 upstream bytes and46799 display/control
bytes survive exactly; all47008 frontend bytes complete without skipped, failed
or pending bytes. The minimum hold is6001ms, with no gateway errors. Fourteen
unreplayed CRC-valid native blocks preserve11521 source bytes plus127SUB padding
in official storage and metadata. Both EOTs, NAK/ACK, actual Files/Main return,
normal DOS/UART/PIC/IRQ/timer/SIP restoration, source identity, existing files
and server code/config/library/message bodies preserve. No message/mail/download
writes occur. DOS application binaries remain unchanged.

The original metadata audit fails only its zero-total-errors assumption. The
stock helper reports successful R/11648 and three cumulative errors. Exact
CCCC startup requests followed by14ACKs and EOT NAK/ACK account for those three
initial no-input timeouts; the pinned official sexyz.c/xmodem.c sources match
their archive exactly and establish the3-second first-block wait and cumulative
counter. Complete native prefix/frame/suffix and opposite-control validation
exclude malformed/replayed data or failed finish. The separate v2 metadata audit
requires this exact attribution: four startup requests, three startup timeouts,
zero data-block errors. Original zero-total-errors report stays retained and
hashed. This accepts delayed-start stock upload compatibility; it does not claim
zero startup retries or waive a failed receive/helper E record.

All three ACK timing mutants reject in both the original linear oracle and the
[indexed lookup validation](../../docs/validation/synchronet-upload-control-index.json).
The latter uses exact contiguous offset manifests with the same control-policy
function and reproduces its original baseline, avoiding quadratic pre-protocol
display scans. The original checker was allowed to finish and its artifacts
remain preserved. Index validation is a component check, not separate audio
acceptance.

The failed reference/partial publication remain separate known evidence.
Other protocols, cancellation/loss cleanup, sustained pressure/reconnect,
physical Boca/SPA2102 and F01-F16 whole-application requirements remain open.
