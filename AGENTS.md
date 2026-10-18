# PCPlus reconstruction

Use the pinned Nix toolchain through `./tools/build` or `./tools/dev --command`.
The default build produces source-only DOS UART, parameter-parser and BIOS
keyboard diagnostics. It must not read any
original executable, original install or generated REA database.

`./tools/build test` exercises the standalone linked DOS programs. The separate
`compat`, `test-compat` and `test-modem` targets require ignored local originals.
Preserve exact baseline comparison in the flat UART build. Intentional behavior
changes need explicit regressions and must remain distinguishable from recovery.

Maintain the real-mode ABI: DS equals SS for routines using DS:BX stack access;
OMF builds use linker symbols while the flat build keeps original addresses.
Never execute synthetic `*.analysis.exe` inputs.

This repository is public. Keep original executables, private dialing files,
disk images, downloaded proprietary archives and generated analysis databases
out of Git. Keep evidence, source provenance and limitations explicit. Do not
claim a complete PCPlus source build until the original executable is absent
from every application build input.
