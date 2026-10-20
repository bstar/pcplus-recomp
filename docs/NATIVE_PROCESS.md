# Native DOS process foundation

The [core validation](validation/native-process.json) retains20 actual8086 DOS
process cases and678 assertions. The [namespace extension](NATIVE_NAMESPACE.md)
now binds2,440 recovered bytes to55 cases/2,053 assertions, adding1,047 exact
bytes for PATH/extension/SYSTEM/access helpers. The component launches
source-owned COM and EXE children, handles native batch/COMSPEC execution and
returns the raw DOS4D termination/exit word. The ASPECT RUN, DOS and SHELL slots
remain unpublished. This component has no display, keyboard or UART controller
and closes no whole-application gate.

`src/process/native_process.c` binds the existing recovered environment/tail,
spawn-extension and EXEC routines to real Watcom near/far allocation, copy and
free functions. It takes a near filename, optional separate tail, current or
explicit near C environment vector, direct/batch kind and required result.
It admits only mode0/P_WAIT, requires DS=SS, rejects arena-overlapping inputs
and result storage, validates native size limits before writes, and checks
busy ownership before touching the supplied result or process state.

The current C `environ` vector supplies inheritance; this avoids accidentally
using the unmodified startup PSP environment after PUTENV. The diagnostic
proves the null-vector inheritance boundary, but full ASPECT PUTENV/external
execution integration remains a separate requirement. Lookup retains native
case-sensitive COMSPEC semantics. Batch admission requires a `.BAT` filename
and a nonempty bounded COMSPEC. Native batch construction retains its recorded
four-character suffix removal; the actual owned batch writes `BATCH.OUT`.
The separate search and SYSTEM APIs now integrate native namespace policies;
their semantics and additional maintained boundaries are in the namespace ledger.

## Ownership and memory

Each native near allocation has an owned-list header and receives four additional zeroed padding bytes.
They define empty-list termination and the optional DOS environment suffix
without depending on uninitialized heap contents. They do not count as native
recovered instruction bytes.

When near allocation fails, the native fallback borrows `runtime_arena`, the
existing0x3aca-byte interpreter arena. Its far allocation is a **backup of live
arena contents**, not the outgoing environment. The maintained adapter allocates
and backs up the padded extent, clears only that backed-up span, lets the native
builder use its paragraph-aligned part, then restores it before returning. The
additional four bytes must fit the arena's capacity; otherwise allocation fails.
The native overlong-tail cleanup passes the arena to near-free; the adapter
recognizes that owner, restores the backup and retires it instead of freeing
the arena. Final cleanup drains any remaining near owners and reports a typed
state failure instead of accepting a native cleanup omission.

The source platform supplies complete DOS EXEC parameter-block/FCB storage,
CS save cells and private CRT state. Its DOS error cell is a full word because
the native builder writes a word; the DOS-version byte is separate and is
checked after every case. The Borland handle-information environment extension
and overlay callback gate are inactive in this source-built component. DOS
inherits the actual handles; six held unbuffered CRT streams retain positions
through every launch and failure. Binding this private state to the existing
production path/environment/VM owners remains required before integration.

The process bracket saves PSP and INT0/23/24, installs a DS-independent child
divide handler, executes the native core and restores all saved vectors/PSP.
The foreign-DS child exits12 through that handler. A child replaces all three
vectors; DOS restores INT23/24 on termination, while the parent bracket restores
the changed INT0. An owned resident child returns0307, demonstrating that the
raw termination byte is preserved. Live near/far guard allocations and the
complete patterned arena remain intact. This is process restoration evidence,
not full ASPECT stream/lease/continuation or physical UART acceptance.

Only unused far-heap storage is released before execution. Open Watcom's
[real-mode startup](https://github.com/open-watcom/open-watcom-v2/blob/master/bld/clib/startup/a/cstrt086.asm)
already releases DOS maxalloc slack. The diagnostic exposed a problem with
calling `_nheapshrink` here: a live far block can prevent near-heap regrowth,
so subsequent `fopen` fails with Watcom ENOMEM while its file exists. The
maintained component retains near-heap capacity. The actual DOS test proves
later file opens work, along with safe failure when a separately owned DOS
allocation consumes all available paragraphs and success after its release.

## Reproduce

```sh
./tools/build native-process
./tools/dev --command python3 standalone/test_native_process_dos.py --label NEW
./tools/dev --command python3 standalone/record_native_process.py --label NEW
```

`./tools/build test-native-process` builds and runs core and namespace executables
with fresh generated labels.
This is an explicit component target, outside the normal application build;
it reads no originals, installations or REA databases. Flat native units must
match the recorded original byte hashes before their OMF objects link. Actual
tests cover command-tail125/126 boundaries, both allocators failing, missing
targets, real DOS memory exhaustion, COM/EXE and batch, near/fallback empty
environments, current C inheritance, foreign DS/division, replaced vectors,
DF/carry changes, raw resident status, six held streams and pointer/busy admission.

Every run retains its executable, manifest and exact authored source snapshot.
The validation record retains three initial failed attempts. The first had an
incorrect vector-mask expectation; the next two exposed the near-heap regrowth
failure. Later successful runs do not relabel those attempts as passing.

Remaining controller work is listed in [ASPECT external commands](ASPECT_EXTERNAL.md):
production integration of the tested namespace policies, shared application state, actual
WAIT/NOCLEAR display/font/cursor handling, UART release/restore, full interpreter
continuation/lease/error paths and final runtime publication with BBS/hardware
acceptance. The standalone process backend is a foundation for those tasks.
