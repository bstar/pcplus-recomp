# Owned native shadow reset

The optional reset composition now performs actual DOS-memory allocation for
the native80/132-column shadow screen and restores its state after selected
synchronous failures. This connects the recovered width adapter, native reset,
geometry and far-fill code to an authored controller in
`src/ui/shadow_owner.c`. It is a component build, separate from the interactive
terminal and Special Edition package.

REA inspection of CS:860F/85FC confirms the far-pointer allocation/free calling
contract. The original allocator walks CRT heap structures; its free entry marks
a heap header. This controller uses owned DOS48h/49h blocks instead. It does not
claim recovery of the original CRT heap implementation. Complete inline REA
evidence is retained locally under `analysis/shadow-allocator-*-20261024.rea.json`;
identifiers and digests are in the [receipt](validation/shadow-reset-owner.json).

## Transaction and measured behavior

Before entering native reset, the controller admits mode3/page0,80 physical
columns,24 logical rows, BIOS cursor output, hidden status, the declared native
near-plane pointers, consistent shadow ownership, IF enabled and DF clear.
Caller DS=SS remains an ABI requirement and is captured in the DOS bootstrap.
Other layouts and a reset entered after shutdown of a still-wide view refuse
before allocation or mutation. A fresh view must be initialized after shutdown.

A guarded snapshot holds the54,784-byte native diagnostic data image,4,000 video
bytes, the old shadow contents and BIOS cursor position/shape. Its largest DOS
block is65,152 bytes including guards. The current6336-byte shadow payload has
its own guarded allocation. Native requests to free old storage are deferred
until reset commits. On typed error, the controller restores the compared data,
video, old shadow and cursor, then releases pending storage. Failed releases
retain their handles for retry. Pending transaction storage, damaged guards or
inconsistent view metadata prevent further reset admission.
`shadow_close` retries owned cleanup; it does not make a closed wide view usable
without initialization. API return values carry admission/cleanup errors;
`shadow_last_error` retains the last native transaction error.

The canonical DOS8086 run passes77 checks:

- Real native wide/narrow resets, same-block reuse, eight repeated wide/narrow
  cycles and successful retries after failures.
- Genuine DOS exhaustion before snapshot allocation and after the snapshot,
  inside the native shadow-allocation path. The latter reaches the real native
  allocation-error callback; the controller restores the saved state.
- Requested post-allocation abandonment, failure after clearing a reused shadow,
  and failure after the native geometry requested old-storage release.
  Independent far buffers compare the complete affected bytes exactly, along
  with pointer/size metadata and BIOS cursor state.
- Foreign-release and reentry refusal, invalid geometry/plane/CGA/width inputs,
  IF-disabled and DF-set entry, without additional allocation.
- Explicitly modeled release refusal and a known injected canary failure retain
  ownership. The fixture repairs only its own known injected guard byte before
  testing cleanup again; this is not arbitrary-corruption recovery.
- All43 controller allocations are released. Two independent comparison buffers
  are also freed, and DOS's largest free block returns exactly to its baseline.

The ordinary controller object also compiles without diagnostic fault hooks.
An empty tree of66 declared source files reproduces the composed executable
byte-for-byte, with originals, old objects and REA databases absent. Both earlier
reset controls remain byte-identical: the ordinary native reset retains47
original comparisons, and the viewport composition retains its ten selected
cursor/reset cases.

## Retained counterexample and reproduction

The expanded pre-fix fixture timed out when it tried reset after freeing a wide
view's storage. Its frozen executable, inputs, bootstrap and committed phase log
are preserved as `shadow-reset-dos-07`. That log ends after the successful cleanup
retry. The next request entered geometry with a wide viewport and no allocation.
The current consistency check returns STATE there, and the fixture verifies
refusal followed by explicit initialization and a successful fresh reset.

Earlier runs remain failed. Their uncommitted host-backed trace files initially
hid progress, prompting unsuccessful startup/performance investigations. DOS
commit after every phase made the actual late failure visible. None of those
timeouts is promoted to a successful workflow. The initial35-check pilot did
not exercise that later shutdown/reuse case.

```sh
./tools/build test-shadow-reset
```

This builds `build/terminal-reset-shadow/RESET.EXE`, runs a fresh DOS test and
reproduces it in a fresh source tree through the pinned Nix toolchain. Allocation
exhaustion and actual DOS calls are distinguished from requested diagnostic
faults in the recorded phase list. No original executable is a build/run input.

The snapshot layout belongs to this native diagnostic. It must not be copied
over the interactive terminal's differently owned data, stack or live UART ring.
Live integration still needs a renderer-specific state schema, far-bank and
memory admission, capture/history and modal UI coordination, source-owned error
presentation, parent/child lifetime checks and BBS width workflows. Arbitrary
asynchronous faults and physical video/modem acceptance remain open. The card
and packaged terminal are unchanged; no full-application gate closes here.
