# Retained ASPECT return to the terminal

The experimental capability7 terminal now identifies an ASPECT child that
returned through DOS31. It keeps the existing error notice and adds
`ASPECT memory retained.` when the raw DOS4D result's mode byte is3. Ordinary
errors keep their existing notice. The parent's execution boundary already
preserved the complete raw status and treated a nonzero child result as an
error; no status normalization was needed.

The [attached-return receipt](validation/parent-exit.json) accepts eight routes:
COM1/COM2 crossed with no, software, hardware and combined flow control. Each
executes the actual terminal, banked ASPECT CLI, DOS child and RUN/WAIT cleanup.
A controlled timer changes foreground INT1B ownership and supplies one BIOS
key, as in the [CLI exit test](EXIT_OWNER.md). The real guard quarantines the
owner and retains the child. The parent then resumes its terminal loop.

The observer records DOS31 before termination and intercepts the real DOS4D
query afterward. Its additional15 words bind:

* DOS31 and raw return030A, preserving state error10 and retained mode3.
* The child PSP, MCB owner and complete paragraph count before/after return.
* INT1B's actual far pointer, matched against the linked source-owned ISR.
* That ISR's data counter changing0 to1 after child termination.
* A separate retained DOS allocation's owner,32-paragraph size and A55A marker.

The observer actively invokes **only the known test ISR**. It does not restore
unknown vectors, repair leases, supply cleanup results or replace terminal
services. The product's exit guard never invokes an unknown vector. The first
observer attempt rejected the map's unreferenced-public `+` marker before DOS
execution; the corrected parser accepts the linker's public-symbol markers.

All eight routes pass296 checks. The captured parent renderer lease is closed,
its JFT/file-owner bytes match, the script does not continue or transmit its
password after the error, and the new notice is visible. Real keyboard output
continues as `ready`. The independent peer then sends a fresh positioning/query
sequence and receives the exact cursor reply through the resumed parent UART.
This checks receive/parser/reply operation after the retained child's return.

Thirteen normal attached workflows pass518 checks with the same parent. These
cover successful WAIT/NOCLEAR, ordinary failure, repeated child calls, compiler
fallback, shared streams/environment/enumeration and both COM ports with all
flow modes. They also require the retained-memory notice to be absent. The
existing standalone recovered-EXEC parent repeats277 memory-pressure checks
against the updated CLI probe. That allocation/fill test is separate from the
attached observer's post-return MCB/callback test.

```sh
./tools/build test-aspect-parent-exit
./tools/build test-aspect-banked-cli
./tools/build test-aspect-parent-exit-source
```

A fresh tree containing only declared sources reproduces31 products, including
both exit probes, the banked CLI, attached/default terminals, compiler and
process components. The default terminal and ASPECT hashes retain their earlier
values. The opt-in notice adds no near data or resident code: the attached
terminal remains64832 data/stack bytes and65368 resident code bytes, with the
new text/logic in its existing ASPECT code bank.

Retained allocations/remaining handles intentionally persist; automatic repair
or unloading is not implemented. Mouse-enabled fatal return, a normal script
retry in the same DOS session after retention, normal dispatch publication,
remaining native services, broader application ownership and physical
RS232/WiFi-modem/keyboard acceptance remain open. This checkpoint closes no
F01–F16 full application gate.
