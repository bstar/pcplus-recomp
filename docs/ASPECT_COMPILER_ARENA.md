# Whole compiler kernel in the parent arena

The complete lease kernel is now a source-linked cold module instead of a large
permanent addition to the parent. All27 existing full-parent GET regressions pass
again, including the lifetime/WHEN cases that failed with the resident kernel.
A parent-only startup probe loads, initializes, releases and reloads the actual
module. Missing/corrupt/short files and malformed relocation tables are refused
before initialization. This fixes the measured co-residency regression, not the
still-unimplemented live source-compiler bridge. No release is promoted.

This advances the [retained-arena experiment](ASPECT_COMPILER_RETAINED.md).
Full-parent source startup/EXECUTE and the remaining application/hardware gates
are still open.

## Module and small permanent frontend

`--compiler-lease-arena` builds the whole self-contained kernel as `PCCOMP.OVL`:
3,376 payload bytes and73 two-byte segment fixups,3,522 file bytes total. Code and
state target existing snapshot space at offset16,384. The frontend uses the
existing shared loader's bounded reads, CRC32, close and relocation machinery.
The module is a matched-parent product; CRC32 checks corruption, not authenticity.
It imports no segment outside its own extracted span and uses no CRT/DGROUP data.

The loader retains the existing foreground arena owner mechanism. Kind4 marks
the compiler kernel and avoids calling any UI-bank initialization or drawing
function. All instructions/state in this kernel can remain owned during a
compiler lease by placing the retained cut after the payload and fixup table.
The ordinary parent's linked cut is22,827 paragraphs; actual compiler lending
from that parent has not been exercised yet.

Only the frontend stays permanently loaded:698 bytes plus48 added CONFIG bytes,
746 before alignment/752 after alignment. The full parent retains65,520-byte
DGROUP and all existing UI/history/ring/stack/variable capacities. CONFIG remains
within64KB. The largest free block before ASPECT EXEC is139,600 bytes, compared
with140,352 before this frontend and138,160 for the compact resident kernel.

Parent frontend entry points are deliberately restricted to startup: DS=SS must
match the parent's near group, current PSP/MCB ownership must match, the retained
cut must fit, hardware/vector owners must be quiet, and redisplay/menu/live-view
owners must be absent. The shared loader must also be idle and nonfatal. This is
not an admission path for a running ASPECT child or an active serial session.

Load checks the complete file and CRC before publishing readiness. Relocations
must be ordered, nonoverlapping, inside the payload and produce legal real-mode
segments. A partially relocated failure never publishes ready or calls kernel
init. Release clears the arena claim; the public release entry refuses a kernel
reporting an active or invalid lease. Duplicate load refuses without discarding
the current claim. Kernel calls require the loaded state first.

## Relocation correctness

Whole-module extraction removes every component segment and transforms only
MZ-declared segment words, plus the existing module expected metadata. It rebases
PCLINE/PCMETA fixups and CRC32/segment fields as a single matched-parent operation.
All permanent code/state/stack remains below the retained cut.

A real link failure exposed shared AUTO grouping: metadata and resident call-log
storage had the same segment base with different offsets. Rebasing the metadata
would have moved the call-log pointer too. Explicit IO/metadata linker groups
remove that alias; extraction now rejects any resident segment base inside the
removed span. The normal memory inspector then passes its original call-log
queue identity/bounds checks. No bounds check was weakened.

## Execution evidence

The startup diagnostic uses the actual complete parent on8086/FPU-off DOSBox
integrated DOS, before UART start. The valid case records10 checks, idle/valid
kernel state, two loads/initializations/releases and duplicate-load refusal.
Five faults return IO refusal on the first load, before init, with the arena
released: absent file, changed payload byte, truncated file, out-of-range fixup
and a duplicate final fixup. The latter two patch expected CRC only in an owned
diagnostic EXE to reach relocation validation. Failure exit4 adds the parent's
existing generic shutdown notice; the harness checks that exact suffix too.
Same-parent recovery after a damaged-module failure is not established by these
separate launches.

The ordinary parent passes the entire existing27-case GET matrix with the same
GET child/compiler identities:6 ordinary cases including a live stream,2 lifetime,
2 WHEN,2 WHEN errors/cancellation,7 storage and8 width-policy cases. Typed
unsupported/malformed outcomes remain explicit. Rebased Meta edit and Line/Port
noop tests also pass with the synthetic serial peer. These precompiled-script
tests do not call the compiler kernel or establish live arena arbitration.

A737-source export reproduces the normal parent, all three modules and layout.
A742-source diagnostic export additionally repeats all six startup cases and
matches their reports and exact patched/unpatched artifact identities. Neither
export includes originals, private files, prior objects or ancestor Git.

```sh
# Add to the complete keymap recipe and GET display/policy flags:
# --compiler-lease-arena          ordinary experimental parent
# --compiler-lease-arena-probe    startup diagnostic, exits before UART
./tools/dev --command python standalone/test_compiler_overlay_parent_dos.py \
  --terminal build/PROBE/TERMINAL.EXE --case valid --output build/FRESH_PROBE
./tools/dev --command python standalone/prove_compiler_lease_parent_layout.py \
  --parent build/PROBE --startup-checks build/FRESH_PROBE/result.json \
  --output build/FRESH_SOURCE
```

The [receipt](validation/aspect-compiler-arena.json) binds the27 script cases,
startup/fault cases, UI cases and both source rebuilds. Full-parent serial cases
use DOS386/UMB; startup cases use8086/FPU-off integrated DOSBox. No physical
machine/modem/BBS, booted-MS-DOS, deployment or whole-parity claim follows.

## Next gate

Implement versioned pre-header compiler admission through the parent/child
bridge. The startup-only frontend cannot simply be called by a live child:
current PSP/stack, serial quiescence and PROGRAM ownership differ. Audit the
existing renderer capability path before choosing the extension; do not assume
an ASX header or adopted display already exists. Acquire/release the arena only
around compilation, prevent every competing snapshot/Meta/Line/reset consumer,
and retire stale module pointers before reuse.

Init must remain trusted parent work, with precise PSP restoration if scoped;
begin/end must preserve checked child DOS ownership and DS=SS. Coordinate the
outer PROGRAM loan, preserve effective environment/live streams and UART flow/
in-flight traffic, and contain restore failure without repainting through
missing tail memory. Require positive source startup and source EXECUTE under
the complete parent, retain the27 cases and test sustained/reconnect/transfer,
physical-route/package/full-parity gates before promotion.
