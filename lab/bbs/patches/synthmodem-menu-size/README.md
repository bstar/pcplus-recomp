# Owned pre-session terminal-size probe

This GPL-2.0-or-later patch extends SynthModem's TelnetProxy, attributed to
[SynthModem](https://github.com/synexo/synthmodem). It is a staged bridge candidate
for the PCPlus reconstruction, maintained by bstar / LoSs oF CoNtRoL. The runner
requires the exact source/COPYING hashes in `check.py`, copies them into ignored
build storage and applies the patch there with zero fuzz. The original COPYING
accompanies each staged tree. No installed source, config or service is changed.
This does not rebrand SynthModem or claim that its modem/DSP code was recovered
from PCPlus.

The new optional `telnet.terminalSizeProbeTimeoutMs` is absent/off by default.
An integer1..10000 enables one CSI18t query after selection of an allowed valid
destination, before opening TCP. The absolute timer and owner precede output,
including an inline terminal response. Only this state interprets the expected
CSI8;rows;columns t response. Positive16-bit dimensions seed the unchanged
TelnetCodec constructor. NAWS is advertised only when the peer enables it;
this is not an application acknowledgment that its layout has resized.

Other typing is retained, up to1024 bytes, and sent once upon connection. One
menu CRLF is consumed, including across receive chunks. Cancellation, failed
connection and return to the menu discard pending typing and accepted dimensions;
a fresh connection probes again. Default behavior with no option/zero is compared
against the pinned stock proxy. TCP identity checks, detach-before-destroy,
connection-deadline identity checks and output-callback cancellation guards
prevent stale events from reopening/closing another session.

Timeout, malformed reserved response, invalid nonzero configuration or queue
overflow closes the modem session, rather than continuing with guessed dimensions.
No TCP is opened on a failed probe. A timed-out query cannot be retried in the
same call, which avoids accidentally accepting its late response as a new query.
There is no wire nonce/authentication: a forged valid response is indistinguishable
from a terminal response. The collector must never be applied to PROXYING data.
Neither BBS output nor upload/download input is scanned for size-report lookalikes.
Existing input-framer/escape options remain independent; binary tests disable both.

`WindowSizeReply.js` is the bounded collector. `proxy.patch` integrates ownership,
queueing and lifecycle in the actual proxy. `check.test.js` runs the actual patched
source with declared IO/config/clock boundaries, and a real loopback TCP test.
The independent `dos-peer.js` also runs the staged proxy with real timers/sockets,
a fake Hayes boundary and an independent Telnet record parser. It never fabricates
a response on behalf of the DOS terminal. The Python DOS runner checks the real
8086 UART reply, exact NAWS, ordinary CPR/DA/keyboard, video, configuration and
sampled interrupt/UART/PIC restoration.

```sh
./tools/dev --command python lab/bbs/patches/synthmodem-menu-size/check.py \
  --runtime /path/to/pinned/synthmodem --output build/NEW-menu-size
./tools/dev --command python standalone/test_menu_size_bridge_dos.py \
  --stage build/NEW-menu-size --terminal build/ORDINARY/TERMINAL.EXE \
  --output build/NEW-menu-size-dos
```

The DOS input must have `--window-size-report`; this experiment does not enable
normal display commands/startup preference application, live online resize,
SIP/audio or analog acceptance, or update the physical machine. The component
coverage does not establish Enigma/Synchronet layout, file-transfer acceptance
or complete PCPlus parity. See `docs/MENU_SIZE_BRIDGE.md` for the bound receipt
and next integration gates.
