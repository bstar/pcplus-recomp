# Experimental native reset bank in the terminal

The later [live transaction checkpoint](LIVE_RESET_TRANSACTION.md) adds an
explicit checked projection/commit/rollback API. It remains separate from the
cold invocation described below and from normal peer width dispatch. Its new
resident cost reintroduces a compiler heap failure; it is not a deployable build.

The optional `--native-reset-bank` parent links recovered reset code with its
own `nreset_` namespace and DS=SS context. A cold invocation runs native soft
reset for80/132 columns without changing live UART, parser, near data or the
live shadow. It **does not enable peer width requests**: those still stop at
the explicit2A6E boundary. Cold reset changes physical video; the test explicitly
restores the maintained renderer afterward. Projection, commit and display
rollback are not implemented.

## Workspace and ownership

The native image and private stack use59,136 bytes; its shadow uses6,336 bytes.
They borrow65,472 bytes of the already retained65,504-byte far frame containing
the inactive frozen redisplay cache, row index and screen-export snapshot.
No live history ring or root shadow is borrowed. Near offsets are absolute;
the context owner supplies the checked workspace segment. The empty native
data group must not absorb or repack the existing far owners.

Entry refuses active redisplay, pending history export/search, the command menu,
screen snapshot, active/pending PROGRAM, monitor, controller, and active/pending
transfer. These eleven flags are tested separately for refusal before any cache
or video mutation. Reopening redisplay copies live history and rebuilds its
index; a non-mouse linked-parent test verifies that lifecycle after native reset
overwrites the cache. Both parent variants preserve the unused32-byte frame tail.
The MZ/map verifier rejects malformed workspace, stack, shadow and namespace layouts.

The linker includes the transitive native-file dependency closure of the reset
body. Every imported dependency counts, including imports in unexecuted branches.
It does not select code based on observed test coverage. Both selected and omitted
candidate sources are declared inputs because their exports determine that
closure.413 native code/data symbols remain, separate from root symbols.

## Initial conventional-memory failure

The table below records the preceding interpreter. The subsequent
[compact runtime checkpoint](COMPACT_RUNTIME_FORMAT.md) reclaims2,656 interpreter
bytes without reducing its stack or features and passes the four recorded
nested source workflows beneath this same optional terminal. The initial failed
receipt remains historical evidence; it is not the current gate result.

| Parent | Minimum allocated module bytes | Nested source compilation |
| --- | ---: | --- |
| Full guarded branded custom-IRQ control |398,112| Pass |
| Initial separate static bank |470,048| Fail |
| Borrowed workspace, complete diagnostic inventory |404,592| Fail |
| Borrowed workspace, reset dependency closure |403,040| Fail |

Module figures exclude the PSP and separately allocated environment/heap. The
final optional parent adds4,928 module bytes to the control. Removing65,472 bytes
of extra bank storage is necessary but insufficient: on the same DOS8086
COM2/IRQ5 fixture, the control produces exact `LOGON.ASX` and transmits `COMPILED`,
while the optional parent reports ASPECT out-of-memory at step0 and produces
neither. Both resume the parent parser and restore hardware and PRM afterward.
The initial static attempt and source snapshot remain under ignored
`build/native-bank-static-witness`.

A separate real DOS PROGRAM child allocates/fills16KB and verifies retained MCB
bounds, live far-buffer canaries, full native-bank/shadow byte sums, far-code
sums and UI-buffer sums. Passing this proves retention and allocation separation,
**not** enough free memory for nested ASPECT/compiler execution.

The ordinary terminal remains byte-identical at
`01f55dfbf5385136931c96700be3173cf8594be1c17677e9852fb0f1d025e447`.
The optional base parent is
`999a9a329d88317f786ef2a22e7dd94c33bb2c994501b0a9d17cb2892ae74e52`;
the optional guarded branded parent is
`dea8981a81c9d996b77cc8a9bed5166968b945bc9b5d9cbd9d2fce9ca579f17a`.

## Reproduction and next work

Use the pinned Nix environment. Build ordinary and optional base parents:

```sh
./tools/dev --command python3 standalone/build_terminal.py
./tools/dev --command python3 standalone/build_terminal.py --native-reset-bank
```

Build the full optional parent using `standalone.build_guarded_helper.FLAGS` plus
`--hook-lookup --exit-guard --traps --custom-irq --special-edition --native-reset-bank`.
`--native-reset-static` additionally selects the larger static layout as a
regression control, not a deployment option.

`standalone/prove_native_bank_parent_source.py` copies declared sources and test
dependencies into a fresh tree, reproduces all three parents exactly, repeats
both ownership models, and runs the branded DOS allocation child. The first
clean-tree attempt exposed a missing custom-IRQ `irq_policy.h` manifest input;
the builder now declares it. The second reproduced the programs and models,
but DOSBox-X aborted with a buffer-overflow message before startup. No system
core was available. A shorter owned mount directory avoids the suspected host
path-length issue while preserving the exact fresh executable and metadata.
Passing this reproduction does not waive the failed nested-compiler gate.

The accepted clean-tree replay is `build/native-bank-parent-source-03`.
The control/failed comparison is under `build/native-bank-nested/acceptance-control-01`
and `acceptance-experimental-01`. The public
[validation receipt](validation/native-reset-parent.json) binds the source hashes,
three exact products, ownership reports, DOS allocation checks, raw comparison
artifacts and unchanged component binaries. It explicitly records
`accepted_for_deployment: false`; successful isolation is not release acceptance.

The recorded nested compiler admission now passes with the compact interpreter.
Implement explicit renderer/profile projection,
commit and display rollback. Normal width requests must wait for those operations
and local UI/child/scroll/field workflows to compose. Repeat incoming-data/BBS
acceptance afterward. This optional parent is not approved for card deployment;
the tested staged Special Edition and installed card remain separate products.
Physical hardware compatibility remains unverified.
