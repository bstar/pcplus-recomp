# Retained ASPECT return to the terminal

The [mouse-enabled receipt](validation/parent-exit-mouse.json) extends this
checkpoint to the capability7 terminal with native mouse support: eight retained
child routes pass376 checks and thirteen normal routes pass648 checks. Both COM
ports and all four flow modes are covered. This adds validation without changing
the product sources or promoting the experimental dispatch to normal publication.

An independent observer captures INT33 registration and the complete driver
snapshot before terminal startup. During ASPECT execution it verifies the mouse
event mask is zero; a disabled driver may retain an inactive callback address.
After return it checks the registration against the linked native callback,
invokes that known callback with foreign DS=0040, and verifies balanced callback
depth, preserved DS, PRM scales8/4 and an unchanged queue for a neutral event.
On the actual Alt-Z menu, motion queues two Down events and a left click queues
Enter. The menu consumer selects Write Screen and creates a nonempty
`PCPLUS.SCR` containing the live screen rather than the menu. Keyboard transmission
and the fresh serial cursor query still work afterward.

At normal terminal DOS4C exit, the registration and all576 saved driver bytes
match the startup baseline. Startup and suspended-child snapshots are distinct:
the reset driver during child execution is not the terminal's original state.
These routes use DOSBox-X's built-in driver. The separate mouse-owner component
tests cover a pre-existing nonzero callback; this receipt does not establish
physical mouse-driver or modem compatibility. Timer-injected native events test
the real producer/consumer path but do not represent physical mouse movement.

The observer's first assembled image exceeded DOS's COM load limit and timed
out. Its report copy now uses a separate DOS48 allocation after relocating the
collector stack and resizing its PSP block. Assembly rejects oversized COM
images. Full before/after snapshots remain resident and are compared byte for
byte; the observer does not repair the product's driver state. Failed pilot
captures remain in the local build tree. A clean declared-source tree reproduces
33 products including both mouse terminals; the mouse-enabled parent uses64864
data/stack bytes and65518 resident code bytes, leaving18 resident bytes spare.

```sh
./tools/build test-aspect-parent-exit-mouse
./tools/build test-aspect-parent-exit-mouse-normal
./tools/build test-aspect-parent-exit-mouse-source
```

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
or unloading is not implemented. A normal script
retry in the same DOS session after retention, normal dispatch publication,
remaining native services, broader application ownership and physical
RS232/WiFi-modem/keyboard acceptance remain open. This checkpoint closes no
F01–F16 full application gate.
