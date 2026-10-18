# Mystic localhost comparison

This lab runs the actual vendor Mystic 1.12 A48 Linux64 server at
`127.0.0.1:23232`. The source-built DOS terminal has completed login, file and
message indexed-menu navigation, arrow input and Escape return against it.
No public board, public account, message posting or physical modem is involved.

The [official download page](https://www.mysticbbs.com/downloads.html) identifies
A48 as the stable build. The pinned archive is
[`mys112a48_l64.rar`](https://mysticbbs.com/downloads/mys112a48_l64.rar), SHA256
`fb427b57d9627ef93008c561df807991bdd288b4a1fc1757dfb5bb5434f286a3`.
Vendor binaries, configuration, synthetic user records and captures stay under
ignored `build/bbs-lab/`; they are not repository inputs or redistributed files.

## Start and stop

From the repository root:

```sh
nix --extra-experimental-features 'nix-command flakes' develop ./nix#bbs --command python3 lab/bbs/mystic.py setup
./tools/dev --command python3 lab/bbs/mystic.py start
./tools/dev --command python3 lab/bbs/mystic.py bootstrap
```

Setup verifies the archive before extraction with Nix-provided `bsdtar`, then
runs the [vendor automatic installer](https://wiki.mysticbbs.com/doku.php?id=installation).
The server runs as this user, without Docker or a system service. Native ELF
execution currently uses the host Linux loader; the Nix shell manages extraction
and Python helpers. Cryptlib is absent, so SSH/TLS are outside this lab.

The pinned A48 server-record layout was corroborated through `mystic -cfg`.
Configuration enables only Telnet, selects IPv4, binds loopback and disables
the seven other server records. The corresponding options are described in
the [vendor server configuration guide](https://wiki.mysticbbs.com/doku.php?id=config_server_servers).
Check the actual listener with `ss -ltnp`; it must be `127.0.0.1:23232`.

The demo's art/menu paths did not load correctly with this repository's long
installation path. Setup supplies the short symlink
`/tmp/pcplus-mystic-lab-<uid>` and rewrites only verified length-prefixed path
fields inside the ignored vendor configuration. It refuses an unrelated existing
alias. The loopback address is allowlisted for repeated synthetic login tests.

Bootstrap creates or logs into the local fixture account `PCPLUSLAB`, password
`LoCtest42`, using the real vendor prompts. Its socket reference client supplies
controlled ANSI detection replies; bootstrap is account setup, not DOS evidence.
It leaves the vendor-generated welcome email unread. Stop the owned server with:

```sh
./tools/dev --command python3 lab/bbs/mystic.py stop
```

Shutdown is asynchronous and may take about ten seconds. Startup metadata and
the owned PID are in `build/bbs-lab/mystic/installation.json` and `server.pid`.

## Actual DOS navigation recipe

Build the source-only terminal first using the root build instructions. With
the server and fixture ready:

```sh
./tools/dev --command python3 lab/bbs/test_dos.py mystic \
  --port 23232 --label menu-navigation-final \
  --keys 'p4000 p c p l u s l a b enter p1500 s-l o s-c t e s t 4 2 enter p2000 n p1000 n p2000 f p2000 i p3000 down p500 up p500 escape p2000 q p2000 m p2000 i p3000 down p800 up p800 escape' \
  --wait 5
./tools/dev --command python3 lab/bbs/mystic.py audit --label menu-navigation-final
```

The harness first types `ATD`, then the schedule logs in, declines OneLiners
and welcome email, opens File menu (`f`) and File Base Listings (`i`), presses
Down/Up/Escape, returns to Main (`q`), opens Message menu (`m`) and Message Base
Listings (`i`), and presses Down/Up/Escape again. It then exits locally with
Alt-X. DOSBox `s-l`/`s-c` are shifted letters in the fixture password. Delays
are explicit waits for this local server; they are not a prompt-aware DOS driver.

The vendor sends `ESC[6n` before login. The DOS program actually replies
`ESC[25;80R`; the modem bridge strips Telnet negotiation but does not fabricate
ANSI replies. Login inputs are CR-terminated; OneLiners/email answers and menu
commands are single bytes. Up and Down leave DOS as `ESC[A` and `ESC[B`.

On 2026-10-17, terminal SHA256
`aca82619ad87a7e9aa259c4716a75eebb9483c204cbd0da17ab8c8b8a7d77029`
passed the actual 33.283-second run. The generic harness confirmed normal DOS
exit, restored UART hardware state, captured video, BBS connection, nonempty
display and unchanged binary during execution. The separate audit passed all
eight semantic checks, including ordered file/message index headings, actual
outgoing arrow pairs and the final rendered Message menu with `General Messages`
and `Command ->`. These establish this workflow; they do not establish every
Mystic feature or every indexed selection.

Evidence is in `build/bbs-lab/results/mystic/menu-navigation-final/`:

- `result.json`: binary hash, actual key schedule and generic checks.
- `mystic-audit.json`: semantic assertions and observed report/heading positions.
- `display.bin`, `serial-received.bin`: actual vendor application stream and DOS output.
- `screen.txt`, `SCREEN.BIN`: final rendered DOS text screen.
- Raw modem wire captures retain Telnet negotiation separately.

An earlier build stopped at the vendor's initial form-feed control. The final
run includes recovered real form-feed behavior and subsequent ANSI6 changes.
An empty display caused by a stale vendor session was explicitly rejected and
is not counted as a successful login. Rerun the audit after future changes;
normal process exit alone cannot prove interactive compatibility.

## Protocol unit checks

```sh
./tools/dev --command python3 lab/bbs/check_modem.py
```

Six groups exercise selected-baud CONNECT/TSPEED behavior, fragmented negotiation/subnegotiation, escaped IAC,
unsupported options, option withdrawal, bounded incomplete subnegotiation,
all-byte transport and unchanged ANSI/CPR/DA streams. A real localhost socket
unit fixture verifies that the modem waits for the serial client's CPR rather
than answering it. That peer is a protocol fixture, separate from the vendor
tests above. The contracts follow [RFC854](https://www.rfc-editor.org/rfc/rfc854),
[RFC1091](https://www.rfc-editor.org/rfc/rfc1091) and
[RFC1073](https://www.rfc-editor.org/rfc/rfc1073).

The remaining compatibility scope includes other screen sizes, public board
customizations, file-transfer protocols, physical RS232/Wi-Fi timing, sustained
traffic and other terminal encodings. This controlled comparison uses 80x25
ANSI-BBS negotiation, DOSBox-X's UART and a modeled Hayes/Telnet modem.
