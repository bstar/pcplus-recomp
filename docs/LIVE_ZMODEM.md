# ZMODEM in the terminal

This document records the initial `8c481cfd` integration checkpoint.
The subsequent `d0274a22` runtime adds [8 KiB reception and logged-in BBS tests](ZEDZAP_BBS.md);
the footprint and validation numbers below remain historical.
Current [windowed sending](WINDOWED_ZMODEM.md) also corrects confirmed-replay
progress and retains both earlier runtime counterexamples.

Alt-R receives and Alt-S sends. In the transfer prompt, press F2 to cycle
XMODEM, YMODEM and ZMODEM. ZMODEM receive takes an existing directory such as
`D:\RECV\`; send takes an explicit DOS filespec such as `D:\SEND\*.BIN`.
The prompt retains typed text while changing protocols. As with the other binary
owners, use HARD or NONE flow and an ff receive mask; SOFT/masked sessions are
rejected before starting a transfer. This selection is session state, not a new
saved PRM protocol field.

The terminal now connects the [maintained session engine](ZMODEM_SESSION.md)
and [wire codec](ZMODEM_WIRE.md) to its serviced UART, checked batch file owners,
transfer prompt, progress, cancellation and completion notices. Engine, codec
and adapter execute in CONFIG_CODE. This does not close F08 or any other
whole-application gate.

## Storage, memory and callbacks

`upload_source_seek` and `batch_upload_seek` support checked absolute reposition
within the frozen source size, including EOF. Invalid ranges leave the snapshot
unchanged; DOS errors and an unexpected returned position poison the source.
Only exact success changes consumed position. A skipped source can close while
preserving enumeration continuation. Existing read/close/uncertain ownership
semantics and the 92-byte source / 90-byte batch snapshot ABIs are preserved.

`batch_download_exact` accepts zero through 1024 unpadded bytes only for an
unknown-length owner. The ZMODEM adapter deliberately removes the advisory
metadata length before opening that owner. Verified ZEOF position determines
file length; no DOS EOF-character trimming is used. Existing YMODEM block
append and declared-length behavior remain unchanged. Checked close/install
precedes the final ZRINIT. Existing targets are skipped and foreign stages are
preserved. Write, short-write, close and installation errors cannot become
successful file completion.

The complete live entry refuses prior open, sealed or uncertain owners before
touching the shared arena, filesystem or UART. Failure and cleanup remain
separate. A failed source close is not repeated, and ambiguous ownership stays
visible for recovery. Earlier installed files remain after later batch errors.

The 4200-byte session and eight bytes of live progress state reuse the existing
exclusive transfer arena. No second payload buffer is allocated near. The ten
far callback pointers are checked against their named CONFIG_CODE targets and
their individual MZ segment relocations. Five new declared bridge pairs bring
the configuration ABI to 66 and the total verified bridge pairs to 115.

UART waits/writes use the existing serviced owner; ISR receive, keyboard escape,
carrier/CTS/stall checks and accepted-progress watchdog remain active. Progress
refreshes when a file's verified high-water position or completed-file count
advances. Source CRC rereads and retransmitting an old position do not create
accepted progress. The display shows the current file's KiB, bounded to a word;
larger files keep full DWORD offsets internally.

Connected modem sessions use a bounded allowance for an unknown carrier speed,
independent of fixed DTE. Direct/raw UART-derived deadlines remain unchanged;
see the [deadline correction and paired proofs](../lab/bbs/carrier-transfer-deadline.md).

The current runtime has 65,056 near data/stack bytes (480 free), 62,946 resident
code bytes and 37,578 CONFIG_CODE bytes. It retains 20,313 paragraphs including
the PSP for PROGRAM children. Compared with the preceding 61db runtime, this
costs 336 near bytes and 724 resident code bytes. These are measured cumulative
integration costs, not estimates of protocol throughput.

## Evidence

`./tools/build test-terminal` includes the linked ZMODEM checks. The dedicated
`./tools/build test-zmodem-owners-live` checks prior-owner exclusion. Source and
batch ownership diagnostics also run through `test-upload-file`,
`test-batch-upload` and `test-batch-download`.

The linked suite executes the actual far entry, callback table, codec, checked
source/destination owners, real UART ISR and foreground dispatcher. Independent
Python wire scripts cover both CRC widths, empty/odd/boundary/over-64KiB files,
source reposition including EOF, post-transfer application bytes and storage
failures. Ten further checks preserve open/sealed/uncertain cross-direction
owners and their entire arena snapshots without file or UART operations. Only
BIOS/UART/ticks and DOS kernel boundaries are modeled in those checks.

The actual DOS fixture uses BIOS Alt-R/Alt-S and two F2 presses, real DOS files,
the production UART/IRQ path and the pinned independent lrzsz peer. It verifies
exact complete destination trees, unchanged source content/metadata, no stages,
post-transfer DSR/keyboard/screen operation, normal exit and UART/PIC/vector
restoration. All media is synthetic under ignored build directories; no mounted
CF card is used. Larger upload fixtures need a longer scheduled-key window than
the initial 45-second attempt; failed attempts remain explicit in the report.
This emulated CPU/serial configuration does not measure physical modem speed.

The hash-bound [live report](validation/live-zmodem.json) identifies successful
and failed fixture attempts, call-frame mutation checks, exact runtime sources,
the terminal regression and the independent 64-output source rebuild. Earlier
component/BBS reports retain their stated historical runtime identities; they
are not silently attributed to this new binary.

## Remaining scope

Actual Synchronet and ENiGMA logged-in ZMODEM workflows, corrupted-wire actual
DOS recovery, timing/cancel/line-loss coverage on the new live adapter, persisted
partial resume, original-style windowed sending, auto-download and physical
RS-232 Wi-Fi modem validation remain open. The generic completion footer still
shares existing batch wording; fuller direction-specific final-handshake
presentation remains part of the unfinished UI. Safe DOS8.3 names are required;
broader remote pathname/name mapping and all remaining protocol families remain
required. Source-owned DOS ZMODEM is a milestone, not a complete PCPlus rebuild.
