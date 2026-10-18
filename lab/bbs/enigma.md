# ENiGMA½ compatibility lab

This runs the actual upstream BBS locally, with its stock Mystery Skull theme
(`luciano_blocktronics`) and official menu templates. All source checkout,
Node dependencies, databases, users, logs and captured sessions stay under
ignored `build/bbs-lab/enigma/`. The Telnet listener explicitly binds only
`127.0.0.1:23233`; SSH, WebSockets and content servers are disabled. No public
board is contacted and no messages are posted by these tests.

Upstream is pinned to commit
`6c25317168b762f7d9088a54d3f8295438827a0e`, package `0.5.1-beta`, with
`package-lock.json` SHA-256
`8fcaecda3a4b1756ad295be95486cbdd5b9afea005949ac3da8822224c822d56`.
The Nix-managed Node used for installation and execution is `v24.18.1`.
The official [manual installation instructions](https://enigma-bbs.github.io/installation/manual/)
require Node22 or newer. [Project start guide](https://enigma-bbs.github.io/start/).

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma.py setup
./tools/bbs-dev --command python3 lab/bbs/enigma.py start
./tools/bbs-dev --command python3 lab/bbs/enigma.py status
./tools/bbs-dev --command python3 lab/bbs/enigma.py stop
```

`setup` installs the locked local dependencies with `npm ci` and `HUSKY=0`,
then creates synthetic accounts through the upstream user API. It does not use
NVM, Docker, global npm installations or real credentials. Stop an existing lab
server before reinstalling its dependencies. The test user is `loclab`, password
`LoC-Lab-2026!`; a separate synthetic first/admin account is created so this
ordinary test user has the normal `users` group. Metadata is saved in
`build/bbs-lab/enigma/metadata.json`.

## Actual DOS tests

The modeled Hayes/Telnet bridge handles IAC negotiation; ANSI replies and
keyboard bytes come from the actual source-built DOS terminal under DOSBox-X.

```sh
./tools/dev --command python3 lab/bbs/test_dos.py enigma \
  --port 23233 --label initial --wait 15
```

The initial connection reached and rendered the stock login matrix. A subsequent
actual DOS test pressed Down/Up in that matrix, selected Login and entered the
synthetic credentials. The server recorded successful authentication and the
DOS video dump showed the login-success art. Both tests exited cleanly and
independently verified IRQ/UART/divisor/PIC restoration. These observations
establish initial rendering, real matrix interaction and login; they do not
alone prove the remaining menus or every BBS feature.

The login keys, after the bridge's initial `ATD`, were:

```text
p8000 down p600 up p600 enter
p5000 l o c l a b enter
p2500 L o C - L a b - 2 0 2 6 ! enter
```

The stock post-login path includes login art, last callers, who's online,
oneliner prompt, optional newscan and user statistics. Achievements and returning
caller state can insert more pauses. At the oneliner prompt Escape declines
without posting; `N` declines newscan. Main-menu `M`+Enter opens messages,
`Q`+Enter returns, and `F`+Enter opens files. Authoritative menu transitions are
recorded as `menuName` in `source/logs/enigma-bbs.log`; a normal DOS exit alone
is insufficient evidence of successful menu navigation.

## Real failure and recovery

The original full-menu DOS run failed after 33.515 seconds entering
`fullLoginSequenceOnelinerz`. Cleanup still restored hardware. The captured
wire and CPU replay identified service `0f62` (VT), at input index21236.

The upstream stock file
[`art/themes/luciano_blocktronics/ONELINER.ANS`](https://github.com/NuSkooler/enigma-bbs/blob/6c25317168b762f7d9088a54d3f8295438827a0e/art/themes/luciano_blocktronics/ONELINER.ANS)
is 1,965 bytes. Its `SAUCE00` marker starts at byte1924, leaving only41 bytes
instead of a complete128-byte record, and it contains no DOS EOF byte1A.
The generic `art/general/ONELINER.ANS` has a complete128-byte record and EOF.
The pinned [`core/art.js`](https://github.com/NuSkooler/enigma-bbs/blob/6c25317168b762f7d9088a54d3f8295438827a0e/core/art.js)
`sliceAtEOF()` preserves art when no EOF marker is found, so this malformed
stock theme sends its metadata as terminal input. The malformed theme file SHA-256 is
`2adc57a2fd56e0862d1ab206d8d988e2f7454158457abc98303f43ca90ca80c9`.
The display visibly prints
`SAUCE00` and the date before the binary bytes arrive. Fixtures are unchanged.

This uncovered missing reconstructed controls rather than proving a general
VT problem in the original PCPlus. The actual original SOH/VT/CAN helpers are
now recovered as240 exact bytes in `reconstruction/input_controls/`, with
real conditional behavior and explicit traps for unrecovered special modes.
Public regressions and the complete captured failure-wire replay pass; the
synthetic public fixture needs no private capture. See
[INPUT_CONTROLS.md](../../docs/INPUT_CONTROLS.md). The final ANSI6 DOS run passed after64.393 seconds, with the server recording
successful login followed by `mainMenu → messageBaseMainMenu → mainMenu →
fileBaseMainMenu`. The actual DOS screenshot shows the stock File Base menu,
and exit restored IRQ/UART/divisor/PIC state exactly. The executable hash was
`aca82619ad87a7e9aa259c4716a75eebb9483c204cbd0da17ab8c8b8a7d77029` and
remained unchanged throughout. Evidence lives in
`build/bbs-lab/results/enigma/menus-ansi6/`, including `server-menus.json`,
video dump, wire transcripts and restoration snapshots. This verifies these
menu paths; file transfers and the remaining feature areas are still untested.

## UI integration regression

The current UI-integrated executable was retested through the same actual DOS
login/menu recipe without restarting the owned server. Session `KMU7ym9r61W`
authenticated and the authoritative server log recorded `mainMenu →
messageBaseMainMenu → mainMenu → fileBaseMainMenu`. The video dump shows the
stock File Base menu. All six harness checks passed in 64.409 seconds, including
normal exit, unchanged executable and exact IRQ/UART/divisor/PIC restoration.

This run used executable SHA-256
`9a4308db775ca40fb7ff3dacf6169dff035b1350341cc852aedf5d6f9d0ede6f`.
Evidence is retained in `build/bbs-lab/results/enigma/ui-integrated/`, including
`server-menus.json`, the isolated `server-session.jsonl`, keyboard recipe,
wire transcripts, screen and hardware snapshots. The stock theme art remained
unchanged. Device/cursor replies came from the DOS program (`ESC[?1;2c` and
`ESC[1;1R`); the bridge handled only modem/Telnet negotiation. These checks cover
login and the named menu paths, with the same transfer/editor/door limitations
as the earlier run.

A separate serial-configuration regression used **COM2, 19200, 8N1, HARD** with
longer login/art pauses. It passed in 81.402 seconds on the same executable.
Authoritative session `4xUL4V5X0BB` traversed main → messages → main → files;
all six harness checks passed, including exact restoration of COM2 UART,
interrupt vector and PIC state. Evidence is in
`build/bbs-lab/results/enigma/com2-hardware/`, including session/menu JSON and
the full keyboard recipe. DOSBox-X nullmodem holds CTS ready: this verifies the
selected port/rate and hardware-flow code path under ready CTS, without claiming
physical handshake stalls or timing behavior.

## Negotiation and capability evidence

Actual server negotiation requested terminal type, NAWS and NEW_ENVIRON,
with ECHO/SGA/BINARY options. The modem model answered `ANSI-BBS` and80x25,
refused NEW_ENVIRON, and the server selected CP437. Actual DOS capture includes
server `ESC[0c` and `ESC[6n`; the executable replied `ESC[?62;2c` and
`ESC[1;1R` in the initial run. Font/CTerm/UTF8 detection depends on those replies.
Private cursor visibility and other theme commands are also present in art.

An independent TCP baseline is available:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma.py probe
```

This baseline negotiates Telnet, logs in and drives the stock menus. Its
headless fixed-home CPR response is a declared baseline limitation; it can
cause the BBS to infer SyncTERM font support and **is not a DOS capability
test**. Actual DOS captures are the authority for compatibility conclusions.
Probes save received bytes, sent bytes, staged output, queries and menu logs
under `build/bbs-lab/enigma/probe/`.

Remaining scope includes file transfers, full-screen editors, doors, advanced
fonts/UTF8/mouse protocols, all control/emulation families and physical Wi-Fi
modem firmware. A successful login/menu run does not establish these features.

## PROGRAM/reset checkpoint

The source-only terminal `7b9ca14b` is tested with COM2/19200/8N1/HARD.
The `program-reset-network-casefix` retry completes Login → Main → Messages →
Main → Files, including Down/Up in the login matrix. It sends the configured
uppercase `N` at the newscan prompt. The earlier `program-reset-network` run
logged in but entered newscan and reached Main too late for the scheduled menu
keys. That failed timed workflow is retained; this retry does not establish
that uppercase alone explains every timing difference.

Keep full-screen editor results separate. The unchanged immediate modem bridge
still exposes split escape-sequence handling; correct DOS wire bytes alone do
not make editing pass. No stock server decoder, theme or modem coalescing policy
was patched for these tests. Physical RS-232 Wi-Fi hardware remains untested.
