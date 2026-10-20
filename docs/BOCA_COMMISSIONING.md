# Boca / SPA2102 commissioning worksheet

Status: adapter ordered; no physical test performed. This worksheet implements
the [integration plan](ANALOG_MODEM_INTEGRATION.md) without changing the ongoing
source-built PCPlus objective. Fill a separate copy per run in ignored local
storage. Publish only redacted settings and synthetic/public test evidence.

## Identify and freeze the setup

Record the following before choosing a modem initialization profile:

| Item | Value to record |
| --- | --- |
| Boca | Board/model labels, chipset, firmware identification and matching manual. |
| ISA/serial | Jumpers, COM, I/O base, IRQ, UART/FIFO type; identify any resource conflict. |
| Modem behavior | Documented fixed-DTE, RTS/CTS, carrier-following DCD, DTR hangup, speaker and modulation commands. Unsupported commands remain unset. |
| PCPlus | Source revision, executable/profile hashes, 8N1, DTE rate, flow settings, autobaud setting and connection timeout. |
| Adapter | Firmware version, saved configuration, PHONE 1 routing, INTERNET/LAN address, SIP destination, codec and RTP settings. Keep existing firmware. |
| Workstation | Wired/Wi-Fi topology, Linux version, Node/QEMU versions, SynthModem revision, patches, backend, runtime-image hashes and bind addresses. |
| BBS | Software/version, hostname/port and test account; keep credentials out of public evidence. |

Use standard COM/base/IRQ pairs currently supported by PCPlus. If the board
requires another pair, add explicit source/config support before testing it.
Select a conservative documented DTE speed independently of line speed; begin
with autobaud disabled. Set PCPlus and modem flow control consistently. Do not
copy bridge AT_INIT commands to the Boca or assume AT+MS, &K, &C or &D support.
Use the modem's documented speaker controls to retain audible training.

Keep SIP/Telnet on Linux. Use official distribution packages first, then
Nixpkgs; never AUR/yay/paru. The repository's Nix lab is available through
`./tools/modem-dev --command`; it does not install or start a production bridge.

## Connection test

1. Save the adapter configuration. Connect Boca RJ11 to PHONE 1, and the
   adapter INTERNET port and workstation to the same router/switch.
2. Configure local SIP routing and audio from the pinned upstream baseline
   described in the integration plan. Record changes and actual settings.
3. Select a documented numeric local dial destination that the adapter routes
   to SynthModem. PCPlus originates that telephone call through the Boca.
4. Record initialization responses, audible training, elapsed time, CONNECT
   result text, DCD transition, backend/protocol and negotiated line rate.
   A SIP answer alone is not a modem connection.
5. Wait for `CONNECT>` inside PCPlus, then type the BBS hostname or hostname:port.
   The hostname is online terminal data, never a Boca ATDT telephone argument.
6. Confirm login and the first banner bytes. Preserve errors and logs if training
   fails; do not classify silence alone as proof that the Boca lacks V.8.

Begin with a documented common low-speed protocol. Native fallback's legacy
chain is not a demonstrated V.32bis path. Test 14400 separately only after
establishing backend and modem support; success at 1200/2400 does not prove it.

## Separate acceptance runs

| Run | Required observations |
| --- | --- |
| Display/interaction | CP437 including box drawing, ANSI color/cursor/scroll, DA/CPR, Synchronet and ENiGMA menus/editors; record escape-sequence timing and negotiation artifacts. |
| Sustained data | Known duplex byte patterns/counts/hashes, long idle, CTS stalls and receive load; check overrun/overflow counters and distinguish corruption from data loss. |
| Disconnect/reconnect | Local hangup, DTR drop, remote Telnet close, SIP/bridge failure and real carrier loss; verify repeated dialing and DOS cleanup. Telnet returning to CONNECT> may leave analog carrier/DCD up. |
| Transfers | Upload/download, empty and all-byte files, files over 64 KiB, supported X/Y/ZMODEM, exact hashes, cancel/retry/carrier-loss behavior and terminal recovery. |

For every run record pass/fail, duration, exact input identities, expected and
observed results, and unresolved failures. Preserve distinct software-only and
physical results. Never infer a hardware pass from an emulator, synthetic modem,
loopback transport or upstream report.
