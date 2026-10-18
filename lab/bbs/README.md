# Local BBS compatibility lab

Test the actual source-built DOS terminal against local Synchronet, ENiGMA½
and Mystic servers. Downloaded server programs, source checkouts, user databases,
wire captures and DOS snapshots stay under ignored `build/bbs-lab/`.
All listeners must bind loopback. Accounts and messages are synthetic.

Use the pinned Nix toolchains:

```sh
./tools/build terminal test-terminal
./tools/bbs-dev --command python3 lab/bbs/enigma.py setup
./tools/bbs-dev --command python3 lab/bbs/enigma.py start
./tools/dev --command python3 lab/bbs/test_dos.py enigma --port 23233
```

ENiGMA's script provides setup/start/stop/status commands; Synchronet provides
setup/serve/probe, with `serve` staying in the foreground. Mystic provides its
own setup/start/stop/probe workflow. Read their
metadata and scripts before choosing a version: the Synchronet bootstrap uses
an explicitly identified development snapshot. The optional BBS shell supplies
Node, native build tools and Synchronet runtime libraries without Docker or
changes to system groups.

`test_dos.py` starts a private serial bridge, launches the real DOS executable
in DOSBox-X, types ATD using emulated BIOS keys, and connects the chosen local
BBS. The bridge models a Hayes Wi-Fi modem: it handles Telnet IAC negotiation,
TTYPE and NAWS, serial rate and software flow control. It passes ANSI queries
unchanged to DOS and never synthesizes terminal capability or cursor replies.
It is a limited test model, not a replacement modem firmware.

Each run records the exact DOS executable hash, both Telnet directions,
terminal display/input bytes, modem negotiation, actual B800 video memory and
independent before/after IRQ/UART/PIC snapshots. `--keys` accepts DOSBox-X ADDKEY
syntax for login/menu workflows; `--label` retains separate runs. A normal DOS
exit is a transport/cleanup check; successful login and menu interaction require
separate evidence from the screen, response bytes and server logs.

## Verified results

The same source-built ANSI executable passed all three local workflows:

| Server | Actual DOS interaction verified | Recipe |
| --- | --- | --- |
| Synchronet 3.22a development snapshot | Login, bulletin statistics, file section, return, empty message-area read and return to Main | [Synchronet](synchronet.md) |
| ENiGMA½ 0.5.1-beta | Login, Main → Messages → Main → Files, including the original failing stock screen | [ENiGMA½](enigma.md) |
| Mystic 1.12 A48 | Login, indexed file/message screens, Up/Down and Escape return | [Mystic](mystic.md) |

Every final run restored the independently sampled IRQ/UART/PIC state exactly.
All three workflows also pass on COM2 at19200/8N1 with hardware flow selected.
Use `--com 2 --baud 19200 --flow HARD` to select that case. The sampler follows
the selected UART; the bridge reports matching CONNECT/TSPEED rates. DOSBox
nullmodem holds CTS ready, so this does not exercise physical handshake stalls.
The initial Synchronet/Mystic runs exposed missing FF handling. ENiGMA½ exposed
SOH/VT/CAN controls inside a malformed bundled theme's SAUCE metadata. Recovered
original handlers and the proved ANSI initialization now pass those cases.
The stock server artwork was kept unchanged.

[Recorded results and artifact hashes](../../docs/validation/bbs-matrix.json)
identify the exact executable and distinguish semantic checks from generic
transport/cleanup checks. Physical RS-232 Wi-Fi modem behavior, the user's
specific failing public-board screens, transfers, full-screen editing and
advanced protocols remain separate validation. This milestone is an interactive
terminal, not the complete PCPlus application.

## PRM startup regression

The current primary matrix repeats all three read-only workflows with
`TERMINAL @D:\TEST.PRM` inside DOS. The synthetic partial configuration selects
COM2/19200/8N1/HARD; no serial CLI option masks the import. The harness option
`--config-fixture` creates this fixture and verifies it is unchanged. It never
loads private dialing or installed configuration data. Current results and
historical executable hashes are distinguished in
[`bbs-matrix.json`](../../docs/validation/bbs-matrix.json). Physical modem timing,
transfers and the complete PCPlus application remain outside these results.

## Automatic dialing regression

`--dial-fixture` builds a synthetic modem+serial PRM and launches
`TERMINAL @D:\TEST.PRM /D:lab.local:port`. The DOS controller expands and sends
configured ATZ and ATD commands; the keyboard schedule contains no typed ATD.
Current primary cases in the matrix cover all three real local servers through
this path. The retained serial capture proves the command prefix; server/menu
audits verify successful navigation rather than assuming normal exit is enough.
See [connection controller](../../docs/CONNECTION.md) for policy and boundaries.

## Native directory regression

`--directory-fixture --directory-browser --entry 3` launches the native
chooser with no `/N` or `/D`, then selects entry3 using Down/Down/Enter.
The synthetic PRM uses COM1/38400 while that record selects COM2/19200. Current
primary matrix cases prove actual configured ATZ/ATD output and subsequent
message/file navigation on all three local servers. The PRM and independent
hardware snapshots remain unchanged. On exit, successful-call accounting changes
only the selected record's date/count bytes; the harness verifies the other
23,039 directory bytes exactly. `--directory-fixture` without
`--directory-browser` instead uses explicit `/N` selection.

The latest `directory-accounting` runs use the same executable, SHA-256
`1ddb64bdba5e94b1522cc51898eb8e6a4a4d77256d76a6c01dac287cfa9a9964`,
on all three servers. Synchronet verifies file-menu return and an empty message
read; Mystic verifies indexed file/message screens with Up/Down and Escape;
ENiGMA verifies Main → Messages → Main → Files against its authoritative session
log, along with actual DOS device/cursor replies and arrow bytes. Historical
results in the matrix retain their original executable hashes.

To audit an existing run through the pinned toolchain:

```sh
./tools/dev --command python3 lab/bbs/synchronet.py check-dos --label directory-accounting
./tools/dev --command python3 lab/bbs/check_enigma_dos.py --label directory-accounting
./tools/dev --command python3 lab/bbs/mystic.py audit --label directory-accounting
```

For owned ENiGMA runs, `test_dos.py` records the server log's starting byte offset
before DOS launches. The ENiGMA audit requires exactly one new server session,
authentication, ordered menu transitions, real DOS replies and the final File
Base screen. An extra concurrent login fails session isolation instead of being
silently attributed to the test.
