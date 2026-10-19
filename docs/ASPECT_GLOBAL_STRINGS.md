# ASPECT global-string primitives

The original loader's allocation and release routines now build from maintained
8086 assembly. These101 bytes match original overlay2 D850..D8B4 inclusive.
They retain native behavior and require read, far-heap and error callbacks.
They do not provide the complete loader, heap/error owner or ASPECT VM.

```sh
./tools/build aspect-globals
./tools/build test-aspect-globals
# Optional private executable comparison:
./tools/build test-aspect-globals-compat
```

`build/aspect-globals/GLOBALS.EXE` has SHA256
`cb96ac730aefadb56b16a25196104d0bad8fc13d44d98a8977c9d4a6c9b67cb1`.
The flat101-byte source has SHA256
`2375d3d0436ed254d52c441682ae07983dcb967c9fe9792bab208c4092890fad`.

## Contracts and verification

The initializer reads AX, stores its complete word as the global-string count,
then calls the heap callback for81 bytes per entry. It stores DX:AX as a far
pointer and zeros only the first byte through LES. The release routine passes
each nonnull pointer to the free callback, in order. Both preserve SI/DI and
require DS=SS. Allocation/free arguments are caller-cleaned; the returning
error callback consumes its101 argument. ES is volatile.

616 CPU scenarios exercise every valid compiler count0..128, distinct far
segments, offset-zero and segment-zero pointers, high offsets, allocation
failure at selected positions, returning versus stopping error callbacks, and
sparse release. Canary bytes and untouched string tails verify the exact write
extent. Every source scenario also passes the optional private native comparison.

The linked8086 DOS diagnostic passes705,369 assertions: counts0..128, table
contents, first-byte initialization, untouched80-byte tails, release ordering,
SI/DI preservation, and selected allocation-failure partial states. Its callbacks
supply an owned pool and explicitly modeled errors. These numerous byte assertions
are not independent application workflows or proof of real heap behavior.

`standalone/record_aspect_globals.py` checks source/evidence hashes and records
`validation/aspect-globals.json`. This executable joins the67-output fresh
original-free build; see `validation/application-components-source-build.json`.
Original binary comparisons remain optional and private.

## Native limitations retained

The loop uses signed JG against the stored word and performs no128-entry bounds
check. EOF FFFF would be negative and skip allocation; a positive255 would
exceed the table. Those malformed paths are documented from instructions and
are not executed in these diagnostics.

Allocation failure stores a null pointer before notifying error101. The real
application error path may perform nonlocal unwinding; the diagnostic separately
models stop-at-error and a returning error callback. It does not establish real
error101 UI, longjmp restoration, rollback or complete partially initialized
resource cleanup. The abort model leaves uninitialized tail entries untouched
and deliberately does not release that tail.

Release leaves pointers and count intact. Repeating release can double-free.
The finished maintained loader still needs an explicit resource owner, checked
header/range handling, initialization tracking and error lifecycle. Do not expose
these native primitives directly to unvalidated files or treat the callback
models as a finished safe allocator.

Retained REA observations:

- D850: `ev_dbc3bcf3bb931cbd0cf28570a05d5156f682cfe62da94105e834a75d5fe3e749`.
- D88E: `ev_a2d880c716be2a76af6e9fe26d4135d05a4ab84aafe2d8240d904763b09c7a53`.

Coordinates and current compiler/header context are in
[ASPECT_DISPATCH.md](ASPECT_DISPATCH.md). F13 remains open, along with every
whole-application gate.
