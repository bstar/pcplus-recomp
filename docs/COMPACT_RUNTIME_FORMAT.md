# Compact interpreter formatting and nested compilation

The optional native-reset parent can now compile and execute source scripts
with the maintained ASPECT interpreter. The preceding attempt failed at step0
with out-of-memory; it remains recorded in
[the historical parent receipt](validation/native-reset-parent.json).

The fix removes the general CRT printf engine from ASPECT. The command-line
owner now constructs its fixed error message directly, sharing the same text
between attached video and stderr. The source-compiler bracket constructs its
exclusive `LPCxxxxx.LOG` filename with the same five uppercase hexadecimal
digits. A private adapter handles the six fixed recovered formats used by
file enumeration, timestamps, DOS version and drive prefixes. It preserves
padding, zero precision, signed 16-bit values, 32-bit file sizes and return lengths;
it does not expose a replacement general printf service to scripts.

The guarded custom-IRQ interpreter drops from 115,026 to 112,382 executable bytes.
Its paragraph-rounded DOS loader minimum, including the PSP, drops from 139,456
to 136,800 bytes: 2,656 bytes reclaimed. Its 8,192-byte stack is unchanged. There
are no grammar, script-line, AST, terminal-history or screen-buffer reductions.
The compiler and optional terminal remain byte-identical. Link-map checks
confirm `sprintf`, `vsprintf`, `fprintf` and the general `__prtf` engine are absent
from the new interpreter.

## Verified scope

The [validation receipt](validation/compact-runtime-format.json) binds:

- 741 declared source/test/toolchain files and four exact fresh-tree products.
- 3,907 comparisons against the host and actual DOS8086 CRT, including exact
 lengths/bytes, full 32-bit sizes, signed extrema, output guards and short error
 message buffers.
- 21 actual production CLI children and 105 checks; 22 source-compilation cases
 and 223 checks, including chained state, compiler fault isolation, cancellation,
 OEM paths and 20 repeated real compiler replacements.
- Four nested source workflows beneath the unchanged guarded branded native-reset
 parent on DOS8086: explicit source on COM2/IRQ5, missing-ASX fallback on COM1/IRQ4,
 chained compilation on COM2/IRQ7 and rejected-source recovery on COM1/IRQ5.
 The explicit case preserves 32 preexisting log files across hexadecimal name
 collisions. All cases verify cleanup, parent parser recovery, PRM and hardware.
- The existing runtime diagnostic corpus: 1,125 cases/27,030 checks. Native file-listing
 consumers pass 310 cases/22,383 checks, timestamp consumers 248/2,907 and system
 queries 341/2,905, including their independent native controls and repeated
 heap/JFT/DTA ownership checks.
- Seven actual DOS UART compilation cases across NONE, SOFT, HARD and BOTH
 flow control, including three 3,200-byte pressure cases. Those deliberately
 hold the real compiler for 36 BIOS ticks and verify exact unread ASIO return,
 transmitted control bytes, numeric/BREAK state and IRQ/vector/PIC/MCR guards.
 These use the default interpreter with a declared diagnostic serial parent;
 the four branded-parent workflows above separately test the guarded build.

The default interpreter is now
`bfd1a4e1998c8f82b27bdd35615948b3d94e8ae3bd308d03fb4187e728d3eed1`.
The guarded custom-IRQ interpreter is
`495d4852275bb7f14c897c8ea9fcaee4620c939690402898fd0c3c6e64723dd7`.
The terminal remains
`dea8981a81c9d996b77cc8a9bed5166968b945bc9b5d9cbd9d2fce9ca579f17a`
and ASPCOMP remains
`18789792ad9e1be92057386d4405e4091e488d9bd8368490f414477e3dd5c8a2`.

```sh
./tools/dev --command python3 standalone/check_compact_runtime_format.py --output build/UNIQUE_FORMAT_RUN
./tools/dev --command python3 standalone/prove_compact_runtime_source.py --output build/UNIQUE_SOURCE_RUN
```

The source proof expects current product manifests and rebuilds all four in a
fresh directory without copying any existing executable, object, original or
REA database. Its accepted run is `build/compact-runtime-source-01`. Seal a
matching proof with `standalone/record_compact_runtime.py --proof ... --output ...`.

This closes the recorded nested-compilation memory gate. It is not an arbitrary
conventional-memory guarantee or complete native-width application acceptance.
The cold bank still needs live renderer/profile projection, commit and display
rollback. General width/UI/BBS composition, full native application/language and
physical modem acceptance remain open. The staged package and card are unchanged.
