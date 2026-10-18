# Interactive terminal milestone

`./tools/build terminal` links `build/terminal/TERMINAL.EXE` from maintained and
recovered source. The build reads no original executable, private configuration,
installation, or disassembler database. Its manifest records each source hash,
executable hash and DS/SS group size.

```
TERMINAL [COM1..COM4] [baud] [8N1] [NONE|SOFT|HARD]
```

Options may appear in any order, once per category. Defaults are COM1, 38400,
8N1 and no flow control. Baud choices are 300, 1200, 2400, 4800, 9600,
19200, 38400, 57600 and 115200. Line formats support 7/8 data bits, N/O/E/M/S parity,
and 1/2 stop bits. `/?` prints usage. Unsupported options fail before hardware
access; only standard BIOS-listed COM bases are accepted.
The source-owned terminal defaults select the proved original ANSI profile6.
See [profile and form-feed evidence](../lab/bbs/synchronet.md).

`src/terminal/main.asm` owns the live entry, hardware lifecycle and loop.
`transport.asm` replaces fixture byte providers with the recovered UART and
BIOS keyboard modules. A foreground 1024-byte TX ring bounds output without
blocking on CTS/XOFF/transmitter stalls. The parser's receive callback continues
servicing keyboard, flow and output while awaiting a fragmented sequence;
36 BIOS ticks bound each wait. Alt-X sets a quit latch, unwinds arbitrary parser
frames and restores saved hardware and vectors. RX/TX overflow and unsupported
services return explicit DOS errors rather than silently losing data.

ASCII and raw CP437 bytes are displayed through the recovered renderer. The
four arrow keys use the recovered key-map/DECCKM path. Other extended/function
keys and full persistent keyboard profiles remain open. ANSI replies originate
in the DOS reporting engine. Specialized mode/font/control services remain
explicit boundaries. The program presently has no status/menu UI, dialing
manager, automatic modem setup, carrier-loss workflow, transfers, scripts or
Host mode. Full PRM startup integration remains open.

## Validation

`./tools/build test-terminal` combines these checks:

* Actual linked transport instructions under a modeled UART/BIOS exercise
  binary RX/unread, full-capacity TX ring wrap/overflow, CTS/XON/XOFF, key
  acquisition/mapping, caller-cleanup conventions, timeout wrap and Alt-X.
* Command-tail replay checks 133 inputs, all serial/flow combinations and
  rejection without partial state mutation.
* Recovered FF, SOH, VT and CAN controls have synthetic instruction-level tests,
  including ANSI erase/home, VT220 differences, mode-dependent branches and
  explicit failures for dependencies that remain unrecovered. Captured BBS
  streams are optional additional inputs, not public test dependencies.
* DOSBox-X drives a private synthetic BBS peer through real emulated UART,
  keyboard and BIOS video. Four cases verify fragmented ANSI/SGR/TAB rendering,
  cursor/device reports, both DECCKM modes, paused TX, partial escape cancellation
  and unsupported-operation cleanup. An independent generated DOS COM sampler
  compares IRQ08..0f/1c vectors, UART registers and PIC mask before/after, and
  captures actual B800 text memory. Product code has no test/capture switch.

Artifacts stay under ignored `build/terminal-tests/`. Modern BBS tests use the
same executable and sampler; see [the BBS lab](../lab/bbs/README.md). These results
establish an emulated interactive milestone. They do not close the complete
application inventory or establish physical RS-232/modem compatibility.
