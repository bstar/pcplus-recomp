# EMULATE admission and rejection recovery

The optional parent `856a9c85` and child `5c641ac4` pass the following additional
checks. Application bytes and installed R59A85A8 are unchanged. The machine
readable record is [validation/aspect-emulate-guards.json](validation/aspect-emulate-guards.json).

## Linked instruction checks

The parent allocation validator passes52 cases for capability20: PSP/MCB owner,
allocation/physical bounds, client extent, token, magic, wrong versions,
callback overlap and first/last permitted callback addresses. Rejected requests
retain the output sentinel and the checked caller registers/stack. This invokes
actual linked C instructions with authored allocation/client bytes; it does not
execute DOS allocation or the resident bridge.

The current child passes59 cases: descriptor capability versions, declared
stack extent and adjacent live-SP limits, all four redzone words, exact live
serial ownership, scalar selector bounds, typed parent results and subsequent
same-process requests. Repairing an intentionally damaged guard allows the next
request. Stack extents come from the actual linker map; usable CRT bounds and
near caller frames are authored. DOS/UART/BIOS and the scalar far endpoint are
modeled. These checks do not establish instruction timing or full bridge fault
composition.

## Actual DOS recovery

Two runs use the ordinary source-built products, a synthetic serial modem and a
passive exit observer. Each passes32 specialized checks:

| CPU | Unsupported selector | Observer | Observed error/opcode |
| --- | --- | --- | --- |
| 386 | TTY,0 | UMB segment CC4Bh | 3 / 2Fh |
| 8086 | WYSE100,32 | Conventional segment0814h | 3 / 2Fh |

The compiled script transmits REJECTBEGIN, executes native EMULATE and never
reaches REJECTBAD. The observer records exit3/error3/opcode2F, DS=SS and clean
owner retirement. Three later scripts in the same parent lifetime successfully
open six streams, recover a missing file and switch VT220→ANSI. Fresh DA replies
come from the actual parent parser. All later interpreter errors/cleanup and
native owner fields are zero; keyboard input and hangup still work afterward.

The observer changes resident memory usage. These are recovery checks, separate
from the unobserved capacity results in [ASPECT_EMULATE_SHARED.md](ASPECT_EMULATE_SHARED.md).
The generic connection harness retains its old-banner failure because EMULATE
intentionally clears that view; the specialized result checks initial CPR order,
actual profile DA replies and the final reset screen instead.

## Remaining

Full resident-bridge negative composition, modal/WHEN/native abort/fatal-reset
paths and receive-service latency remain open. Only unsupported selectors0 and32
ran through the native VM here; earlier direct parent tests cover all other
unsupported byte selectors. Current-product Enigma/Synchronet regressions,
package reproduction and physical Boca/SPA2102/SynthModem acceptance remain
required before selecting this optional pair. This is not full feature parity.
