# Synchronet loopback laboratory

This laboratory runs the actual official Synchronet server at `127.0.0.1:23231`.
The account `LABUSER` / `LABPASS42` and all profile fields are synthetic. The
server disables FTP, mail, web, services and event processing. Keep all tests on
loopback and all downloaded server data under ignored `build/bbs-lab/`.

The pinned bootstrap is **3.22a development snapshot**, commit
`9de2c48d0265b07e1a8406d8a55d31df4fad7ee8`, built with GCC14.2.0. It is not
stable3.21e. `synchronet.py` records exact official development/run/source archive
SHA256 digests and refuses changed rolling archives. Source and runtime archives
are retained locally; the actual executable is the matching official binary,
not a claim that this repository rebuilt Synchronet. Native libraries come from
`nix#bbs`. This avoids Docker daemon permissions and system package changes.

Official references: [Unix installation](https://wiki.synchro.net/install:nix),
[prerequisites](https://wiki.synchro.net/install:nix:prerequisites),
[server configuration](https://wiki.synchro.net/config:sbbs.ini),
[downloads](https://www.synchro.net/download.xjs) and
[official source](https://github.com/SynchronetBBS/sbbs).

```sh
./tools/bbs-dev --command python3 lab/bbs/synchronet.py setup
./tools/bbs-dev --command python3 lab/bbs/synchronet.py serve
# Separate terminal, one LABUSER session at a time:
./tools/bbs-dev --command python3 lab/bbs/synchronet.py probe
```

Setup fills required synthetic profile fields so first-login enrollment does not
obscure protocol testing. `serve` stays in the foreground; stop it with Ctrl-C.
The reference Python peer is a limited Telnet client. It advertises ANSI and
80x25, and answers size-detection CPR with a declared fixed25;80 response. It is
not the DOS terminal and does not establish DOS compatibility. Captures preserve
both complete wire directions, Telnet events, filtered full transcript and ANSI
sequence inventory under `build/bbs-lab/synchronet/captures/`.

Observed login/navigation is `Login:` -> `LABUSER` + CR -> `Password:` ->
`LABPASS42` + CR -> stock ANSI welcome artwork -> `[Hit a key]` -> Space ->
Synchronet BullsEye! bulletin menu (`Enter number of bulletin or [Quit]:`).
Bulletin1 displays board statistics. `Q` leaves that menu. Reply `n` + CR to
`Search all groups for new messages?`, then Space at `[Hit a key]` reaches the
stock main menu. The reference probe asserts each prompt and the bulletin
statistics/main menu content; it does not send message or mail commands. Do not post messages, send mail or invoke external programs for this
read-only compatibility check.

Initial server negotiation requests Telnet ECHO, SGA, terminal type, terminal
speed, location, NAWS and NEW-ENVIRON. It emits primary device attributes and
cursor-position queries, cursor save/restore, large cursor movement, SGR,
erase/home, optional SyncTERM APC capability query, `CSI ! _` and a UTF-8 BOM
probe. Unsupported optional probes must be distinguished from fatal renderer
boundaries. The first actual DOS run failed on ASCII FF, after199 serial input
bytes; the recovered FF path fixed that concrete abort. Later actual DOS login
and navigation runs reached the stock main menu and restored UART/IRQ/PIC state.
This proves those captured local paths only. Optional SyncTERM facilities,
Unicode, file transfer, complete menus and physical modem behavior remain
separate checks.

## Original profile identity and formfeed evidence

Original resident display-name lookup at `0x130a8` indexes DS`299c + 2*id`.
Original data table labels ID4 **VT220**, ID6 **ANSI**, ID7 **IBM PC**. The
startup routine at resident`20a4` initializes the same profile gating flags for
4 and6 except DS`8ff6`, which is0 forVT220 and1 forANSI. DS`d122` and DS`8fe8`
are1 for both; DS`8ff8` and the other family gates are0. Existing analyst names
`attributes_color_mode`/`attributes_monochrome` are observed-use aliases, not
literal descriptions of video hardware color/mono modes.

Recovered resident`0fb0..1001` (81 baseline bytes) implements FF differently by
profile: VT220's default follows actual linefeed; ANSI/IBM PC dispatch through
resident trampoline`ba4b` to overlay12`da12..da45` (51 baseline bytes). That
helper erases the full physical window using current attribute when DS`8ff6`
is set, otherwise the erase attribute, then homes to origin row/column0. It
calls recovered rectangle erase`2530` and cursor update`1bbe`; it is not a no-op
renderer. REA evidence IDs are
`ev_d82dc1948d45d5e8c06dc39233f4f83717ed70b5dcbf83e12e4bb07fbfcdd576` and
`ev_69017b522a437c1c0ff6ec2b312f16bcce17c94eacc14171434df7bf025222d7`.
The flat helper matches51 original bytes exactly; local originals are optional
compatibility inputs and are not shipped or read by the source build.

```sh
./tools/dev --command python3 lab/bbs/check_formfeed.py
# Optional, explicitly selected local capture:
./tools/dev --command python3 lab/bbs/check_formfeed.py --wire build/bbs-lab/results/synchronet/probe/serial-sent.bin
```

Mandatory synthetic tests use actual linked receive dispatch/BIOS erase/cursor
instructions and a declared BIOS CPU model. They cover FF family branches,
attribute normalization, ANSI/IBM PC erase attributes and origin rows, VT220 vs
ANSI device attributes, status/position reports and DECCKM key binding changes.
VT220 replies `ESC[?62;2c`; ANSI replies `ESC[?1;2c`. Both preserve actual
DECCKM transitions. These specific profile gates do not establish recovery of
the full original profile initialization/UI.

## Actual DOS navigation check

The final ANSI-profile executable SHA256
`aca82619ad87a7e9aa259c4716a75eebb9483c204cbd0da17ab8c8b8a7d77029`
completed the following actual DOSBox-X run in43.204seconds. The bridge passed
BBS queries unchanged; DOS generated `ESC[?1;2c` and cursor replies. Wire output
shows `T` opening the file section, `Q` returning to Main, `R` requesting the
empty Local Notices message area, and the final `Q` dismissing its pause. The
server replied that no messages had been posted. Actual B800 video ends at the
main menu; IRQ/UART/PIC snapshots match before and after. There were no
unrecognized-command responses. This exercises menu interaction without
transferring files or posting content.

```sh
./tools/dev --command python3 lab/bbs/test_dos.py synchronet --port 23231 \
  --label ansi-navigation \
  --keys 'p7000 L A B U S E R enter p2000 L A B P A S S 4 2 enter p8000 space p3000 Q enter p5000 space p3000 T p4000 Q p3000 R p3000 Q' \
  --wait 4 --timeout 75
./tools/bbs-dev --command python3 lab/bbs/synchronet.py check-dos --label ansi-navigation
```

The checker asserts eight conditions against real retained serial/display
bytes, run metadata and final DOS video, writing `navigation-checks.json`.
The timed keyboard recipe assumes the configured synthetic board; slow hosts
may require longer waits. Captures and account/server logs are local ignored
evidence. `provenance` re-verifies local archive digests and records server
version without rewriting runtime configuration.
