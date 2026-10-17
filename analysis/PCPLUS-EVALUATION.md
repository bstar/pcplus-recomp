# PCPlus reassessment and reconstruction status

The REA/Ghidra decompilation route works. A controlled incremental reconstruction
is practical; a complete source rebuild is still unfinished. The earlier stop
for supposedly missing Ghidra/Java was unnecessary: an existing installation was
present but invisible to the connected MCP process. Analysis now uses a pinned
Nix environment and an actual REA 6.5.0 stdio MCP connection.

## Artifacts and measured coverage

| Work | Result | Evidence/artifact |
| --- | --- | --- |
| Preserve inputs | Three original executable variants plus a complete 32-file copy of the active install | `pcplus-originals/SHA256SUMS`, `pcplus-install/inventory.json` |
| Verify original MZ import | 4,608 header bytes, 53,456 initialized module bytes, 155,952 appended bytes; relocation and mapping checks passed | `pcplus-main/inspect_native_load_image.json`, Evidence `ev_e64adede842cb5581a5caa88c7267b5fe09e200a2aa6cbcc31d7beee9f04e6ab` |
| Resident decompilation | 515 pseudocode files and matching assembly exports | `pcplus-main/functions`, overview Evidence `ev_a333d7c28a07e193e7b0b27f687521d56f71c40c309349d54d7396301f170519` |
| Parse PLINK86 overlays | 31 code overlays and one startup-data overlay, every file boundary validated | `inspect_pcplus.py`, `pcplus-overlays/manifest.json` |
| Seed overlay analysis | 502/502 unique exported entrypoints discovered in their respective overlay contexts | `pcplus-overlay-anchored-summary.json` |
| Export overlay functions | 894 pseudocode functions plus assembly, zero failed tool operations | `pcplus-overlay-anchored-01` through `pcplus-overlay-anchored-31` |
| Reassemble serial code | UART block (466 instructions, 1,099 bytes) plus 46-byte receive timeout; 1,145 unique bytes rebuilt exactly | `../reconstruction/uart/core.asm`, `../reconstruction/uart/receive_timeout.asm`, candidate manifest |
| Compile a DOS program | Nix-built Open Watcom successfully compiled an MZ DOS compiler probe; flake checks passed | `../nix/flake.nix`, check `dos-compiler` |
| Build compatibility candidate | Two serial source units inserted into the original container; 214,016 bytes, exactly two changed bytes; eight handler cases passed | `../reconstruction/dist/tech-net-candidate/manifest.json` |
| Exercise full DOS application | Startup/compiler, UART terminal queries, CSI-q regression, keyboard and exit checks pass; raw serial and emulated Hayes/Telnet | `../reconstruction/lab/*/result.json`, `../reconstruction/dos_lab.py` |

Function counts are exports in specified analysis contexts, not a claim that
every original source function or type has been recovered. Known exported-entry
coverage is measured against the program's own 502 trampoline entries. All
native sessions created by the analysis clients were closed.

The complete install copy includes private dialing/configuration data. It is
kept locally for later testing and is not an input to the Nix package derivation.

## Version choice

Both 214,016-byte PCPlus 2.01 executables contain identical resident code and
identical code overlays. Their only differences are ten contiguous bytes in
startup data overlay 32. There is no different code patch level to choose
between these copies. The active install is a suitable reproducible baseline.
The older 1.1B binary is retained for reference, not selected for development.
No original PCPlus source project or original compiler/linker build files were
found in the inspected installation.

## A concrete terminal lockup and a tested candidate

The preserved [Datastorm support archive](https://aspectscripting.com/support.shtml)
contains `TECH_NET.DTP`, which describes keyboard lockups associated with
`ESC [ ; 4 q`. The original patch recipe is retained in
`archived-support/dp201/tech_net.dtp`; its source archive URL and hash are in
`archived-support/manifest.json`. Archives were extracted with Lhasa; their DOS
self-extractors and patching utility were not launched.

The actual original code agrees with the recipe. At file offset 96,067, bytes
`7d 03` enter a CSI-q payload-read path when at least two parameters are present.
With second parameter 4, that path makes 20 calls to the timed receive routine.
Each empty-buffer call can wait 36 BIOS clock changes, producing roughly 40
seconds of delayed interaction when the expected payload does not arrive.

`check_ansi_freeze.py` executes the original handler and receive routine in a
16-bit Unicorn CPU with controlled BIOS clock changes. The two-parameter
baseline makes 20 receive calls and advances 740 simulated BIOS ticks. The
historical two-NOP replacement makes no receive calls and reaches the handler
epilogue immediately. One-parameter q cases also return normally.

The same harness runs the original status and cursor-position query handler
through modeled UART input/output. Both baseline and candidate return
`ESC [ 0 n` for CSI 5n and `ESC [ 10 ; 20 R` for CSI 6n at the chosen cursor
position. PCPlus already implements those terminal responses; treating all
modern BBS detection failures as missing cursor-position support would be wrong.

The candidate is a partial source rebuild within the original executable container.
It reassembles 1,145 bytes of serial code and applies the historical fix; the
remaining program still comes from the preserved original:

- File: `../reconstruction/dist/tech-net-candidate/PCPLUS.EXE`
- SHA-256: `06708fec7663ad2122ca37947d45e88f4f5766ad70f99f40bac6340a15fa8a00`
- Changed file offsets: 96,067 and 96,068 only
- Source patch: `../reconstruction/patches/tech_net.asm`
- Build/test command, inside the Nix environment: `python3 reconstruction/build_compat.py`

The handler replay begins with parsed CSI state. A separate full-DOS harness
now tests the complete application through DOSBox-X's UART and keyboard. It
compiles an ASPECT startup script using the original ASPCOMP.EXE, starts PCPlus,
sends terminal queries through a loopback TCP peer, injects emulated keyboard
events and verifies return to DOS. The original stops replying after CSI-q and
recovers when the peer supplies its expected payload; the candidate replies
immediately. Both pass status/cursor queries and key translation.

| Executable | Transport | Configured baud | CPU cycles | Result |
| --- | --- | ---: | ---: | --- |
| Original 2.01 | Raw emulated serial | 9,600 | 6,000 | Expected lockup/recovery reproduced; other checks pass |
| Candidate | Raw emulated serial | 9,600 | 6,000 | Pass |
| Candidate | Raw emulated serial | 38,400 | 6,000 | Pass |
| Candidate | Raw emulated serial | 115,200 | 3,000 | Pass |
| Candidate | Hayes modem with Telnet filtering | 38,400 | 6,000 | Pass |

The modem case issues ATZ, ATNET1 and ATDT to the emulated modem, then checks
binary/echo/suppress-go-ahead negotiation and the same terminal/key behavior.
DOSBox-X consumes server WILL options without replying; the test checks its
supported DO responses. ASPECT PAUSE was found to delay terminal input handling
while the startup script runs, so the script ends before host-side tests begin.
The configured baud tests do not measure sustained throughput or physical UART
reliability. No physical Wi-Fi modem or public BBS was contacted. This is a
concrete fix for one known failure, not proof it matches the user's failure.
The candidate has not been installed on the card.

Run the interactive sandbox with `./tools/pcplus-run` from the project root.
It maintains a private install under `reconstruction/lab/interactive/drive`,
rebuilds the candidate, configures COM1/38,400/8N1/ANSI and enables the emulated
modem's Telnet filtering. Type `ATDThost:port` to connect; Alt-X exits. Incoming
modem listening is disabled. The launcher itself passed a bounded headless
startup/compile/exit test. `./tools/pcplus-test test` reproduces the original vs
candidate regression; `./tools/pcplus-test test-modem` exercises Hayes/Telnet.

The archive also contains keyboard, escape timing and UART-specific fixes.
`archived-support/patch-audit.json` compares their prescribed replacement bytes
against this baseline without applying them. The selected keyboard/timing/FIFO
replacement bytes are absent. One recipe uses unsupported audit commands and is
explicitly marked unknown. A blanket patch collection is not a sensible target:
several fixes deliberately change behavior for particular UARTs or CPU timing.

## Why pseudocode cannot simply be compiled

The original resident export includes 48 pseudocode functions containing
bad-instruction warnings. More subtly, Ghidra removes the BIOS timeout path in
function 0x15ca0 as unreachable: it does not model asynchronously changing BIOS
memory. Compiling that pseudocode literally would turn a finite receive wait
into an endless wait. The observed assembly retains the correct timer behavior.
That routine has now been hand-reconstructed and reassembled exactly.

The native code also relies on real-mode segment relationships: startup sets
DS equal to SS, and assembly helpers use that small-model invariant to access
stack arguments through BX. Overlay lifetime, volatile BIOS/UART state, calling
conventions, relocation records and fixed-address data need explicit recovery.
The synthetic overlay images expose those bytes for static analysis, but their
trampoline substitutions and entry anchors are analyst-created context, not
original runtime behavior. They must never be executed or deployed.

## Practical route to a maintained version

Continue reconstructing the serial driver, keyboard translation and VT/ANSI
parser in bounded units. Preserve the current memory/overlay layout while
reassembling original routines, attach captured serial streams and explicit
regressions to any behavior change, and expand the linked source build as
calling conventions and data structures are recovered. Open Watcom provides a
working DOS C compiler; it has not been established as the original compiler.

A full source rebuild and physical modem/public-BBS validation remain
open. The next diagnostic input is the exact modem model/firmware and a failing
BBS/key sequence, so the next change targets an observed incompatibility.

## Nix and global REA

`../nix/flake.lock` pins Nixpkgs, and the npm lock plus fixed-output hash pin
REA 6.5.0. The environment supplies Ghidra 12.1.2, JDK 21, Open Watcom V2,
NASM, Python with Unicorn, Lhasa and DOSBox-X. Use `../tools/dev` from the project
root as `./tools/dev`; see `../nix/README.md` for individual analysis commands.
The full shell and Nix flake checks have been verified.

Global `rea` and `rea-agents` launchers report 6.5.0 and forward to the user's
Nix profile. The Codex registration points to that launcher; the matching REA
skill is version 42. Existing connected MCP processes keep their old version
until reconnection. This work used a separate verified 6.5.0 MCP session, whose
server identity is preserved in `pcplus-main/binary_session.json`.

The original wrapper, Node launchers, Codex config and skill were backed up
before migration. Earlier npm/provider files remain available for rollback.
The mounted card's PCPLUS.EXE still matches the original SHA-256.

## Independent source link milestone

The dedicated project is now `bstar/pcplus-recomp`. The recovered UART source
supports OMF linking with named state and service symbols while the flat mode
still reproduces the original 1,099 bytes exactly. Its ISR data segment is a
linker relocation, replacing the baseline-only segment literal in this mode.
The separate 46-byte receive timeout remains verified in the compatibility path.

`standalone/serial.asm`, `data.asm` and `services.asm` provide a new DOS host,
new state storage and explicit minimal host callbacks. NASM and Open Watcom link
`build/standalone/SERIAL.EXE` without reading the original executable or data.
The host establishes SS=DS before calling recovered routines. This is an
independent serial diagnostic, not the full PCPlus application or its UI.

All three DOSBox-X cases pass: flow off, software flow and hardware flow modes.
Each echoes more than 4,096 bytes, crosses the receive-ring boundary and verifies
DOS exit, restored IRQ vector and ring invariants. The software case also checks
XOFF pause and XON resume. Hardware mode uses the emulator's asserted CTS;
CTS stall/recovery and physical UART validation remain open. Summaries and exact
binary hashes are committed in `../docs/validation`; full local logs are ignored.
See `../docs/UART.md` for calling conventions and inherited limitations.
