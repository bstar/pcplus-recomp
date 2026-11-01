# Telephone logging with stock BBS editors

A new optional `--status-geometry` build reserves physical row 25 for status and
advertises a coherent 80×24 terminal. The call-log candidate now passes actual
owned ENiGMA and Synchronet editor workflows through the installed SynthModem
proxy, with logging enabled and exact independent screen comparisons.
This is selected application composition, not a complete PCPlus replacement or
physical acceptance.

## Geometry and source-built identities

The earlier logger variant used 25 logical rows while the tested directory
candidate used 24. The new explicit option gives the logger the same status-row
boundary without changing existing defaults or requiring the separate directory
adoption/native-reset ownership variants to coexist.

New image: `build/terminal-phone-log-bank-d882144fee4f/TERMINAL.EXE`.
SHA256: `003bc6b7a0529c737b697c1149d2cfecfef930b5e96406df9dba31d9c137380f`.

The file differs from the existing `2c5f5fc4...` logger at exactly five geometry
bytes: last row, row count, screen bottom, origin bottom and erase-cell count.
Code, relocations and memory extents are otherwise unchanged. The near group
retains 64,752 bytes/784 spare and resident code 65,530 bytes/six spare. The memory
inspector now verifies coherent geometry in every build; this option requires 24
rows. Rebuilding the default logger still produces the exact old executable.

The ASPECT helper was refreshed from current source and reproduces its existing
`495d4852...` image. No original executable, installation or REA database is a
build input. A clean 1,745-file public export of `e3f6645` reproduces the new
terminal exactly and repeats all 42 native logging/access/flow workflows.

A separate committed DOS geometry test sends cursor probes before and after
RIS, then scrolls 24 numbered rows and compares the complete final viewport with
an independent 24-row reference. The new candidate matches all 1,920 cells and
both bottom-row replies. The old 25-row control is deliberately rejected by that
contract: it reports 25 and differs in 27 cells. This validates selected runtime
reset/scroll behavior as well as the initialized words.

## Actual BBS workflows

The test PRM enables telephone logging, and an explicit DOS PCPLUS fallback
binds it to the owned test drive. A passive COM3/IRQ5 observer follows the actual
parent's event, queue and disk owners. Both sessions require one heading and
one exact START/END pair, the original generation and timestamps, exactly two
append attempts, no retry acknowledgements and START committed while online.
The clock oracle permits the real multi-minute editor session instead of the
short synthetic-call limit.

**ENiGMA:** actual authentication and 24-line draft entry, Page Up, an inserted
edit, Page Down and an unsaved disconnect all pass. The final delivered prefix
contains 88,157 bytes; the independent reference matches all 1,920 raw character/
attribute pairs and actual CPR 22;8. The log records the MODEM target and a
2:04 call. Server-session evidence requires that no post was published.

**Synchronet:** the source-built ASPECT child completes the real login/menu/
subject sequence before returning to the parent editor workflow. Stage markers
are written only after actual matcher success. Real BIOS keys exercise the
editor; the held continuation proves normal Ctrl-Q abort. All1,920 cells and
CPR 5;8 match after 22,689 delivered bytes. The directory name/target and 51-second
call are logged once. Server inputs, message bodies and post/mail/transfer
counters remain unchanged.

Seven copied-artifact screen controls pass for each capture: unchanged,
character, attribute, cursor, truncated prefix, unsupported font and truncated
proxy input. The reference consumes only its own actual probe reply. All other
outgoing bytes remain bound to the real proxy. ENiGMA retains the previously
declared default-CP437 font projection; font pixels and every intermediate
frame are outside these comparisons.

## Reproduction and remaining work

See the [receipt](validation/phone-log-stock-bbs.json) for the exact candidate,
source revisions, geometry words, public replay, session logs, screen audits,
controls and unchanged published-package hashes. With the owned loopback
servers already running, use fresh labels and run shared-server sessions
consecutively:

```sh
./tools/dev --command python3 lab/bbs/test_synthmodem_proxy_dos.py \
  --runtime /home/bstar/projects/synthmodem \
  --terminal build/terminal-phone-log-bank-d882144fee4f/TERMINAL.EXE \
  --label log-enigma-check-01 --framing-ms 250 --byte-delay-ms 20 \
  --screen-reference --multiline-editor page-down --phone-log
./tools/dev --command python3 lab/bbs/test_synchronet_screen_reference_dos.py \
  --runtime /home/bstar/projects/synthmodem \
  --terminal build/terminal-phone-log-bank-d882144fee4f/TERMINAL.EXE \
  --label log-synchronet-check-01 --phone-log
./tools/dev --command python3 standalone/prove_phone_log_existing_terminal.py \
  --terminal build/terminal-phone-log-bank-d882144fee4f \
  --output build/phone-log-bbs-geometry-public-repeat-01 \
  --commit e3f6645 --extended --permissions --slow --watermark
```

Run `lab/bbs/audit_screen_reference.py` against each result and its matching
bridge directory for the independent comparison. The new geometry oracle is
`standalone/test_status_geometry_terminal.py`; its source revision is recorded
separately from the application/public-export snapshot.

This uses synthetic Hayes/nullmodem transport, actual local proxy code and
stock owned BBS servers with 250ms key framing/20ms input pacing. Unframed
operation, carrier loss/reconnect while logging, long transfers, remaining
ASPECT/child paths, full original-menu/feature composition, every frame/profile,
physical Boca/SPA2102 and card deployment remain open. The published `c41df22f...`
package and card are unchanged. No live BBS, bridge service, ATA or host network
configuration was changed; only owned fixtures and ignored build storage were used.
