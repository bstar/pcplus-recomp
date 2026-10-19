# Repeated downloads and receiver ownership

`enigma_repeat_download_dos.py` runs three actual transfer processes in one
authenticated DOS/ENiGMA connection. It receives the generated long-name ZIP01,
requests it again so the existing alias must be skipped, then opens ZIP02 and
receives that file. It opens the correct NFO page after each transfer.

The canonical DOS keyboard/UART harness is unchanged. Its modem boundary uses
the existing passive observer, and synthetic PRM fields enable automatic
ZMODEM reception into the owned test drive. The test emits no protocol replies;
the production DOS engine and the real ENiGMA protocol helper perform every
handshake and file operation.

Both received sessions must pass the independent ZMODEM metadata/data CRC,
byte-exact source, receiver controls and ZEOF/ZFIN/OO audit. The middle session
requires a CRC-valid ZFILE offer followed by the actual receiver's `ZSKIP`, no
data/EOF, the receiver's finish reply and sender `OO`. Cross-direction timestamps
must put those responses after their corresponding offer/finish. A subsequent
real NFO command and matching game-specific page are required for every session.

A passive task snapshots the receive directory after each confirmed finish.
ZIP01's inode, length, mtime, ctime and SHA-256 remain identical after its skip
and after ZIP02 arrives. This detects rewriting the same bytes as well as content
replacement. The final directory contains only `8868026D.ZIP` and
`FFF6D09D.ZIP`, each 1301 bytes matching its generated source. No staging file
remains after any finish. The server log must show three successful protocol
processes in order within one login, with no saved posts. Normal DOS exit and
restored interrupt/serial hardware are retained canonical harness checks.

The observed sequence passes. A separate replay changes one condition at a
time: file data, ZSKIP CRC, skip finish-reply CRC, sender OO, post-skip NFO text,
expected source bytes and ZSKIP chronology. All seven corruptions reject.

With the isolated [search fixture](enigma-search.md) prepared and running:

```sh
./tools/dev --command python3 lab/bbs/enigma_repeat_download_dos.py \
  --candidate build/bbs-lab/NEW/candidate --label unique-repeat-label
./tools/dev --command python3 lab/bbs/check_enigma_repeat_audit.py \
  --candidate build/bbs-lab/NEW/candidate --label unique-repeat-label
```

Use a new output label; old captures are preserved. Only source/menu/art copies
and generated archives are used. This does not install the staged decoder on
the live board, test its actual catalog or replace physical RS-232 Wi-Fi modem
validation. No whole-application gate closes. See the
[validation record](../../docs/validation/enigma-repeat-download.json).
