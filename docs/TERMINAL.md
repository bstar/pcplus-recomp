# Interactive terminal milestone

`./tools/build terminal` links `build/terminal/TERMINAL.EXE` from maintained and
recovered source. The build reads no original executable, private configuration,
installation, or disassembler database. Its manifest records each source hash,
executable hash and DS/SS group size.

```
TERMINAL [@FILE.PRM] [COM1..COM4] [baud] [8N1] [NONE|SOFT|HARD]
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
Host mode. The explicit PRM option imports the validated serial, flow, ANSI/VT220,
attribute, wrap and scrolling subset; complete PRM/application startup remains open.

## Validation

`./tools/build test-terminal` combines these checks:

* Actual linked transport instructions under a modeled UART/BIOS exercise
  binary RX/unread, full-capacity TX ring wrap/overflow, CTS/XON/XOFF, key
  acquisition/mapping, caller-cleanup conventions, timeout wrap and Alt-X.
* Command-tail replay checks 175 inputs, all serial/flow combinations and
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

* Configuration tests exercise 115 CPU cases and 15 actual DOS cases, including
  explicit-file reads, CLI precedence, simultaneous flow flags, profile-derived
  state, rejected malformed files, unchanged files and hardware restoration.

Artifacts stay under ignored `build/terminal-tests/`. Modern BBS tests use the
same executable and sampler; see [the BBS lab](../lab/bbs/README.md). These results
establish an emulated interactive milestone. They do not close the complete
application inventory or establish physical RS-232/modem compatibility.

## Explicit PRM startup

```text
TERMINAL @PCPLUS.PRM
TERMINAL @PCPLUS.PRM COM1 38400 SOFT
```

The file must be exactly 1,264 bytes. Serial CLI categories override the imported
port, baud, line or complete flow pair. The selected PRM subset is validated even
when a CLI category overrides it. Config failures return DOS errorlevel7 before
UART access; help and invalid CLI syntax do not read the file. The importer does
not save, create defaults or search for an installed configuration. It accepts
profiles4 (VT220) and6 (ANSI), standard COM1..4 bindings and independent boolean
flow flags, including both enabled. Other legacy bytes remain opaque.

See [startup evidence and boundaries](STARTUP_CONFIGURATION.md).
