# Native PROGRAM Ctrl-Break services

The original resident routines at 7508 and 758a now rebuild as 80 and 36 exact
instruction bytes. The handler referenced by 7508 at 7f90 is one `IRET` byte.
The [receipt](validation/program-break.json) binds each source region to the
selected original executable, an independent MZ file mapping and a complete
REA byte read. No synthetic analysis carrier is executed.

7508 takes one callee-popped stack word and tests only its low byte. It sets
the saved break byte to FF. With a nonzero argument it queries DOS extended
break checking, saves DL and disables it if DL is nonzero. It gets INT1B and
INT23 through DOS, saves both far vectors and installs the same CS-owned IRET
handler for both. DS must equal SS because its argument read uses DS:BX=SP.

758a takes no arguments. It restores both saved vectors using temporary LDS
loads and restores DS afterward. It re-enables extended break checking **only
when the saved byte is exactly 1**. A saved 0 or FF leaves a child's current
break setting unchanged. This is measured native policy, not an exact snapshot
restore for every child mutation. Its near RET and assembly do not support the
three phantom parameters inferred by Ghidra's decompiler.

These routines provide no reentry guard or lifetime ownership. Reinstalling
without first restoring can replace the real baseline with the application's
own handler. A maintained application owner must validate admission, retain
callback code and integrate the PSP/trap/foreground unwind ordering before
binding these native services. They are not published by normal PROGRAM or
ASPECT in this checkpoint.

## Verification

```sh
./tools/build test-program-break
./tools/build test-program-break-source
# Analyst-only: requires the ignored genuine original executable.
./tools/build test-program-break-original
```

The linked instruction model passes 48 install/restore cases with 48 matching
genuine-original comparisons. It checks saved vector bytes, conditional break
policy, native stack cleanup, BP/SI/DI/DS/SS, DF and nonstack DS guards. Eight
additional IRET frames check IP/CS/flags/stack restoration. DOS21 vector and
break services in those model cases are explicit boundaries; raw nonboolean
query values do not claim actual DOS behavior.

The source-linked `build/program-break/BRKVEC.EXE` passes 16 actual DOSBox-X8086
cases: four native argument words crossed with initial and simulated-child
break0/1 settings. Actual DOS services get/set both vectors, software INT1B/23
run the installed IRET handler, and original vectors/break state are restored
independently before exit. Child vector/break changes occur in the parent; this
is not a child EXEC or physical-keyboard test.

The first two DOS attempts invoked this shell's built-in BREAK command, even
with the BREAK.EXE spelling. The required output assertion rejected both; their
captures remain retained. Renaming the diagnostic avoids that namespace
collision. A fresh tree with only eight declared source/provenance inputs
reproduces BRKVEC.EXE byte-for-byte, without an original, prior object, analysis
database or REA connection. All 31 preceding DOS products remain unchanged.

The adjacent PROGRAM services 40c9/40df were also inspected. They conditionally
call 5c20 with0/1; it writes index14h at the port held in DS7a90 and then31 or
the BDA0485 byte minus1 to the next port. Those static observations are retained
as a next recovery frontier; their hardware purpose and application integration
are not claimed here. Full controller, macro/window/error services, physical
testing and all F01–F16 gates remain open.
