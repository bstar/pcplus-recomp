# CRT-free banked mouse ownership

The mouse owner now has a DOS allocator backend and an explicit code-bank ABI.
An assembly-started parent executes that combination without linking a C runtime
or initializing a CRT heap. This removes the allocator/startup obstacle recorded
in [mouse/keyboard composition](MOUSE_KEYBOARD.md). It does not yet connect mouse
ownership to the interactive terminal's startup, menus or ASPECT controller.
The [validation receipt](validation/mouse-bank.json) records the exact scope.

## Allocation and release

`MOUSE_DOS_PLATFORM` selects `src/mouse/dos_memory.asm`: INT21/48 allocates a
paragraph-rounded block, INT21/49 releases it, and INT21/3533 obtains the driver
vector. Allocations return offset0. Zero sizes, invalid release pointers and DOS
errors are explicit failures. Rounding works through65535 bytes without wrapping
the intermediate16-bit byte count. Byte loops replace CRT memory helpers in this
owner build; its object imports only the declared mouse services and compiler
small-code marker. The ordinary CRT diagnostic remains a separately tested build.

The parent must first release its PSP's unused maxalloc memory while retaining
every code, data, callback and stack segment. The allocator deliberately does
not guess that boundary or shrink the PSP itself. The test host calculates the
bound from its DS/stack end, and the builder checks that every linked segment,
including the callback's private foreign stack and mouse code bank, lies below
that bound. It also checks the full BSS clear range before accepting the build.

A failed DOS free keeps the owner quarantined. Once original driver/native
state has been restored, a later close retries only the storage release. The
same applies to a rejected snapshot before any driver mutation. Such retries
need not call a driver whose vector has subsequently changed. The linked tests
inject both failures and verify that retry frees the block without driver calls.
If restoration is still outstanding, vector/size/guard checks remain mandatory.

## Code segments and ABI

The maintained owner, native producer, native far callback and driver adapters
live in `MOUSE_CODE`. The native keyboard consumer stays in resident `_TEXT`.
`src/mouse/abi.inc` declares all eight public entry names and their exact
caller-cleaned argument-word counts. Existing explicit C adapters copy those
words across CALL FAR/RETF; two far resident services bind polling and reading
back to the real native keyboard routines. The callback continues to accept
the driver's foreign DS/SS. Foreground C operations still require DS=SS.

The test parent deliberately adds60000 trap bytes to resident code. Its near
segment occupies63383 bytes; the2266-byte mouse bank has a different CS. Linked
replay verifies execution in that bank for all eight C implementations and the
native callback, and resident CS for both keyboard services. It checks caller
argument preservation, stack balance and the existing BP/SI/DI/DS/SS contract.
BX/CX/DX and flags remain compiler temporaries; callers use the declared C ABI.
The padding belongs only to the diagnostic, not the production mouse module.

## Execution and reproduction

```sh
./tools/build test-mouse-bank
./tools/build test-mouse-bank-source
./tools/build test-mouse-keyboard-dos
./tools/build test-mouse-keyboard-dos-source
```

The banked `MOUSEBNK.EXE` performs46 actual8086 DOS assertions. It checks native
mouse-to-keyboard consumption, BIOS priority/fallback, typed settings and exact
opaque driver restoration. Both children launch through maintained `process_run`
and DOS EXEC, with no CRT `spawnl`. They independently check callback retirement,
change sensitivity/position, and install/read back/retire their own callbacks.
The vector-changing child still requires explicit diagnostic repair before close.

DOS MCB traversal verifies one extra parent-owned block while the mouse owner is
held, retention through each child, and its release after close. The retained PSP
size stays constant through the handoffs. All576 reported driver-state bytes and
all28 native bytes match their initial snapshots. The prior callback is retired
before process exit. These checks use the DOSBox-X driver, not physical input.

Current results are84 linked bank cases and46 actual DOS assertions; the DOS
allocator/CRT-started variant contributes84 linked cases and42 DOS assertions;
the CRT allocator regression contributes76 linked cases and42 DOS assertions.
Each variant reproduces its executable and both children from a fresh source
tree. The children are shared byte-identical products across the variants.
All27 preceding application products and their frozen source inputs remain
unchanged. Their earlier161 DOS cases are carried by executable identity, not
represented as newly executed here.

Remaining integration includes startup/live settings UI, terminal menu dispatch,
PROGRAM and ASPECT ownership/fault paths, and safe handling of quarantine before
application termination. Physical mouse/modem testing, other DOS kernels and
the other application requirements remain open. No whole-application gate closes;
the separate live ENiGMA decoder remains unchanged.
