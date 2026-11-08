# Source compiler residency under the complete parent

Source compilation currently fails under the full experimental parent and GET
interpreter at640KB. This is a confirmed compatibility gap, not a successful
compilation checkpoint. Earlier standalone compiler/serial checks and the
[27 attached GET cases](ASPECT_GET_WIDTHS.md) remain valid within their scopes;
those GET programs were compiled before parent startup.

Two new owned DOS cases reach actual ASPCOMP.EXE EXEC with the connection live:

| Source route | Largest free block immediately before nested EXEC | Result |
| --- | --- | --- |
| LOGIN.ASP with no LOGIN.ASX | 2,368 bytes | Compiler fails to start; runtime error8, compiler exitFFFF, Watcom errno5 (ENOMEM). |
| Compiled login executing NEXT.ASP | 1,856 bytes | Same refusal; prior NEXT.ASX preserved; open stream flushes exact BEFORE\|. |

The optional compiler's page-based DOS load minimum is75,920 bytes including
PSP, before environment and dynamic allocations. The complete parent minimum
is481,712 bytes and GET interpreter136,128 bytes. Their sum693,760 already
exceeds640KB. Actual nested EXEC measurements establish the much smaller free
blocks after live allocations; header arithmetic alone is not the runtime test.
These numbers bind parent `b25fe6d2…`, GET interpreter `54590fd3…` and compiler
`db9de7ca…` in the checked DOS386/UMB fixture.

The passive INT21 observer samples AH48's largest block only for nested EXEC
while the ASPECT invocation is active. It records the real compiler pathname and
one attempt, and preserves the caller's registers and flags. Later SNAP/RENDER
helpers cannot overwrite that sample. It does not alter allocations, force an
EXEC result or resize the product. A request for FFFF paragraphs fails without
allocating a block.

Both cases retain the connection and return to parent keyboard/hangup with file
and sink ownership restored. No failed compiler output is published, no stale
ASX runs, and the private compiler log is retired. Startup failure leaves no error text in the post-return terminal snapshot;
EXECUTE failure leaves the normal inline error. That is a snapshot observation,
not proof that startup displayed no message before returning. The parent has
separate adopted-renderer and ordinary PROGRAM paths, including an acknowledged
error prompt. An added timer scan did not establish pre-return prompt visibility;
its zero observation is not proof of absence. The diagnostic records
`startup_error_retained_after_return=false` and leaves prompt visibility open.
Both source cases retain `compatibility_accepted=false` because the compiler
cannot start. The reused renderer's startup FINAL FAIL line remains in the log;
it checks retained inline text, not all possible transient error displays.

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD \
  --get-compiler-dir build/GET_COMPILER --source-memory-cases \
  --allocation-probe --output build/FRESH_SOURCE_MEMORY
./tools/dev --command python standalone/prove_get_vm_source.py \
  --parent build/PARENT --parent-profile keymap --child build/GET_CHILD \
  --compiler build/DEFAULT_COMPILER/ASPCOMP.EXE \
  --checks build/FRESH_SOURCE_MEMORY/checks.json --output build/FRESH_REPLAY
```

The isolated source proof reproduces these two expected failures and the
existing27 GET cases, plus compiler/serial/CLI/file/MZ regressions. A diagnostic
PASS means the refusal and its evidence reproduced, not that source compilation
fits. `source_compiler_residency_verified` remains false. The
[receipt](validation/aspect-compiler-memory.json) binds exact identities and limits.
No installed/default application or package changes follow from this checkpoint.

The next implementation target is temporary parent memory sharing during
compiler EXEC, preserving complete capacities and contents. The current link map
places the parent stack and DGROUP below image paragraph4E33. UI storage,
redisplay/snapshots, erase shadow and63,000-byte history occupy the later tail;
the UART receive buffer and script-handoff descriptor are in resident DGROUP.
Existing PROGRAM sizing retains
history through `terminal_far_storage_end`, so that tail cannot simply be
truncated or discarded. The existing `process_loan_begin/end` manages a
rebuildable snapshot/index around PROGRAM execution; it does not back the
complete history/UI tail and must not be reused unmodified for a nested compiler.
A compiler lease must coexist with that outer loan and restore the actual
current MCB allocation without overwriting its bookkeeping. This layout is a
candidate, not an implemented compiler loan.

The implementation must first audit every IRQ/shared-pointer user and link-map
boundary. It can then back the complete eligible tail to reserved storage,
validate the backup, temporarily resize only the checked parent allocation,
execute the compiler while the serial pause/IRQ owner remains intact, restore
the allocation and exact bytes, and only then permit parent rendering. No
stack, history, UI, ring or variable limit should be reduced. Layout changes
must keep every executing instruction, stack and asynchronous data resident.
The parent DGROUP already uses65,520 bytes, so new lease bookkeeping must
remain in explicitly resident far storage rather than growing that near group.
The parent/child bridge needs versioned admission and a bounded owner/token
contract; the compiler must not resize an arbitrary foreign allocation. Startup
compilation occurs before a script header/ordinary renderer adoption, so loan
admission cannot assume that an ASX file or active GET already exists. It must
use the checked parent/child handoff without implicitly adopting a display view.
Source compilation on EXECUTE must retain the interpreter's existing state;
compiling only initial login scripts in a separate process is insufficient.

A new candidate needs successful source-startup and source-EXECUTE tests;
matching these old-build refusal diagnostics alone cannot validate the fix.
Tests must cover byte-exact restoration, DOS allocation/handle ownership,
effective environment, buffered streams, queued serial traffic/flow control,
compiler errors/cancellation and reentry. Admission/backup failures must leave
the parent intact. Restore failures must quarantine access to the loaned tail
and retain recovery evidence rather than silently resume through missing memory.
The startup pre-return error-display path also needs direct tracing before
classifying it as a defect or choosing a parent change.

This plan has not been implemented or physically tested. DOS386/UMB synthetic
serial results do not establish Boca/SPA2102/SynthModem/BBS behavior, ordinary8086
parent capacity, full memory pressure or whole-language/application parity.
