# Gateway sink, transfer and reconnect composition

The normal Gateway-enabled executable from commit `89221e9` now passes selected
capture/HOLD/PRN preservation, carrier-loss/redial, and stock Enigma binary
cancel/retry workflows. Its bytes are unchanged:
`ae6cbad95094fd59f98fd95a7831cbdc014b404ec37886a290294fe05089d90b`.
The receipt is [gateway-composition.json](validation/gateway-composition.json).

## Capture and printer across actual Gateway

Five actual DOSBox-X workflows run an 8086 with FPU disabled, both software and
hardware flow enabled, and a source-built COMSPEC child. Real BIOS keys open
capture/PRN, select HOLD where applicable, enter Alt-F4, resume capture, close
owners and exit. The peer supplies FIRST, optional PAUSED text, a 3,200-character
burst plus CRLF during the child, and LAST after normal keyboard service returns.

| Case | Capture bytes | File-only PRN bytes |
| --- | ---: | ---: |
| Capture | 3,215 | 0 |
| Capture on HOLD | 13 | 0 |
| Capture and PRN | 3,215 | 3,215 |
| HOLD and PRN | 13 | 3,223 |
| PRN only | 0 | 3,215 |

Every byte matches the independently specified expected output. HOLD continues
suppressing capture through the child until explicitly resumed; printing remains
independent. The child attempts write/close on descriptors 5–19: every operation
returns DOS error 6 (invalid handle). It can still create its own file. The original
parent descriptors resume afterward; no child X byte appears in either sink.

A passive DOS entry observer records AX/BX/CX/DS without calling DOS inside its
handler or accessing product memory. The application's mapped EXEC parameter
block distinguishes its child launch from COMMAND.COM launching samplers. The
trace proves the same capture descriptor before/after EXEC and no intervening
capture close. The PRN cases also check the absence of premature parent closes.
The observer verifies and restores its own interrupt chains before collecting
the report. One-byte writes are deliberately omitted from this trace, so it is
not a complete PRN write-call transcript.

The child's own snapshots show the live wrapper/vector and IER=9 at both ends,
RTS falling from asserted to held low while its foreground is suspended, and at
least 54 BIOS ticks elapsed. The peer observes XOFF/XON, fresh post-return DSR
and keyboard output without a return-key prompt. Startup CWD and UART/PIC/vector
snapshots restore on final exit. These are controlled serial/filesystem tests,
not stock-BBS sink combinations or physical printer/readiness/fault tests.

The first collector diagnostic inherited an assembler default that allowed
386-style long conditional branches. It failed on the explicitly selected 8086.
The new observer sources require `CPU 8086`; their isolated collection check and
the final five workflows pass. This was test code, not an application defect.

## Carrier loss and redial on the normal image

The existing reconnect test now accepts `--terminal` for a normal source-built
parent, using explicit saved display preferences. Its old `--build` diagnostic
selection remains available. Both ANSI/profile 4 and VT220/profile 6 pass at
25 physical rows, COM3/IRQ5 and combined flow.

A real DOSBox modem socket closure produces the first carrier loss. The actual
ASPECT child exits through its disconnect path; the parent clears stale flow
state, observes disconnection, receives ordinary menu keys to redial, and runs
the second script successfully in the same DOS process. JFT/private-owner
comparisons, lower-row/cursor replies, complete logical frame, final status,
clean modem commands and hardware restoration pass. The second script writes
RECONNECTED, and subsequent manual keyboard/query service works.

This regresses the Gateway-enabled image; it does not open Gateway during the
loss/redial scenario. The peer is synthetic and DOSBox generates carrier/result
codes. No physical modem, stock BBS reconnect or analog timing claim follows.

## Stock Enigma cancellation and retry

The same normal executable completes one authenticated stock Enigma session
through the accepted staged SynthModem Telnet proxy, COM3/IRQ5 at 19200/HARD.
A real BIOS Escape cancels a ZMODEM download after data reaches disk. An
independent audit verifies the 4,096-byte source-prefix partial, an empty receive
directory before retry, normal BBS listing/search interaction, and an exact
65,539-byte retry containing every byte value. Standard packet CRCs, controls,
finish, raw proxy byte equality and both protocol-helper exits are checked.
The canceled helper exits nonzero; the retry helper exits zero. No post is saved.

This is one DOS process, authenticated session and proxy connection. Gateway is
not invoked during the transfer. It does not establish upload, every protocol,
transfer interrupted by carrier loss, SIP/DSP/audio or physical flow acceptance.

## Replay and remaining gates

Use the pinned Nix shell. `standalone/test_gateway_sinks_dos.py` takes an explicit
`--terminal` and fresh `--output`. `standalone/test_modem_large_reconnect_dos.py`
takes `--terminal`, `--runner`, `--rows 25`, `--profile 4` or `--profile 6` and `--flow both`.
`lab/bbs/test_proxy_cancel_retry_dos.py` runs the owned stock Enigma recipe;
`lab/bbs/audit_proxy_cancel_retry.py` independently audits its capture.
`standalone/record_gateway_composition.py` rechecks hashes and raw sink/child/
trace evidence and binds all three groups into the receipt.

Device faults, additional BBS/file-owner combinations, sustained real-peer flow,
uploads and carrier-loss-during-transfer, wider profiles/layouts/protocols,
Microsoft DOS 6.22 and physical Boca/SPA2102/SynthModem acceptance remain open.
The remaining original file/DOS commands, directory/key tools, Chat and broader
ASPECT/emulation/protocol/Host parity remain in the full inventory. No physical
files, deployment selector, boot, network, adapter or live services changed.
