# Compiler heap admission beneath the live-transaction parent

The later [row/startup checkpoint](LIVE_RESET_ROWS.md) adds a borrowed metadata
tail for the larger parent and repeats the compiler corpus and ownership checks.
The identities and receipts below describe this earlier allocation fix.

The larger transaction parent now passes all four recorded nested source
workflows with the maintained compiler. The parent and ASPECT binaries retain
their previous identities; the change is in ASPCOMP's allocation policy and
stream-buffer ownership. This resolves the compiler gate recorded as failed in
[the live transaction checkpoint](LIVE_RESET_TRANSACTION.md).

The first-pass allocator still prefers 512-byte metadata pools. If that physical
allocation fails, it halves the optional capacity until a smaller pool fits or
the exact aligned object extent also fails. At most ten physical attempts are
possible. Logical allocation counters and injected failure ceilings still apply
once per requested object. Every successful pool is linked into the same owned
list and retired by the existing disposal path.

The CLI lends two 512-byte stream buffers from its existing 24 KiB stack
reservation. Their lifetime covers all reads, seeks, flushes and both closes;
the CRT never owns or frees them. This avoids spending two additional far-heap
blocks while a terminal and interpreter remain resident. Buffering remains
enabled, and compiler input/output publication rules are unchanged. The public
compiler API retains its existing borrowed-FILE behavior and workspace contract.

The final executable is 52,022 bytes, compared with 51,766 previously. Its DOS
loader minimum, including the PSP, is 75,472 bytes rather than 75,216. Its stack
remains 24,576 bytes. The fix therefore comes from reusing reserved storage and
avoiding unnecessary pool slack, rather than reducing the loader minimum, stack,
grammar, line limit or expression capacity.

## Verified scope

The [receipt](validation/compiler-arena-fallback.json) binds:

- A fresh original-free build of four exact products from 799 declared source,
 test and toolchain files. Both ASPECT variants and the transaction parent remain
 byte-identical; the new compiler is
 `8be133a27ea1bff0484a7ecba751a92d0e631d60725901289bc927f7b5d043ce`.
- Actual DOS allocator controls using real CRT allocations with a test-imposed
 block-size ceiling. The predecessor without fallback rejects the constrained
 inventory, while the new allocator produces the same inventory as an ordinary
 allocation. All 21 logical fault positions, total physical rejection, 100
 successful reuse cycles and far-heap/foreign ownership checks pass. The control
 has 66 checks and the fallback has 611. The fixture warms its own comparison
 streams before observing compiler ownership and uses the CRT's actual calling
 convention for the allocation wrappers.
- The complete 2,043-case maintained grammar corpus: 1,077 exact accepted ASX
 outputs and 966 rejected sources. The 18 checked CLI depth cases retain the
 24 KiB stack; the checked compiler API retains 16 KiB. Publication, rename
 rollback and allocation faults remain covered by the corpus harness.
- The borrowed-workspace suite: 12,746 checks, including 100 cycles, with the
 unchanged 11,306-byte workspace. The first-pass inventory regression passes
 2,015 cases and 5,028 checks against the maintained host.
- Explicit compilation on COM2/IRQ5, missing-ASX fallback on COM1/IRQ4, chained
 compilation on COM2/IRQ7 and rejected-source recovery on COM1/IRQ5 beneath the
 guarded branded transaction parent. All ASX bytes, parent parser recovery,
 hardware/PRM, log cleanup and 32 preexisting log collisions are checked. These
 trials link the transaction API but run in the ordinary display geometry;
 they do not prove ASPECT rendering with an active 132-column viewport.
- Seven UART compilation cases across NONE/SOFT/HARD/BOTH flow, including three
 3,200-byte pressure cases with a declared 36-tick hold around the real compiler.
 Exact unread ASIO bytes, control traffic, numeric/BREAK state and IRQ/vector/
 PIC/MCR/guard ownership pass.

Earlier attempts remain under ignored build storage. An exact-size-only retry
passed explicit compilation but failed the chained source. Geometric pools
compiled the first chained file but exhausted heap in the second. Borrowing the
stream buffers resolves those recorded cases without weakening their tests.

```sh
./tools/dev --command python3 standalone/check_compiler_arena_fallback.py --output build/UNIQUE_ALLOCATION_RUN
./tools/dev --command python3 standalone/prove_arena_fallback_source.py --output build/UNIQUE_SOURCE_RUN
```

The proof expects current manifests for the compiler, both ASPECT variants and
the guarded branded transaction parent. The accepted run is
`build/arena-fallback-source-02`; it repeats allocation controls, the full grammar,
stack/workspace checks and all four nested workflows in the fresh source tree.
The preceding failed transaction receipt is retained as historical evidence.

This is not an arbitrary low-memory guarantee. Normal peer width dispatch is
still disabled. General rows/margins, protected fields, modal/child rendering,
width-changing BBS sessions, full native application coverage and physical modem
acceptance remain open. The staged package and card are unchanged.
