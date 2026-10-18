# PCPlus DOS reconstruction

An incremental source reconstruction of ProComm Plus 2.01, focused first on
serial communication, ANSI terminal handling and BBS compatibility.
The complete task list and current work are tracked in [PLAN.md](PLAN.md).

**This is not yet a complete PCPlus source rebuild.** Current outputs:

| Output | Inputs | Current purpose |
| --- | --- | --- |
| `build/standalone/SERIAL.EXE` | Maintained assembly source only | Independently linked DOS diagnostic exercising the recovered UART module |
| `build/ansi/PARSER.EXE` | Maintained assembly source only | Independently linked parameter-reader diagnostic with bounds checks |
| `build/keyboard/KEYBOARD.EXE` | Maintained assembly source only | Recovered BIOS keyboard acquisition/normalization diagnostic |
| `build/csi/CSI.EXE` | Maintained assembly source only | Combined ESC, parameter, CSI, attribute and cursor self-check |
| `build/{escape,attributes,screen,text,reports,erase}/` | Maintained assembly source only | Separate DOS diagnostics for each recovered component |
| `build/{scroll,modes,render,cursor-shape}/` | Maintained assembly source only | Scroll, mode, character-rendering and BIOS cursor-style diagnostics |
| `reconstruction/dist/tech-net-candidate/PCPLUS.EXE` | Recovered source plus a locally supplied original executable | Full application with the historical CSI-q lockup fix |

Original executables, dialing/configuration files, disk images, downloaded
support archives and generated disassembler databases are excluded from Git.
No original executable is required to build the standalone diagnostic.

## Build and run in DOS

Requires Nix with flakes; the wrapper enables its required experimental features.
The flake pins NASM, Open Watcom, DOSBox-X, REA, Ghidra, Java and Python tooling.
The current development host is x86_64 Linux. Its first toolchain build can take
some time, particularly Open Watcom.

```sh
./tools/build
```

Copy `build/standalone/SERIAL.EXE` to DOS and run:

```text
SERIAL       COM1 / IRQ4 / 38400 baud / 8N1, flow control off
SERIAL S     Same settings with XON/XOFF
SERIAL H     Same settings with RTS/CTS
```

It echoes incoming serial bytes; **Escape on the local keyboard exits**.
This is a diagnostic, not a terminal UI. It saves/restores the IRQ vector and
UART state. Port selection, additional UART types and physical-hardware
validation remain work in progress. Do not use it inside another serial program.

Run the bounded, headless DOSBox-X integration suite:

```sh
./tools/build test
```

The test first replays the linked driver with controlled UART/PIC/DOS state,
including overflow, flow-control watermarks, CTS/transmitter stalls, timeouts and
hardware restoration. It then sends binary data across the 4096-byte receive-ring
boundary in DOSBox-X, checks XON/XOFF transmit pause/resume and checks DOS exit,
IRQ restoration and ring invariants. Use `./tools/build test-driver` for replay only. Emulator results do not establish physical modem/BBS compatibility.
Test artifacts and exact executable hashes are recorded under `build/serial-tests`.

The build also produces `build/ansi/PARSER.EXE`, which runs self-checks for the
linked parameter reader when started in DOS. Run its replay and DOS tests with:

```sh
./tools/build test-parser
```

Original-vs-maintained parser comparison is optional and requires local originals:
`./tools/build test-parser-compat`. See `docs/ANSI.md` for exact scope and fixes.

The keyboard unit has its own source-only DOS diagnostic and injected-key tests:

```sh
./tools/build test-keyboard
```

It covers acquisition and normalization, not terminal-specific escape-sequence
mapping. See `docs/KEYBOARD.md`. The full application acceptance inventory is
tracked in `docs/FEATURES.md`, including non-terminal features and dependencies.

The combined ANSI path and separate screen/reporting components build and test
through `./tools/build test-csi`, `test-screen`, `test-attributes`, `test-text`,
`test-erase`, `test-reports`, `test-cursor_state` and `test-escape`. The default `test` target includes
these diagnostics. See [docs/CSI.md](docs/CSI.md) for integration scope and gaps.
Additional targets `test-scroll`, `test-modes`, `test-render`, `test-cursor_shape`
and `test-terminal-services` verify real scrolling, terminal modes, ordinary
character output, cursor visibility/style and key-map/tab/reset helpers. These
are source-built components; a complete interactive application remains open.
`./tools/build test-input_dispatch test-input-relocation` verifies continuous
text/ESC/CR/LF/TAB/BS through the recovered input, renderer and history paths.
Selected controls and ANSI profiles are implemented; this diagnostic uses a
memory byte provider. See [docs/INPUT_DISPATCH.md](docs/INPUT_DISPATCH.md).
`./tools/build test-config` verifies a partial lossless host codec for proved PRM
settings. It preserves unknown bytes and uses synthetic data; DOS configuration
loading, complete defaults and the full settings UI remain work in progress.
See [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Full-application compatibility build

To use this optional path, supply your own original PCPlus 2.01 executable with
SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`
at `analysis/pcplus-originals/PCPLUS-main-2.01.EXE`. For full-application tests,
place your supporting installation files, including ASPCOMP.EXE, in
`analysis/pcplus-install`. These locations are ignored by Git.

```sh
./tools/dev --command python3 analysis/inspect_pcplus.py
./tools/build compat
./tools/build test-compat
./tools/build test-modem
./tools/pcplus-run
```

The compatibility build verifies and inserts 10,129 recovered source bytes (including 130 startup pointer-table bytes) into the
original container, then replaces exactly two bytes using the archived Datastorm
TECH_NET recipe. Other maintained parser/input bounds fixes apply to source-built
diagnostics; this compatibility container still changes only those two bytes. It retains the original program's other code and resources.
The launcher uses a separate private installation under `reconstruction/lab`.
Type `ATDThost:port` to dial its emulated Hayes modem; Alt-X exits. Its generated
startup script and executable are refreshed on launch.

## Source and evidence

- `reconstruction/uart/core.asm`: recovered resident UART block, with exact
  baseline and relocatable OMF modes sharing the same instruction source.
- `reconstruction/uart/layout.inc`: original DS addresses versus linkable symbols.
- `src/uart/api.asm`: bounded transmit and foreground flow-control service.
- `reconstruction/ansi/parameters.asm`: exact original recovery plus maintained OMF mode with bounds checks.
- `reconstruction/ansi/transition.asm`: shared parameter-to-dispatch state transition.
- `standalone/`: newly written DOS host, state allocation, host services and tests.
- `docs/UART.md`: interfaces, observed behavior, evidence and known limitations.
- `analysis/`: REA MCP client, binary/overlay analysis scripts and evaluation.
- `nix/`: pinned toolchain, global REA package and compiler check.

Generated `.analysis.exe` files are synthetic disassembler inputs. Never run or
deploy them. Decompiled pseudocode is evidence, not recovered original source.

## Next milestones

1. Extend driver validation to physical UARTs and the intended Wi-Fi modem;
   controlled watermark, overflow and stall regressions now pass.
2. Recover the terminal parser and keyboard module behind explicit interfaces.
3. Reconstruct application startup, settings, UI, dialing, transfers and scripting.
4. Link the complete application from source, removing the original executable
   from every build input.

PCPlus and ProComm Plus are names of the original product. This repository is an
independent reconstruction effort; original program rights are not reassigned.
