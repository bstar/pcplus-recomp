# Live compiler bridge checkpoint

The opt-in capability23 pair can compile source while the complete terminal and
ASPECT interpreter remain loaded. Startup `LOGIN.ASP` and source `EXECUTE` run the
actual DOS compiler, execute its exact ASX output, complete GET input and return
to ordinary terminal input. This checkpoint is experimental; the selected
connection package and physical machine are unchanged.

It extends the [whole-kernel arena loader](ASPECT_COMPILER_ARENA.md). The source
build uses the keymap connection recipe, parent `--compiler-lease-bridge` and
child `compiler_parent_lease=True, heap_growth_bytes=256`. Parent/child capability
versions must match. Existing ASIOv7 layout remains unchanged.

## Admission and lifetime

Requests27/28 use the authenticated resident renderer. BEGIN requires the child
serial pause and compiler scope, no field/window/confirmation/PROGRAM/snapshot
owner and the expected parent/child PSP chain and MCB ownership. DS=SS is the
checked retained parent RPC stack. The live UART IRQ vector must point into the
child allocation; the parent `vector_active` flag is only a suspended cleanup
marker and cannot establish actual ownership.

The loader's compiler kind4 can load only through this separately admitted
foreground path. Other UI/history owners remain excluded. Load and relocation
finish before trusted init; only init briefly adopts the parent PSP. CurrentPDB
returns to the child before the lease, compiler or child file operations.

The whole3,408-byte kernel plus146 fixup bytes lives in existing snapshot space
at offset16,384. The retained cut follows the module. BEGIN verifies and backs
up the later parent tail before shrinking its MCB; the actual compiler EXEC then
has enough conventional memory. END regrows and verifies the entire tail before
releasing the module claim or resuming ordinary interpreter/rendering work.
All current application capacities, stacks, history and UART buffers are retained.

While memory is lent, ordinary renderer requests are refused. A tagged `E000`
response explicitly attests intact/restored parent memory with a typed error;
an untagged END failure enters BIOS-only repair/key/retry instead of touching
missing parent state. Unexpected child termination with an active loan enters a
BIOS fail-stop. Those application-level fault/recovery paths still need dedicated
injection tests; they are not accepted merely because they exist in source.

## Return-stack and memory fixes

An initial live test compiled and ran successfully but crashed on the final
ASPECT return. DOS INT21 entry updates CurrentPDB:2E with its return SS:SP.
Temporarily adopting the parent PSP overwrote the suspended outer EXEC stack.
Both init and resize scopes now save that far pointer and restore it after
switching CurrentPDB back to the child. Renderer retirement also preserves the
assembly caller's registers and FLAGS around shared-loader cleanup.

The first512-byte heap-growth child passed ordinary/lifetime/WHEN cases but a
framed WHEN arithmetic-error case with an open file ran out of near heap.
The existing256-byte growth option removes excess allocation granularity;
it does not reduce object, stack, stream or interpreter limits. This case
remains a required regression and reaches its expected arithmetic error.

## Evidence and limits

The machine-readable [validation record](validation/aspect-compiler-bridge.json)
binds exact sources, artifacts and checks. The full-parent source cases require
one actual compiler EXEC with116,576 bytes available at that attempt, byte-exact
generated ASX, successful compiler status,
GET input/password/cursor replies, no stale/trailing execution, stream closure,
parent file-owner/history retention and ordinary parent keyboard resumption.
Precompiled regressions cover all27 existing GET cases. A separate retained-arena
kernel harness passes1,416 client checks and three exact109,792-byte restorations.

`standalone/prove_compiler_bridge_source.py` exports only the public source
closure, rebuilds parent/child/compiler and all module files, and replays supplied
reports. The1,037-source export reproduces all six artifact files and all29 DOS
cases. It compares exact artifact identities, serial bytes, check booleans,
observer code, memory/allocation and compiler probes with no prior objects,
original executables or ancestor Git available inside the export.

The peer is an owned emulator modem, not SynthModem or a live BBS. Physical
Boca/SPA2102 carrier/flow control, sustained traffic, real disconnect/reconnect
and transfers remain unverified here. The NIC/modem IRQ5 constraint still applies.
The whole-language/full-ASPECT, application parity and package-promotion gates
remain open. Do not deploy this experiment solely on these compiler tests.

Next: inject full-parent source compiler errors, missing/corrupt modules and
restore failures; verify quarantine/repair and unexpected-child containment,
repeated compilation and shared-arena reuse in one parent process. Then broaden
source-language/UI/stream composition and re-run the selected connection package
before requesting physical modem acceptance.
