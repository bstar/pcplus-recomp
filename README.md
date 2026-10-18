# PCPlus DOS reconstruction

An incremental source reconstruction of ProComm Plus 2.01, focused first on
serial communication, ANSI terminal handling and BBS compatibility.
The complete task list and current work are tracked in [PLAN.md](PLAN.md).

**This is not yet a complete PCPlus source rebuild.** There are two outputs:

| Output | Inputs | Current purpose |
| --- | --- | --- |
| `build/standalone/SERIAL.EXE` | Maintained assembly source only | Independently linked DOS diagnostic exercising the recovered UART module |
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

The compatibility build verifies and inserts 1,320 serial/parser source bytes into the
original container, then replaces exactly two bytes using the archived Datastorm
TECH_NET recipe. It retains the original program's other code and resources.
The launcher uses a separate private installation under `reconstruction/lab`.
Type `ATDThost:port` to dial its emulated Hayes modem; Alt-X exits. Its generated
startup script and executable are refreshed on launch.

## Source and evidence

- `reconstruction/uart/core.asm`: recovered resident UART block, with exact
  baseline and relocatable OMF modes sharing the same instruction source.
- `reconstruction/uart/layout.inc`: original DS addresses versus linkable symbols.
- `src/uart/api.asm`: bounded transmit and foreground flow-control service.
- `reconstruction/ansi/parameters.asm`: 175-byte exact recovery of the ANSI parameter reader.
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
