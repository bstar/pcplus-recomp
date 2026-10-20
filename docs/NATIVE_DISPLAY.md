# Native screen geometry, snapshot and restore

The [validation record](validation/native-display.json) binds310 recovered
bytes to963 CPU cases/963 original comparisons and13,045 actual DOS assertions.
The functions are dependencies of the original PROGRAM controller. They are
not a complete display, WAIT/NOCLEAR or UART handoff controller, and no ASPECT
external-command slot is enabled by this work.

| Native service | Original resident offset | Bytes |
| --- | --- | --- |
| Screen snapshot | 6BBE | 50 |
| Restore and free | 7558 | 49 |
| Geometry/BDA refresh | 6D1A | 176 |
| CGA unblank | 77AE | 15 |
| CGA retrace/blank | 77BE | 20 |

REA/Ghidra evidence identifies the exact function bodies and independent
original-file mappings. The analyst regeneration script pins the original
SHA-256 and reconstructs source with byte-for-byte assembly checks. The committed
assembly and numerical provenance are ordinary build inputs; normal build/test
targets never read the original executable or REA bundle. Analyst steps never
launch a target executable. The optional original comparison emulates only these recovered
instructions, with explicitly modeled BIOS, allocator and port boundaries.

The native geometry routine reads BIOS mode/columns and BDA cursor shape, CRT
base and last-row byte. It retains its original low-byte-only column write,
row29 adapter special case, shared cursor-row overlap and16-bit multiplication.
The CPU oracle covers all row and mode byte values, monochrome/color CRT bases,
legacy mode, snow policy and overflowing geometries. It separately characterizes
odd-byte copy truncation. Those raw behaviors are not claims that every encoded
geometry is a valid hardware view.

The maintained C platform supplies a defined high column byte and admits page0
text views only. It checks the full-width expected byte count against the native
result and32KiB video window. Snapshot allocation uses the real far heap. One
snapshot is owned until matching-geometry restore or explicit discard; restore
executes the original7558 copy/free body. Its native `ret4` ABI is bridged to
the C caller's separate stack arguments, and the C boundary preserves ES.
Allocation failure changes no video memory, repeated capture is BUSY and repeated
restore cannot free twice. Graphics, nonzero active page and an oversized BDA
geometry reject before snapshot allocation. A changed view retains the owned
snapshot until the caller restores a matching mode or discards it, preventing
the native copy count from reading beyond the saved allocation.

Actual8086 DOS tests fill and compare every character/attribute word in40x25,
color80x25, monochrome80x25 and VGA80x50. A separately source-built VIDEO.COM
executes through the real native process backend, switches to graphics mode13
and returns37. The parent rejects mismatched restoration, keeps the allocation,
restores BIOS mode3 and then restores the original cells and frees exactly once.
Another case discards while in graphics mode without writing a text image there.
The diagnostic returns to mode3 before exiting. This tests the snapshot services
under a real child lifetime; it does not implement the missing controller's mode
or font recovery on behalf of the application.

The CGA source retains its actual retrace loop and3DA/3D8 accesses. Declared CPU
port fixtures verify blank/copy/unblank ordering and show that missing retrace
can wait indefinitely. The DOS platform leaves snow control disabled. Physical
CGA timing and broader adapter admission remain unverified, rather than being
represented by a successful no-op hardware service.

```sh
./tools/build test-native-display
# Explicit retained run and evidence publication:
./tools/dev --command python3 standalone/test_native_display_dos.py --label NEW
./tools/dev --command python3 standalone/record_native_display.py --label NEW
```

The Make target runs the source-only CPU check before actual DOS. Analyst-only
`check_native_display.py --original` adds the pinned original comparison;
the recorder's optional `--original-comparison` and `--rea-bundle PATH` bind that
additional evidence without making it an application build requirement.

Remaining [external controller](ASPECT_EXTERNAL.md) work includes production
shared geometry/cursor/renderer state, actual BIOS mode/font restoration,
WAIT input, NOCLEAR policy, serial IRQ/flow handoff, full ASPECT continuation and
lease unwinding, and final runtime publication with BBS/hardware acceptance.
All whole-application gates remain open.
