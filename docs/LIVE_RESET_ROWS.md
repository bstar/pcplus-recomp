# Explicit width changes from normal startup

The optional native width transaction now accepts coherent plain profile4/6
layouts with1..25 rows and valid scrolling margins. The normal peer width
requests remain unbound. This extends the earlier
[live transaction checkpoint](LIVE_RESET_TRANSACTION.md); its failed compiler
receipt remains historical, and the later
[compiler fix](COMPILER_ARENA_ADMISSION.md) is retained unchanged.

A visible status line owns physical row25. The application's legacy narrow
startup describes25 rows, so its first explicit width transaction adopts24
content rows. Hiding status permits25 content rows. The transaction resets
scrolling margins to the full admitted content, retains the origin-mode flag,
and clears/homes that content. This margin policy belongs to the maintained
adapter, rather than a claim about recovered native behavior.

Saved cursor coordinates are clamped to the resulting row/column bounds.
Current and saved pending-wrap latches are cleared: restoring a saved position
from column132 must not put an80-column cursor outside its display, and an old
right-edge wrap must not carry into a newly cleared display. Entry requires
consistent cursor, previous-cursor, viewport and cached video/attribute offsets.
Unsupported or intermediate states refuse before the workspace is borrowed.

The scalar projection stores its commit flag in the high bit of each root
offset; link inspection verifies all34 field names, offsets and flags and
refuses any root offset that no longer fits15 bits. Nearby failure returns
keep8086 conditional branches compact without dropping admission checks.

The native width routine remains separately recovered. A maintained ABI wrapper
derives its resulting cell count from the admitted row owner instead of retaining
its original24-row constant. Native allocation requests must equal rows*264;
private far pointers never become root-owned pointers. The root RIS baseline,
serial/parser/connection state, file handles and configured defaults are excluded
from the display projection.

The transaction-only borrowed image begins at offset0, removing its unused
256-byte prefix. Its full4096-byte private stack ends atE600, followed by a
6600-byte shadow ending atFFC8. The existing65504-byte workspace still leaves a
24-byte tail guard. No parent data/stack reservation is added. The branded
parent minimum allocated module is404848 bytes,304 more than the earlier24-row transaction.
Cold-only builds retain
their earlier prefix/layout. Rollback uses at most the existing4000-byte PROGRAM
screen buffer and restores only admitted content; an independently owned visible
status row is preserved. When status is hidden, all25 rows belong to content.

## Validation

The [row/startup receipt](validation/reset-rows.json) binds a clean source-only
rebuild of four terminal products, both ASPECT children and the updated compiler.
The ordinary and cold-only terminal hashes remain exactly
`01f55dfbf5385136931c96700be3173cf8594be1c17677e9852fb0f1d025e447`
and `999a9a329d88317f786ef2a22e7dd94c33bb2c994501b0a9d17cb2892ae74e52`.
The new base transaction is
`1265e7cb481e13e4054ea33de06764e714abb106aff07aa60bf51617a96856f4`;
the branded transaction is
`32ee91479f44ea499d64a67fffc83fe5951c16f1eec9d8a960bc585301adce55`.

Each linked model checks25 repeated/interrupt-bearing commits,112 row/margin/
origin/saved-cursor transitions,20 injected-fault rollbacks with the actual root
UART ISR on the private stack, and62 refusals. Rows1,5,24,25 cover single-row,
interior and upper boundaries, with status visible/hidden and profiles4/6. Real
ESC7/ESC8 parser calls check saved positions and pending wrap after both widths.
The fault cases preserve root near data, unread binary RX, root shadow and BIOS
cursor/shape while restoring exactly the owned content. These are hardware-model
checks, not physical ISA tests.

Both base and branded DOS8086 witnesses start from the application's25-row
geometry. They call the real public far API after a BIOS cursor operation,
without changing the row count. The optional hidden-status witness changes only
status ownership. All four runs observe the native clear before parser redraw,
verify the exact132-column logical screen and bottom-row CPR, restore DS=SS,
and compare the ordinary42-byte hardware/vector snapshot. The MZ is unmodified.
This fixture is an explicit API caller, not normal BBS width dispatch.

Cold bank checks on the cold-only and both transaction parents also check
namespace/ownership separation, retained PROGRAM storage, busy-owner refusal,
tail guards, and rejection of four malformed map layouts. Under the new branded
parent, ordinary-display nested compiler trials cover explicit source, ASX
fallback, chained execution with numeric/BREAK state retention, and invalid
source recovery. The explicit case preserves32 preexisting log files. ASPECT is unchanged. The compiler now lends256 bytes beyond its caller-owned
context for first-pass metadata, falling back to ordinary arenas when full.
The CLI supplies that tail from its existing24KiB stack reservation; no stack or
grammar bound is reduced. It never links borrowed storage into the heap free
list. The entire supplied workspace span is checked for segment/physical wrap
and aliases, including aliases that occur only in the metadata tail.

This change follows an actual failed chained trial under the larger parent:
`NEXT.ASP` failed with heap error3 at line4 even though the explicit and fallback
workflows passed. Compacting the projection and8086 branches alone did not fix
it. The borrowed metadata fix passed the same chained source and exact ASX
checks. Failed runs remain under `build/reset-rows-source-01` and
`build/reset-rows-compact-chain-01`/`02`; they are not accepted receipts.

The updated compiler is
`0d2712885175f1cb7fa67e7f77eae392bca724d4cc61f41e2484f9ed6586c47a`.
The initial1024-byte CLI tail exceeded the checked stack on a line-limit
unary expression. The accepted256-byte tail keeps that expression and all
other depth cases within the existing24KiB reservation. The source proof repeats all2043 compiler cases,18 checked CLI expression-depth
cases and publication-fault CLI variants with the full24KiB stack, a
checked16KiB API corpus and deliberate2KiB
stack-overflow controls. Workspace ownership tests run100 compiles each with
zero,16,256 and1024 borrowed metadata bytes, check every logical metadata fault
position and a tail-only report alias, preserve guard/foreign heap ownership,
and verify exact emitted ASX. Existing bounded physical arena-fallback tests
also repeat. Ordinary initialized compiler units retain heap ownership;
only an explicitly enlarged workspace lends metadata.

Reproduce after building current ordinary, cold-only, base and branded terminal
manifests plus the custom-IRQ ASPECT and compiler products:

```sh
./tools/dev --command python3 standalone/prove_reset_live_source.py --output build/UNIQUE_ROWS_PROOF --nested
./tools/dev --command python3 standalone/record_reset_rows.py --proof build/UNIQUE_ROWS_PROOF --output docs/validation/reset-rows.json
```

The accepted run is `build/reset-rows-source-06`. The proof copies only declared
sources into an initially build-free directory, rebuilds the seven exact products,
runs the checks there, and verifies source hashes again afterward.

## Remaining work

The transaction is excluded from the staged/card package. Protected-field repair,
scrolling and modal/UI/ASPECT rendering in active wide mode must compose before
peer requests can call it. Nested compiler admission with the ordinary display
does not establish an active132-column child renderer. A width-changing BBS
session and physical modem/card tests remain unverified. The absent DOS card has
not been written during this checkpoint.
