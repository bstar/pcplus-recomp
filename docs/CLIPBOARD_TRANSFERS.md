# Clipboard filenames across file transfers

The maintained terminal passes six actual DOS workflows that select remote
filenames with Alt-=, transfer the selected files and reuse the clipboard after
returning to the terminal. The checkpoint is bound to the frozen executable in
[`validation/clipboard-transfers.json`](validation/clipboard-transfers.json).
It supplements the core, live transport and saved-settings evidence in
[`FILENAME_CLIPBOARD.md`](FILENAME_CLIPBOARD.md) and
[`CLIPBOARD_SETTINGS.md`](CLIPBOARD_SETTINGS.md).

| Workflow | Selection and file checks |
| --- | --- |
| XMODEM receive, Single | Select ONE.BIN; receive 12,288 exact binary bytes; Single then offers retained TWO.BIN. |
| XMODEM send, Single | Select ONE.BIN; send its actual DOS source with CRC framing; source content and metadata remain unchanged; TWO.BIN remains available. |
| YMODEM receive, Tagged | Select two of three names with a space separator; receive an empty file and an 8,197-byte binary file, without receiving the untagged file; tags remain available. |
| YMODEM send, All | Send the CR-separated selection, an empty file and an 8,197-byte file; verify exact batch framing/lengths and unchanged sources; list remains available. |
| Stale remote name | Peer rejects OLD.ZIP before any handshake; select TWO.BIN and complete a real receive; empty-list paste produces no serial bytes. |
| Cancel local filename prompt | Select ONE.BIN, cancel the local receive prompt, resume an actual queued status query without starting a protocol, select TWO.BIN and complete the receive. |

The peer consumes exact clipboard packets at each remote filename prompt and
uses those names to choose the protocol payload. Protocol controls are strict:
unexpected bytes fail the test. Existing independent XMODEM/YMODEM framing peers
check CRC, block sequence, file bytes and completion; the batch peer also checks
headers, lengths and the final empty header. A post-transfer status query and
typed `ready` verify resumed parser and keyboard service.

An external INT16 observer chains the actual BIOS, preserving its flags and
register results, and records selected keys alongside the visible header and
footer. It verifies that Alt-=, Ctrl-PgUp and paste letters were actually read
while the transfer screen owned the keyboard. The clipboard must not open, and
the wire/file checks must still pass. Alt-R while the clipboard is open must
leave the clipboard in control; clipboard hotkeys at the local filename prompt
must not replace that prompt. A separate INT1C video observer samples clipboard
list/notices. Neither observer reads application memory, injects replies or
calls product functions. The key observer restores and independently reads back
the original BIOS vector when collected.

All six cases verify normal DOS exit, the complete 42-byte hardware restoration
sample, no leftover transfer staging files, and the restored live screen. Each
run uses a fresh owned directory and an explicit executable SHA256. Synthetic
binary payloads include control bytes; upload sources are checked by inode,
size, modification time and SHA256.

Run through the pinned Nix environment after building the desired terminal:

```sh
./tools/build test-clipboard-transfers
```

To retain a chosen label and record the evidence:

```sh
./tools/dev --command python3 standalone/test_clipboard_transfer_dos.py \
  --label YOUR_FRESH_LABEL --sha256 YOUR_TERMINAL_SHA256
./tools/dev --command python3 standalone/record_clipboard_transfers.py \
  --label YOUR_FRESH_LABEL
```

The recorder checks all six results, source hashes, observed filename packet
offsets and retained artifacts. It also verifies the existing 77-command
terminal regression and 64-output source rebuild refer to this same runtime.
The new tests do not change the production executable. The first development
attempt exposed a DOS batch-fixture issue: redirection created an empty FAIL
file even when its inline IF condition was false. Explicit GOTO branches fix
that fixture; the attempt remains in ignored local evidence.

These controlled peers prove the selected DOS ownership/protocol workflows.
They do not prove stock BBS menu integration, physical Wi-Fi modem operation,
original clipboard UI parity or other video geometries. F11 and every other
whole-application gate remain open.

## Stock BBS prompt integration

The separate [`validation/bbs-clipboard-transfers.json`](validation/bbs-clipboard-transfers.json)
records actual stock-server workflows. Synchronet passes a clipboard Single
paste at its Filespec prompt followed by a CRC/1K XMODEM download and a return to
the main menu. The known 11,521-byte fixture is received as 11,648 bytes because
XMODEM has no original-length metadata; all 127 trailing bytes are SUB padding.
The independent passive auditor replays the retained wire to verify framing and
bytes. Exactly one uppercase filename packet precedes the transfer, while the
lowercase text entered into the local clipboard editor never reaches the BBS.
The actual invocation and full BIOS key recipe are retained in the report.

This Synchronet session uses a temporary daily-logon exemption for the synthetic
LABUSER account, declared separately from terminal compatibility. The original
exemption word is restored in a finally block, then a separate stock User API
process reads back the persisted value. The report retains both records. No
server protocol or terminal replies are supplied by the fixture.

ENiGMA passes clipboard Single at its file-search form, queues the matching file,
returns through the search form to the file menu and downloads it with the stock
YMODEM helper. DOS receives exactly 11,521 bytes, including all binary control
values, and acknowledges the final empty batch header. Afterward the same local
clipboard editing/paste sequence performs another remote filename search. The
actual returned filename and size are verified after removing standard CSI
formatting codes; the runtime harness also checks their ordered raw wire tokens.
The stock server log independently binds one login, search, successful helper
exit and a subsequent file list to this session. Both servers' file metadata is
checked through their official read APIs, and their source identities/helper
hashes are retained.

Four earlier unsuccessful ENiGMA fixture attempts remain explicit in the prior
runtime report: returning to the
search form instead of the file menu; incorrectly trying to clear an already
empty new-session queue; expecting the requested file first in a general listing
sorted by date; and searching raw ANSI bytes for a caption containing intervening
color codes. The last two attempts completed the real transfer, but failed their
post-menu assertions. Neither is relabeled as a passing run. The aggregate report
therefore remains false while its two latest selected workflows pass.

The command-menu runtime now enters the clipboard through Alt-Z, View and F
on both servers, including ENiGMA's second search after the download. The report
verifies the menu's right-arrow keys do not reach the remote prompt. The first
Synchronet attempt failed this acquisition prerequisite: arrows and lowercase
local-edit text reached Filespec. A linked replay leaves stable opening guards
clear; the exact transient refusal was not established. Increasing the settling
interval before Alt-Z from1500ms to3000ms passes. Both attempts remain explicit.

The BBS evidence recorder takes explicit current attempts and preserves earlier
runtime reports separately:

```sh
./tools/dev --command python3 lab/bbs/record_clipboard_transfers.py \
  --run synchronet:menu-clipboard-download-c0d6-1 \
  --run synchronet:menu-clipboard-download-c0d6-2 \
  --run enigma:menu-clipboard-search-download-c0d6-1
```

These are selected Single/download integrations on owned loopback servers.
Stock-server uploads, multi-name prompt conventions, full original UI parity,
other geometries and physical modem behavior remain outside this checkpoint.
