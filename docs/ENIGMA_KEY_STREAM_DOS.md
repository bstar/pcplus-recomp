# ENiGMA keyboard framing: actual DOS comparison

The isolated server correction now has actual DOS evidence. With the same
`731418bd` executable, canonical editor keys, COM2/19200/8N1/HARD settings and
immediate byte-transparent modem forwarding, stock ENiGMA reproduces the Home
and Insert failures; the patched instance passes all seven editor checks.

| Run | Outcome |
| --- | --- |
| `key-stream-7314-stock-editor-1` | DOS harness passes; all eight exercised key sequences reach the wire; Home cursor movement and Insert/overtype fail; no post saved |
| `key-stream-7314-editor-1` | Same keyboard recipe and binary; seven editor checks pass, including Home and Insert; no post saved |
| `key-stream-7314-editor-zmodem-2` | One authenticated session enters an editor, discards its draft, automatically receives a file, and searches the file list afterward; all 20 checks pass |
| `key-stream-7314-editor-zmodem-1` | Retained failed recipe: Escape did not leave the message menu; no validated ZFILE; corrected recipe uses Q plus Enter |

The successful combined session transfers exactly 11,521 bytes of
`PCXTEST.BIN`, SHA-256
`3a15e1b5f15c8a5f8acb69e2cbc12e825e5f19ea2455494cca6478731e9543e6`.
The passive protocol auditor verifies CRC-valid framing, receiver negotiation
after the automatic invitation, ZEOF, ZFIN/OO and actual post-transfer keyboard
input/menu output. No local transfer keys or fabricated protocol replies are
used. The DOS configuration and source file remain unchanged, no staging file
remains, and the UART/vector sampler matches before and after. Official ENiGMA
FileEntry readback confirms download count 17 -> 18, matching file size/hash and
the separate physical source path. The patched instance's message count stays
1 -> 1 and its session log contains no saved post.

This isolates a server-side decoder boundary. The DOS executable is unchanged:
`731418bde8f3264d5f6c987195eb54b20c86a2981259ea1c721ba252e3c9a776`.
The server starts from upstream revision
`6c25317168b762f7d9088a54d3f8295438827a0e`, with the
[experimental patch](../lab/bbs/patches/enigma-key-stream/README.md).
All 1,202 exported tracked files match the clean pinned checkout byte-for-byte
except `core/client.js`; the only added core file is `core/key_stream.js`.
Git's checkout/archive line-ending transformations are retained in that
comparison; it is not a claim that every raw Git blob equals its checkout bytes.

The patched fixture listens on loopback port 23234. It receives SQLite backup
snapshots of the two synthetic fixture users and copies of the owned file area,
menus and helper. Configuration rewrites point to the candidate tree. Official
configuration readback confirms separate database, log, drop and mail paths;
all 21 observed writable file-descriptor paths of its live Node process were
under that tree. Only installed Node dependencies are reused. The stock server
on 23233 is neither patched nor restarted. The owned experimental server was
stopped after testing; its state remains available under ignored `build/`.

The harness records the exact server-log path, inode and initial byte offset.
The passive auditors distinguish stock and experimental results and reject an
incorrect inode or a log outside owned build fixtures. Six synthetic boundary
controls cover foreign sessions, path/inode identity and invalid extents.
The existing 88 ZMODEM auditor checks and ten transfer-auditor control groups
also pass. These controls validate the auditors; the DOS runs provide the
compatibility evidence.

The frozen [report and artifact hashes](validation/enigma-key-stream-dos/report.json)
include all four outcomes, official readbacks, source comparison, 92 local
artifact hashes and the successful wrapper's before/after input hashes.
Original executables, databases and binary media are excluded from Git.

To reproduce with a new candidate and the existing pinned stock fixture:

```sh
./tools/bbs-dev --command python3 lab/bbs/patches/enigma-key-stream/check.py \
  --source build/bbs-lab/enigma/source --output build/bbs-lab/key-stream-new
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py setup \
  --candidate build/bbs-lab/key-stream-new/candidate
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py start \
  --candidate build/bbs-lab/key-stream-new/candidate
./tools/dev --command python3 lab/bbs/enigma_key_stream_dos.py editor \
  --candidate build/bbs-lab/key-stream-new/candidate --label key-stream-editor-new
./tools/bbs-dev --command node lab/bbs/enigma_key_stream_readback.js \
  build/bbs-lab/key-stream-new/candidate
./tools/dev --command python3 lab/bbs/enigma_key_stream_dos.py editor-transfer \
  --candidate build/bbs-lab/key-stream-new/candidate --label key-stream-transfer-new
./tools/bbs-dev --command node lab/bbs/enigma_key_stream_readback.js \
  build/bbs-lab/key-stream-new/candidate
./tools/dev --command python3 lab/bbs/packetization_editor_probe.py \
  --delay-ms 0 --label key-stream-stock-editor-new
./tools/bbs-dev --command python3 lab/bbs/enigma_key_stream_fixture.py stop \
  --candidate build/bbs-lab/key-stream-new/candidate
```

Run these sessions sequentially. Preserve the before/after readbacks if comparing
download counts; fresh snapshots can start with different inherited counts.
The stock experiment intentionally reports an editor failure. The original
failed recipe remains evidence rather than being overwritten by the correction.

The patch's 100 ms first-byte deadline still needs delayed-network evaluation.
This checkpoint covers one editor recipe and one same-session download, not
every editor/view, transfer direction, protocol or terminal profile. It does
not change an unmodified remote BBS, prove physical RS-232 modem behavior, or
close F04/F05/F08 or any other whole-application gate. No upstream issue or PR
has been submitted. Wider network timing, transfer ownership, physical hardware,
full UI/emulations/protocols, ASPECT and Host work remain in scope.
