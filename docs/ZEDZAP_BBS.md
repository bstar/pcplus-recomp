# 8 KiB reception and logged-in BBS transfers

The `d0274a22` source-built DOS terminal receives ZMODEM/ZedZap packets up to
8,192 bytes. The original 1 KiB limit made ENiGMA's stock `-telnet -8 sz` helper
fall back through repeated retransmissions. A retained 11,521-byte download used
29,380 protocol bytes with the previous `8c481cfd` client; the new client used
12,041, accepting packets of 1,024, 2,048, 4,096 and 4,353 bytes. These are
capture lengths for these fixtures, not a physical throughput benchmark.

## Runtime and memory

The receive and encoded-response buffers share a union. File callbacks consume
verified received data before responses overwrite it; continued subpackets are
explicitly tested. The 9,308-byte engine plus eight-byte live context fits the
existing 10,240-byte exclusive workspace policy. Sending remains limited to
1 KiB packets and waits for each packet's acknowledgment. Windowed sending,
automatic download detection and persisted partial-file resume remain open.

Near data/stack is 65,088 bytes (448 spare), resident code 63,038 bytes and
CONFIG_CODE 37,627 bytes. The retained parent uses 20,323 paragraphs including
PSP. Relative to the published `c51b0d9` checkpoint this adds 32 near bytes,
92 resident code bytes and seven parent paragraphs. No additional resident payload
buffer is allocated. All ten far callback identities/relocations, 115 bridge
pairs and 325 rejected damaged frames/pointers remain checked.

The accepted-progress deadline permits a worst-case quoted 8 KiB packet at each
configured baud: 30 seconds at 9600+, then 60/120/240/480/960 seconds at
4800/2400/1200/600/300. Incoming noise does not refresh accepted progress.
XMODEM/YMODEM retain their previous policy. If received files are installed but
the final OO is missing, the footer says `RX files saved; finish unconfirmed`.

## Actual BBS workflows

Both directions pass through the production DOS terminal, real UART ISR,
Hayes/Telnet bridge, synthetic file areas and logged-in local servers:

| Server | Download | Upload |
| --- | --- | --- |
| Synchronet `9de2c48d02` | PCXTEST.BIN, 11,521 exact bytes; return to Main | PCZUPA01.BIN, 12,337 exact bytes; official FileBase metadata; return to Main |
| ENiGMA `6c25317168` | PCXTEST.BIN, 11,521 exact bytes; subsequent search | PCZEU01.BIN, 12,337 exact bytes; official FileEntry metadata; subsequent file list |

The passive Python auditor independently checks source bytes, header/data CRCs,
offsets, retransmitted prefixes, ZEOF, ZFIN/OO, opposite-side controls and their
ordering against actual post-transfer menu input. Its 84 fixture checks include
bad CRCs, missing/late controls and retransmission after an initial ZEOF. Exact
DOS/server files and official server metadata separately establish storage.
ENiGMA server logs identify one authenticated connection, successful stock helper
exit and ordered return to menus. Hardware state, settings/directory accounting
and source immutability are checked in the DOS workflows.

ENiGMA's helper was absent from PATH. The owned fixture sets its executable path
to the Nix-loader-adapted stock Docker helper, preserving inherited `-telnet -8
sz/rz` arguments. It also sorts ZMODEM first. This bypasses the separately
observed fragmented-arrow selector problem, which remains unresolved. Login
animation settling and command-line clearing are explicit fixture steps; they
are not changes to the server's decoder or menus. Synchronet's synthetic account
uses a temporary daily-logon exemption, restored to zero and independently read
back; its level remains 50.

Ten attempts are retained: five passed and five failed. The failures were a
quota rejection, an arrow selector entering YMODEM, an old auditor that rejected
valid post-EOF recovery, and two login/menu pacing fixtures. The old auditor's
failed result remains unchanged even though the captured file and helper exit
were successful. Four passing runs belong to the current binary; the fifth is
an older Synchronet baseline. These distinctions are preserved in the report.

Two additional actual DOS sessions with lrzsz receive empty, one-byte and
65,797-byte files with CRC16 and CRC32. Independent capture audits confirm full
8,192-byte packets, exact files, post-transfer keyboard/DSR and restored hardware.
The linked 71-case test models a 16-byte UART FIFO and RTS with foreground
execution between interrupts. Its large-packet memory tests freeze BIOS time;
they do not measure physical timing. Earlier unbounded-FIFO fixture failures
are retained in ignored build logs.

## Evidence and limits

[Current validation](validation/zedzap-bbs.json) binds the runtime, sources,
retained captures, test results and source-only rebuild. The historical
[live ZMODEM report](validation/live-zmodem.json) retains its original binary and
memory accounting. Build artifacts, server installations and synthetic account
files stay outside public Git.

No physical RS232 WiFi modem, complete loss/cancel/timing matrix, other terminal
emulations, full menus, ASPECT or Host mode is established here. The ENiGMA
fragmented-key interaction issue still needs a client/server timing investigation.
All F01–F16 application completion gates remain open.

Component checks can be repeated with the pinned toolchain:

```
./tools/build test-zmodem-wire test-zmodem
./tools/dev --command python3 lab/bbs/check_zmodem_audit.py
./tools/build test-terminal
```

The optional stock-helper peer matrix uses `standalone/check_zmodem.py --sexyz`
with the owned helper path. Actual logged-in workflows use
`lab/bbs/test_zmodem_dos.py`; each invocation requires a fresh label, explicit
owned fixtures, paced keys and expected post-transfer input/replies. Uploads
also require an official metadata audit. `standalone/record_zedzap_bbs.py`
reconciles the retained frozen checkpoint; it does not rerun BBS connections or
rewrite the failed results.
