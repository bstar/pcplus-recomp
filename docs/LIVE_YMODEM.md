# Live CRC YMODEM

The source-built terminal provides maintained YMODEM batch receive/send through
the actual serviced UART. Alt-R/Alt-S opens the transfer prompt; F2 switches
ordinary XMODEM and YMODEM before Enter starts the session. Ordinary XMODEM is
the initial default. A selected protocol persists for subsequent prompts.

For receive, enter an existing directory (`D:\RECV\`); for send, enter a local
DOS8.3 filespec (`D:\SEND\*.BIN`). Both peers must select YMODEM. HARD and NONE
are supported; SOFT rejects before acquiring files. Escape cancels; Alt-X
cancels and exits. Empty source patterns send a successful empty batch.

`src/transfer/ymodem.c` is a maintained batch session, distinct from the
recovered ordinary native sender/receiver and the exact native metadata
diagnostic. It links the recovered CRC routine and bounded metadata codec. It
uses the existing exclusive native arena for working/header/last-frame buffers,
preserving the far shadow/history and DS=SS near ABI. No originals are build
inputs.

Block0 accepts CRC128/1024 metadata, safe DOS8.3 basenames and the documented
optional fields. Paths, devices, malformed strings and numeric overflow reject.
Known length0 creates an empty file. Known-length data stores exactly the
declared bytes, discarding only final-frame padding; unknown lengths retain
complete blocks. Premature EOT or a distinct frame beyond the declared length
fails. Timestamps/modes/extensions are parsed but not applied to DOS files.

Each incoming file uses exclusive same-parent `PCRX.$$$` staging and checked
writes, close and no-overwrite installation before the final EOT ACK. Exact
duplicate header/data frames are acknowledged without reopening or appending.
Sequence rollover is modulo256. A two-EOT closure precedes the next header;
an empty block0 terminates the batch. Earlier installed files are retained on
later failure. Cancellation removes only the current owned stage. Uncertain
close or unresolved storage remains visible for recovery; a refused new owner
must not clean up a previous owner's file.

Upload enumeration saves/restores the caller's DOS DTA around each find call,
skips hidden/system/volume/directory entries, and has no fixed file-count cap.
Each source uses one read-only handle and a DWORD size snapshot. A cached frame
is retransmitted without rereading. Actual ACKs advance maintained progress.
The consumed source is closed before the first EOT; close failure cannot commit
the remote file. Source growth after the snapshot is not included; shrink/read
failure aborts. The inherited safe size ceiling is `0x7ffffbff` bytes per file.

Retries are finite, and the live accepted-progress watchdog also bounds noise
and duplicate storms:30seconds,120seconds below1200baud. Accepted headers/data
and checked closure refresh it; duplicate ACKs do not. Every byte services
keyboard, carrier, overflow and hardware flow. Physical TX stall is bounded
separately. A final-header ACK grace period handles retransmitted end headers;
speculative application prefixes are restored to the actual ring atomically,
with capacity and count checks, so the next terminal escape sequence survives.

Uploads distinguish a missing final batch ACK from confirmed success. After
all files have their EOT ACKs, a peer returning application text instead of the
final empty-header ACK ends protocol ownership with status10
`YM_END_UNCONFIRMED`. The first application byte is restored, no more binary
headers/CAN are sent into its menu, and the notice says `TX batch sent; ACK?`.
Missing data/EOT ACKs never use this exception. Timeout/NAK still retries and
fails finitely. The stock Synchronet helper's observed producer-buffer defect
motivated this policy; [peer findings](../lab/bbs/YMODEM_PEER_FINDINGS.md) retain
the strict failed handshake and REA evidence. It is not a fabricated ACK.

Rebuild with `./tools/build terminal`. Checked file-owner tests are
`./tools/build test-batch-download test-batch-upload`; the independent DOS peer
is `standalone/test_terminal_ymodem_dos.py` and requires an explicit runtime
SHA256 and fresh label. Local BBS workflows use `lab/bbs/test_ymodem_dos.py`.
Their raw fixtures, captures and databases remain under ignored build storage.

The capture/serial-poll checkpoint `6b69f9b0` repeats all30 independent DOS
YMODEM cases and the linked owner/UART failure suite successfully. BBS transfer
workflows retain their tested `2dafc08b` identity; the new build's separate editor
runs do not count as current-runtime BBS transfer validation. Both checkpoints
and earlier failed runs remain in the public validation records.

This implements CRC YMODEM, not YMODEM-G, ZMODEM, SEALINK, crash atomicity or the
complete PCPlus transfer/settings interface. DOSBox null-modem tests do not
prove physical Wi-Fi modem wiring, buffering, CTS/DCD behavior or hardware
timing. See the recorded validation for precisely which sessions passed.
