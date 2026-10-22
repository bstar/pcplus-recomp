# Live DOS modem connection controller

The maintained terminal now initializes and dials an explicitly selected target
through the actual recovered UART. It expands configured caret commands with
the recovered4934 routine, feeds received modem bytes to the recovered4a1d
matcher, and applies the proved response/autobaud classification. The recovered
overlay5 dial-attempt object remains unlinked: its modal UI, retry directory and
other application services are separate unfinished work. This controller is
new source with deliberate bounded behavior, not an assertion that every
original dialing feature has been reconstructed.

```text
TERMINAL @PCPLUS.PRM /D:bbs.example:23
TERMINAL @PCPLUS.PRM /D:bbs.example:23 COM2 19200 HARD
```

The file must be an externally identified2.01 PRM image. It is loaded once into
staging; the serial/display and modem subsets both validate before either plan
commits or any UART access occurs. Invalid CLI syntax returns errorlevel1;
missing/invalid required configuration returns7. The program never generates
original modem defaults, modifies the file, reads a dialing directory or searches
for an installed profile. Without `/D`, the existing terminal-only import stays
available and unused modem fields are not decoded. Target text preserves case,
is limited to63 bytes and accepts a documented bounded network-target alphabet;
spaces, caret escapes, pause markers and command separators are rejected by
the CLI parser. A configured pause byte that happens to occur in a target still
has its original sender meaning; choose a modem profile suitable for that target.

## Interaction and ownership

| Key | Behavior with a configured target |
| --- | --- |
| Escape during initialization/dial/wait | Cancel the attempt; do not send the Escape key as ordinary BBS input. |
| Alt-H online | Send the configured hang-up command, then configured DTR cleanup. |
| Alt-D after cleanup | Repeat the explicitly selected target. No automatic directory cycling is implied. |
| Alt-X | Request bounded cancellation and exit after cleanup. A second Alt-X exits immediately if a stalled BIOS clock or modem delays cleanup. |

Normal keyboard data and ANSI reports use the existing bounded TX ring only in
raw/online states. Connection commands go directly through `uart_try_write`.
Starting an attempt discards queued old-session output. Active modem states own
keyboard/RX control traffic; a partial ANSI reader yields rather than consuming
modem responses. Once a response matches during final command pacing, the main
loop leaves subsequent data in the actual UART RX ring until online mode begins.
Same-write CONNECT plus ANSI banner is tested in DOS, including the first
display character and actual DOS DA/CPR replies.

Small bottom-row notices use the recovered screen snapshot and flow-message
services with zero duration. They do not enter the original blocking timed
window path. Saved cells are restored before online data renders. This is a
connection notice, not the complete PCPlus menu/status-window interface.

## States and deadlines

`src/terminal/connection.asm` owns raw/idle0, initialization1, dial-send2,
response-wait5, online6, abort-send7, DTR-pulse8 and configured-hangup9, plus initialization reply/drain10.
Every foreground poll is bounded. The sender attempts at most one physical
byte; it advances only after the real UART accepts it. CTS, software XOFF and
THRE stalls leave the byte pending while keyboard/flow/deadline service continues.

The controller takes atomic full32-bit BIOS day-tick snapshots with the
caller's interrupt flag preserved. Delta calculation handles both low-word
rollover and the BIOS midnight modulus `0018:00b0`. A positive timeout uses
`ceil(seconds *1193182 /65536)` ticks and a32-bit elapsed counter. The deadline
covers initialization and dialing as well as response waiting. This differs
deliberately from the original modal loops, whose command sends can block and
whose signed elapsed counters can wrap. Supported timeout is1..32767 seconds;
redial delay/cycle count and legacy pacing units are retained within0..32767.

Cancel tries the configured nonzero abort byte, allowing at most18 ticks for
flow stalls. If configured, it clears DTR for18 ticks and then restores the
saved DTR bit while preserving other current MCR bits. Successful configured
hang-up also follows that DTR policy. These are source-owned timing choices;
physical modem escape guards, firmware behavior and line timing are unproved.
The online controller notices DCD loss only after observing DCD asserted in
that session, clears pending output and returns to raw mode. BIOS-clock failure
cannot complete a timed cleanup; the explicit second Alt-X escape remains usable.

Status words distinguish online, response failure, timeout, cancellation,
hang-up, carrier loss and internal errors. Interactive dial failures return to
the terminal; they are not automatically DOS process failures. Normal Alt-X
still returns0. Unsupported terminal services and overflow retain their existing
explicit error exits and hardware restoration.

## Initialization result policy

[Configurable initialization waiting](MODEM_INITIALIZATION.md) adds `/I` seconds
per acknowledgement, with zero/omitted preserving legacy no-wait behavior.
Initialization ERROR returns response-failure status 2 with an Init failed notice;
timeout returns status 3. Both prevent ATD and use the existing bounded cleanup.
Each initialization send retains the PRM send deadline, and successful initialization
resets the dial clock. Direct/carrier skip policies retain precedence. The
historical baseline and current independent component receipt remain distinct;
current-product BBS/audio and physical modem validation are outstanding.

## Timing and result compatibility

The live sender intentionally uses one BIOS tick between ordinary bytes and
ten ticks for the configured pause byte. Sentinelff sends NUL without ordinary
pacing; pause matching has priority over sentinel handling. Expanded zero ends
each original command segment. The configured prefix, target and suffix are
expanded/assembled before UART side effects; the bounded target plus PRM field
limits fit the owned129-byte buffers. Legacy calibrated delay units remain
stored and validated, but are **not** silently reinterpreted as ticks or
milliseconds. The separately recovered original sender/delays and their real
UART diagnostic are documented in [MODEM_SEND.md](MODEM_SEND.md).

Matching preserves original case sensitivity, first-completion and partial
prefix behavior. Generic CONNECT can win before a longer speed-specific label;
autobaud can therefore select300 when slot0 matches. Slots0..6 select300..38400,
while7..10 indicate failure. The current baud index updates after autobaud so a
later attempt compares against the actual active rate. Modern57600/115200 result
policies, line-framed/longest matching and firmware-specific escapes remain
separate compatibility work; these are not fabricated by the test modem.

## Validation and remaining scope

`./tools/build test-terminal` includes CPU execution of the actual linked
decoder/controller/sender/UART/keyboard code plus DOS filesystem, IRQ, video and
modem-peer tests. Independent combined-startup tests verify one read, unchanged
plans on error and all16 CLI override combinations. Near-output extents and
overlap are rejected by the public combined C interface.

`standalone/test_connection_dos.py` exercises immediate CONNECT+banner,
BUSY, silence timeout, configured hang-up and explicit redial. It captures
physical emulated serial bytes, video, unchanged synthetic PRM and independent
before/after42-byte UART/PIC/vector samples. Real local Synchronet, ENiGMA½ and
Mystic sessions additionally verify automatic ATZ/ATD output followed by login
and menu navigation. `--dial-fixture` in the lab supplies synthetic configuration;
no private modem commands or directory data enter public tests.

Physical UART/modem testing, automatic selected-number redial cycles,
directory/settings UI, complete initialization/carrier policy, configurable
modern pacing, transfers, scripts and Host mode remain open. See the full
[plan](../PLAN.md); passing these tests does not complete PCPlus reconstruction.

The terminal also supports [read-only directory selection](DIRECTORY_LIVE.md):
selected records override PRM serial/profile settings, support MODEM or DIRECT,
and choose literal/legacy target interpretation explicitly. Original automatic
selection cycles and the complete directory/settings editor remain open.
