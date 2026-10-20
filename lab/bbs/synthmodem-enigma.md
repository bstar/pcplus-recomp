# Stock ENiGMA sessions through the SynthModem candidate

The actual source-built DOS terminal now passes an authenticated menu route and
an unsaved editor route through the isolated SynthModem TelnetProxy candidate.
The owned server is the unchanged stock ENiGMA checkout at
`6c25317168b762f7d9088a54d3f8295438827a0e`, listening only on127.0.0.1:23233.
The live board is not used, changed or restarted.

The path is DOSBox-X UART -> synthetic Hayes call adapter -> actual candidate
TelnetProxy -> immediate byte-transparent TCP observer -> owned ENiGMA. The
observer has no batching timer, Telnet codec, terminal responses or keyboard
rewriting. PCPlus automatically sends ATZ/ATD1 with fixed COM1/38400/8N1/HARD;
BIOS keys enter the observer's local address at CONNECT>, then the synthetic
lab login and navigation recipe. No hostname goes to the modem in ATD.

The menu route has16 passing checks, including authoritative server-confirmed
authentication and Main -> Messages -> Main -> Files, visible final File Base,
actual DOS DA/CPR replies, exact42-byte UART/PIC/vector restoration and unchanged
profile/application/candidate/server inputs. The editor route has18 passing
checks: authentication, entry into New Post, typed ABCDE, Home moving to column1,
Insert entering overtype, no saved post and normal DOS cleanup.

The separate read-only auditor also verifies that every decoded outgoing TCP
payload byte equals the serial input after ATZ/ATD1/address entry, and that the
complete decoded BBS display appears unchanged on actual serial output. It binds
the saved session log, wire/video hashes and source freezes, checks named menu
order, and measures all eight exercised editor keys. Home is ESC[H, End ESC[F,
Insert/Delete/PageUp/PageDown are CSI2~/3~/5~/6~, Tab is09 and Ctrl-Y is19.

The [recorded receipt](../../docs/validation/synthmodem-enigma.json) retains
34 producer checks plus independent audits and observed key/chunk spans.
Accepted labels are `synthmodem-enigma-menus-01` and
`synthmodem-enigma-editor-01`.

These results are specific to this path. The observer received each measured
Home/End/Insert/Delete/PageUp/PageDown sequence in one complete TCP read. That is
evidence about these runs, not a promise about future TCP boundaries at the BBS.
There is no explicit30ms batching policy here, but operating-system/socket
packetization can differ from the existing Python modem path. Earlier stock
ENiGMA fragmented-input and immediate-bridge failures remain valid; this pass
does not fix or replace those results or establish robustness under arbitrary
fragmentation. The stock server source was not patched.

```sh
./tools/dev --command python3 lab/bbs/synthmodem_bbs_dos.py \
  --candidate build/bbs-lab/synthmodem-telnet-03/candidate \
  --output build/bbs-lab/synthmodem-enigma-menus-new
./tools/dev --command python3 lab/bbs/synthmodem_bbs_dos.py \
  --candidate build/bbs-lab/synthmodem-telnet-03/candidate \
  --output build/bbs-lab/synthmodem-enigma-editor-new --route editor
./tools/dev --command python3 lab/bbs/audit_synthmodem_bbs.py \
  --output build/bbs-lab/synthmodem-enigma-editor-new
```

Use new output directories and run the two routes sequentially so the captured
server-log boundary identifies exactly one new lab session. The harness requires
the existing owned loopback fixture with its clean pinned source and synthetic
account. It does not install packages or start/reconfigure a server. Original
test recipes come from `editor-recipes.json`; the unsaved editor route never
sends Enter after body editing starts and closes the connection without saving.

## Logged-in automatic download

The [download receipt](../../docs/validation/synthmodem-enigma-download.json)
adds21 checks plus an independent audit through this same candidate. An actual
DOS/BBS session searches for the existing owned `PCXTEST.BIN`, tags it, selects
Download and starts the existing ZedZap helper. The PRM enables automatic ZMODEM
reception into `D:\RECV\`; there are no Alt-R/Alt-S/F2 transfer keys.

All11521 bytes arrive exactly, with CRC-validated ZFILE/data/ZEOF/ZFIN/OO and
four corroborated opposite-direction controls. Observed packet payload sizes
are1024,2048,4096 and4353 bytes. A new real keyboard search succeeds after the
transfer. The official FileEntry API's download count advances17 ->18, its source
bytes remain unchanged, staging disappears and UART state restores. The readonly
auditor reconstructs decoded stream timing from raw TCP chunks, repeats the
protocol/control audit and compares complete serial payloads and stored files.

The owned fixture already has the helper path configured and ZedZap sorted
first. No server configuration, source or running process was changed for this
run, and no protocol-selector arrow behavior is established. Source hashes in
the earlier menu/editor receipt identify their earlier test-harness revision;
they remain historical results, not reruns under this new download branch.

```sh
./tools/dev --command python3 lab/bbs/synthmodem_bbs_dos.py \
  --candidate build/bbs-lab/synthmodem-telnet-03/candidate \
  --output build/bbs-lab/synthmodem-enigma-download-new --route download
./tools/dev --command python3 lab/bbs/audit_synthmodem_bbs.py \
  --output build/bbs-lab/synthmodem-enigma-download-new
```

The exact source fixture and helper are additional frozen runtime inputs, never
ordinary application build inputs. Uploads, other protocols and error/retry/cancel
routes through this BBS path remain open.

SIP/RTP, answering-modem DSP, analog audio, physical modem/UART timing, broader BBS
transfers and the Boca/SPA2102 remain untested here. The independent-peer
[ZMODEM composition](synthmodem-dos.md) remains separate evidence. All complete
PCPlus application gates remain open.
