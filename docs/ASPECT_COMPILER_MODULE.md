# Compiler bank loading and full-parent admission

The next [compact/retained-arena checkpoint](ASPECT_COMPILER_RETAINED.md)
restores the six ordinary GET cases, but richer cases still fail. It also
validates whole-kernel placement in modeled retained snapshot space. The
2,902-byte layout and failed matrix below remain historical evidence.

The source-linked compiler bank can now be extracted, checked and loaded as
`PCCOMP.OVL`. A complete-parent layout builds and reproduces from735 public
sources. **That layout is not accepted:** its additional resident footprint
causes the existing GET interpreter to fail before reaching the script/field
boundary. No installed build or release selector changes.

This is the next stage of the [backed lease](ASPECT_COMPILER_LEASE.md), not a
replacement definition of full-parent compatibility. The source-startup and
source-EXECUTE gates in [compiler residency](ASPECT_COMPILER_MEMORY.md) stay open.

## Module mechanics

The matched-parent module contains1,792 code bytes and61 declared segment
fixups, for1,914 bytes total. Only MZ relocation words are transformed. The
extractor removes the bank from the permanent executable, rebases resident
references, patches the linked expected size/fixup count/CRC16/target/boundary,
and rebuilds the MZ header/table. Bank start/end are in an explicit linker group;
the entry offset must be zero. Paragraph padding is made explicit in the module.

The parent-only cold loader checks current PSP, MCB ownership/extent, token and
resident phase before loading. It checks exact size/EOF and CRC16, validates all
sorted/nonoverlapping fixups before applying any, and enters banked init only
after success. The caller must already hold the inactive overlay arena. The
loader does not establish that ownership and must not be exposed as a child RPC.
CRC16 detects accidental corruption, not authenticity or malicious code.

The full-parent variant targets a2KB slot at offset14,336 of the existing
redisplay snapshot arena. This overlaps other temporary users by design; runtime
exclusion is still required. It adds no UI/history/ring/variable capacity cuts
and no DGROUP bytes. The extractor also rebases the existing PCLINE/PCMETA module
fixups and their resident expected CRC32/segment metadata in the same operation.
Cross-module pointers into the compiler bank are refused.

| Resident section, including cold loader | Bytes before alignment |
| --- | ---: |
| LEASE_CORE | 1,858 |
| LEASE_IO_CODE | 518 |
| LEASE_STORAGE | 512 |
| LEASE_MODULE_INFO | 14 |
| Total | 2,902 |

The earlier banked core without this loader remains2,241 bytes. The full parent's
observed added footprint is2,912 bytes after alignment; adding a child bridge
would consume more. The bank itself is removed from the permanent footprint.

## Checks and the failed admission gate

The cold-module harness passes all1,416 lease checks and three exact161,152-byte
restorations. Before valid loading it also refuses a missing module and a module
with a changed payload byte. The compiler subsequently overwrites the loaded
bank, and resident restoration/CRC succeeds, including blocked-grow retry and
injected expected-CRC rejection. A33-source cold rebuild reproduces exact
parent/client/compiler/module identities and observations.

The full parent retains65,520-byte DGROUP and existing capacities. A735-source
export without originals, private files, prior objects or ancestor Git reproduces
its executable, PCCOMP/PCLINE/PCMETA modules and memory-layout report exactly.
This is a build/layout result, not runtime compiler admission.

Existing full-parent Line/Port noop and Meta edit tests pass with the rebased
modules and live synthetic serial peer. The six ordinary GET cases fail with
the new parent layout. In the string case:

- Largest free block before ASPECT EXEC is137,440 bytes, down from140,352.
- The child has8,516 paragraphs; environment has73 paragraphs. Its exit probe
  records Watcom errno5 (ENOMEM), near-heap head0 and no script runtime steps,
  file-open or variable allocations. This supports an early initialization
  memory failure; it is not an instruction-level CRT trace.
- The script never reaches GET; expected values and normal field/error outcomes
  do not pass. Passing outer connection/hangup/return checks cannot excuse that.

The parent can still return to keyboard/hangup with hardware/JFT/input files
preserved, but this candidate would regress ordinary precompiled scripts. Keep
`production_bridge_admission=false`, `runtime_arena_ownership_verified=false`
and compatibility unaccepted. Do not promote it or weaken the GET gate.

```sh
# Use the complete keymap recipe flags, plus these opt-in builder flags:
# --aspect-get-display --aspect-get-policy --compiler-lease-module
./tools/dev --command python standalone/test_compiler_lease_dos.py --module \
  --compiler-dir build/GET_COMPILER --output build/FRESH_MODULE
./tools/dev --command python standalone/prove_compiler_lease_source.py \
  --checks build/FRESH_MODULE/result.json --compiler-dir build/GET_COMPILER \
  --output build/FRESH_MODULE_SOURCE
./tools/dev --command python standalone/prove_compiler_lease_parent_layout.py \
  --parent build/FULL_PARENT_LAYOUT --output build/FRESH_LAYOUT_SOURCE
```

The [receipt](validation/aspect-compiler-module.json) binds passed component,
module-rebasing and rebuild evidence alongside the failed six-case application
matrix. DOS execution is8086/FPU-off for the component, DOS386/UMB for full-parent
serial tests, using DOSBox integrated DOS; no physical machine/ATA/modem/BBS test
or booted MS-DOS acceptance follows.

## Next implementation

Reduce the permanent footprint enough to preserve child initialization and
ordinary GET behavior before adding bridge overhead. Cold-only work can reuse
existing checked overlay loading, while the resize/read/CRC boundary must remain
resident. A smaller resident implementation or reuse of existing resident DOS
helpers needs measured maps and the same restoration/failure checks. Do not
increase emulator conventional RAM or shrink user capacities to hide the problem.

Then implement exclusive arena admission, versioned pre-header parent/child
capability, coexistence with outer PROGRAM loans, and positive full-parent source
startup/EXECUTE. Keep the full UART/flow/in-flight, effective environment, streams,
UI/history/overlay, repeated same-child lease, disk/I/O/fatal fault, physical and
whole-parity requirements. Neither a passing component nor reproducing this
negative admission result closes them.
