# Local BBS CRC YMODEM validation

The maintained DOS batch owner is exercised against the actual Synchronet and
ENiGMA½ SE/X/Y/Z helpers through the existing Hayes/Telnet modem bridge. It
does not replace the protocol peer, inject ACKs, coalesce escape sequences or
patch the BBS decoder. All accounts, files, configuration and captures belong
to the ignored loopback lab. Actual physical RS232/Wi-Fi modem tests remain
outstanding.

The current terminal is SHA256
`2dafc08b51450faf183e06f68d253eec410572cbfadedec5ab388e9e28b7aed6`.
It passes 30 independent actual DOS peer cases and 8 linked-instruction fault/UI
groups (23 inputs). Ordinary XMODEM regressions pass 7 receive groups/44 inputs
and 10 send groups/54 inputs on the same binary. A fresh public-source checkout
without originals, analysis databases, install files or previous outputs
reproduces 43 byte-identical DOS outputs. These are component milestones, not
completion of the original PCPlus application.

## Run a workflow

Build with `./tools/build terminal`. Alt-R/Alt-S opens the filename prompt;
F2 inside it selects YMODEM. Receive uses an existing directory such as
`D:\RECV\`; send uses a filespec such as `D:\SEND\*.BIN`. Both BBS and DOS
must select YMODEM. The test harness prepares its own isolated SEND/RECV trees.

The independent protocol peer requires an explicit runtime hash and a fresh
result label:

```sh
./tools/dev --command python3 standalone/test_terminal_ymodem_dos.py \
  --sha256 SHA256_OF_TERMINAL_EXE --label fresh-label --jobs 4
```

Cases cover empty/zero/binary/multiple files, unknown lengths,128/1024 headers
and mixed blocks, sequence rollover, bad CRC, header/data retries, duplicate
frames, repeated final headers, unsafe/existing targets, early EOT, excess
data, cancellation, partial batches and one-shot application escape sequences
after protocol ownership ends. Exact file contents, source metadata, actual
DSR/keyboard/video resume and42-byte hardware snapshots are checked.

`lab/bbs/test_ymodem_dos.py` accepts repeatable
`--file NAME.BIN=build/owned-source` arguments, paced actual DOS hotkeys,
explicit start/post menu inputs and expected subsequent BBS responses. Its
independent passive auditor requires block0 metadata, CRC/data sequence,
individual EOT/ACK/C closure and the final empty header. Downloads must have
exact declared lengths. Uploads must preserve every DOS source and match the
official server metadata and installed bytes. ENiGMA server logs additionally
prove one authenticated session, helper exit0, and ordered return to its file
list. Matching an old menu before the transfer cannot pass.

## Server configuration and final ACK

Synchronet uses pinned 3.22a commit
`9de2c48d0265b07e1a8406d8a55d31df4fad7ee8`, its official bootstrap helper and
the dedicated `pcplab` file area. ProtocolY already selects stock sY/ry.

ENiGMA uses pinned 0.5.1-beta commit
`6c25317168b762f7d9088a54d3f8295438827a0e`, its bundled helper adapted only
for the Nix ELF loader/library paths, and the dedicated `pcplus_transfer`
area. `./tools/bbs-dev --command python3 lab/bbs/ymodem_setup.py` selects that
helper path for YMODEM and puts Y first in the protocol selector. It preserves
inherited sY/ry arguments and stock server/decoder code, records a configuration
backup and refuses to restart while a lab connection is active.

Both actual helper receivers omitted the final empty-header ACK before
returning application text during uploads. Exact files and individual EOT
ACKs alone do not make that a standard ACK-confirmed batch success. The strict
failed attempts remain recorded. REA, original helper instruction replay and
source corroborate the producer-buffer cause in the Synchronet artifact;
ENiGMA's internal helper cause remains unresolved. See
[peer findings and evidence](YMODEM_PEER_FINDINGS.md).

The maintained terminal preserves the first application byte and ends with
`YM_END_UNCONFIRMED`, displaying `TX batch sent; ACK?`. It sends no additional
binary headers or CAN into the BBS menu. Timeout/NAK retain bounded retries;
this exception never applies to missing data-block/EOT ACKs. An explicit
`--expect-final-ack-missing` harness case verifies this compatibility policy,
while recording `standard_final_ACK: false`. Default audits still require the
real final ACK. This separation keeps peer defects visible.

ENiGMA's fragmented escape-key decoder remains a separate compatibility
boundary. The initial arrow-navigation failure and later successful Enter-only
login are preserved; neither makes its editor pass. Upload details pages may
start at different fields, so batch tests pace each actual form separately.
Readiness-probe ghost idle timers must be attributed by sessionID rather than
node number; they are not evidence of the current authenticated user timing out.

## Retained results

Latest workflows on the current runtime:

| Server | Direction | Files / exact stored bytes | Label | Final batch ACK |
| --- | --- | --- | --- | --- |
| Synchronet | Download | 1 / 11,521 | `ymodem-download-2` | Confirmed |
| Synchronet | Upload | 1 / 11,521 | `ymodem-upload-3` | Missing; compatibility case |
| ENiGMA½ | Download | 2 / 23,044 | `ymodem-download-batch-1` | Confirmed |
| ENiGMA½ | Upload | 2 / 23,044 | `ymodem-upload-batch-3` | Missing; compatibility case |

Each final workflow checks exact installed bytes, actual subsequent menu
input/response, sampled hardware restoration and configuration/accounting
preservation. Uploads also preserve each DOS source's bytes/inode/size/mtime.
The two ENiGMA batch files are 11,522 bytes each. Per-file metadata trims
transport padding; it is not retained in their installed DOS/server files.

Five earlier BBS attempts remain failed: the strict missing-ACK cases, initial
ENiGMA arrow navigation, incomplete batch details submission, and an incorrect
assumption about which uploaded file would sort first. The corrected batch
details path uses three Tabs on the first observed form and two on the second,
with sufficient rendering time. The file-list check avoids assuming a particular
sort order and still requires the actual area and independently logged list menu.
No recorded failure is relabeled as a successful run.

Two initial independent DOS probes also retain harness failures: their
10-second resume deadline expired before the queued 15-second keyboard check,
although file transfer and DSR had succeeded. The corrected bounded deadline
allows the scheduled key delay plus 10 seconds; all 30 release cases pass.

The authoritative [BBS report](../../docs/validation/bbs-ymodem.json) retains
failed attempts and successful retries with individual runtime hashes,
independent protocol audits, official metadata and artifact hashes. The
[DOS report](../../docs/validation/terminal-ymodem-dos.json) and
[linked fault/UI report](../../docs/validation/terminal-ymodem-live.json) record
their separate evidence scopes. No raw captures or proprietary executables are
published.

`standalone/record_ymodem.py --dos-run LABEL --bbs-run SERVER:LABEL` records
explicitly selected runs. Historical binaries remain separate from the
workspace runtime, and failed attempts are not converted into successes.
All raw commands, synthetic fixtures, source/destination files and captures
remain under the selected `build/.../LABEL` directory.
