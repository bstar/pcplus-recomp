# PCPlus analysis and DOS build environment

This isolated flake directory prevents Nix from copying the large disk images
in the project root into the store. `flake.lock` pins Nixpkgs; the npm lock and
Nix dependency hash pin REA 6.5.0 and its dependency graph.

The toolchain includes Ghidra 12.1.2, a full JDK 21, REA 6.5.0, Open Watcom V2,
NASM, Python, Make, and DOSBox-X. Ghidra 12.1.2 is accepted by REA's 12.1.x
adapter; its upstream verification version is 12.1.4. The original and derived
PCPlus images have been analyzed successfully with this pinned configuration.
Open Watcom's license is allowed only for its package family within this flake.
Nothing changes the system's Nix configuration or distribution packages.

Enter the full development environment from the project root:

```sh
./tools/dev
```

The smaller analysis environment avoids building the C compiler:

```sh
nix --extra-experimental-features 'nix-command flakes' develop ./nix#analysis
```

Useful commands inside either environment:

```sh
rea --version
rea mcp
python3 reconstruction/verify_uart.py
python3 analysis/inspect_pcplus.py
python3 analysis/rea_mcp.py analysis/pcplus-originals/PCPLUS-main-2.01.EXE analysis/pcplus-main --decompile-all
python3 analysis/prepare_overlay_analysis.py
python3 analysis/analyze_overlays.py
python3 analysis/prepare_overlay_analysis.py --entry-anchors
python3 analysis/analyze_overlays.py --entry-anchors
python3 analysis/audit_patches.py
python3 reconstruction/build_compat.py
```

`rea_mcp.py` is a small stdio MCP client, not a substitute decompiler. It starts
the Nix-provided REA MCP server, calls its actual tools, and saves complete MCP
responses and Evidence alongside pseudocode and assembly. It closes every
native analysis session. It never executes a supplied DOS binary.

The overlay adapter creates explicitly synthetic `.analysis.exe` files. It
places active parent overlays and the startup data at loader-derived addresses,
replaces overlay trampolines for static analysis, and preserves provenance in
its manifest. These files are not executable deliverables: never deploy or run
them. Their Evidence proves analysis of the derived input, not execution of the
original application.

`--entry-anchors` adds explicitly synthetic call sites for every known exported
overlay entrypoint. The summary measures function discovery against the
original 502-entry loader trampoline table; it does not prove recovery of every
unexported function. Initial unanchored exports are retained for comparison.

`build_compat.py` reassembles the recovered UART block and receive-timeout
routine (1,145 bytes), verifies exact original bytes and relocation positions,
inserts them in the preserved original container and assembles the two-byte
historical TECH_NET fix. Eight handler replay cases run in Unicorn. The rest
of the source project remains unrecovered.

Run these from the project root; each enters the pinned Nix shell:

```sh
./tools/pcplus-test build       # Partial source build and handler replay
./tools/pcplus-test test        # Full DOS original/candidate serial/key tests
./tools/pcplus-test test-modem  # Hayes/Telnet loopback test
./tools/pcplus-run              # Interactive private PCPlus install
./tools/pcplus-run --smoke      # Bounded headless launcher verification
```

The DOS harness executes local copies of PCPlus and its ASPECT compiler in
DOSBox-X, records serial streams and outcomes under `reconstruction/lab`, and
never modifies the mounted card. The interactive launcher preserves its own
private configuration between runs; its generated PROFILE startup script and
PCPLUS.EXE are refreshed. This emulation evidence does not establish physical
Wi-Fi modem or public-BBS compatibility. No archived patcher is executed.

Validate the Nix expressions and build a small DOS compiler probe:

```sh
nix --extra-experimental-features 'nix-command flakes' flake check ./nix
```

The default shell's first build may take time because Open Watcom is built from
its pinned source. The probe is a new test program, not rebuilt PCPlus.

## Global REA

REA 6.5.0 is installed in the user's Nix profile. The global `rea` launchers
forward to that profile, and the Codex REA registration uses the same launcher.
The matching REA skill is installed under `~/.agents/skills`. Earlier launchers,
the Codex configuration, and the skill were backed up before migration.

Existing MCP connections keep their original server process. Restart/reconnect
Codex to use the new registration in its built-in tool connection. The analysis
in this project uses its own verified REA 6.5.0 stdio MCP session immediately.

The previous npm installation's files and the earlier extracted Ghidra/Java
installation remain available for rollback, but the active launchers use Nix.

## Independent source-only DOS program

From the dedicated repository root, `./tools/build` assembles the recovered
UART block as OMF and links it with a new DOS host. `./tools/build test` runs
three full-DOS driver cases. Neither command needs a source PCPlus executable;
see the root README and `standalone/`. The original compatibility build remains
a separate target, `./tools/build compat`, requiring local ignored originals.
