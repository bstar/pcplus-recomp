# Read-only internal viewer owner

The [file owner](../src/filesystem/viewer_file.c) now supplies the source-built
read/seek/close prerequisite for the [incremental decoder](FILE_VIEWER_DECODER.md).
The initial [component receipt](validation/viewer-file.json) binds actual DOS,
linked fault injection and a public-source reproduction. The later
[serviced viewer](FILE_VIEWER_UI.md) adds terminal integration, dynamic-reservation
admission and updated owner checks. The physical installation is unchanged.

## File and reservation lifetime

The owner keeps90 bytes of state in FILE_CODE; the initial object occupied1568
bytes, and the dynamic-reservation callback increases it to1640 bytes. Both
emit zero bytes in other object segments. A read-only84-byte
snapshot exposes status, handle number, claim, position and canonical path.
Querying the snapshot does not transfer ownership. Its public interface uses
far cdecl calls with DS=SS, while the small DOS boundary shares FILE_CODE.

A caller supplies a stable non-null near opaque token. The existing capture
validator rejects malformed DOS83 paths, wildcards, devices, traversal and
unbounded strings. DOS6000 canonicalization is mandatory; the absolute result
is normalized, revalidated and reserved before attributes/open. All later path
operations use that admitted absolute name. The shared capture reservation
mechanism rejects both an active writer's alias and a writer attempting to open
or replace the viewer's reserved file. The viewer now uses its dynamic slot,
coexisting with the call log's fixed claim; the original standalone checkpoint
used the fixed slot before that application interaction was exposed.

Directories/volume entries are refused. DOS3DA0 requests read-only access,
deny-write sharing and no inheritance. DOS4400 then rejects a character-device
handle, including a device the earlier name check did not recognize. Sharing
enforcement depends on DOS/SHARE/network support; the in-process reservation
remains necessary. This is not protection against arbitrary namespace changes,
host-mount aliases/hardlinks or external processes bypassing DOS sharing.

Reads accept a disjoint valid far allocation of at most256 bytes. Count zero
does not perform DOS IO. A successful short/zero read publishes the exact count;
position advances by those bytes. On a DOS error, the caller's count remains
unchanged and destination bytes are unspecified. The owner then forbids more
reads/seeks until cleanup. The future decoder controller must feed only
successful reads and retain any read-ahead not consumed at a page boundary.

Absolute seeks support0–7fffffff and verify the returned32-bit position. A DOS
failure or mismatched result poisons further IO, because the actual cursor is
uncertain. Read-position overflow is also rejected without a wrapping counter.
Argument failures preserve state and caller output. Caller allocations must
fit16-bit offsets, stay below1MB and not overlap the owner or count output;
linear-address checks recognize paragraph aliases. Callers remain responsible
for actual allocation ownership and foreground-only invocation.

Cleanup physically closes a known handle once, then releases its reservation.
A failed close retains the handle/claim and quarantines the owner. A failed
release retains the claim even after a successful physical close. Further
open/read/seek/close calls return recovery without repeating those boundaries.
The primary error remains visible alongside the close/release error. There is
no reset that discards unresolved ownership, and this component does not yet
provide an application recovery/child-launch policy for it.

## Validation

The following counts describe the initial component checkpoint. The later
[UI receipt](validation/viewer-ui.json) repeats the owner with902 actual DOS
checks (including fixed-claim coexistence) and25 updated linked cases.

- 897 actual DOS checks execute with8086/FPU-off DOSBox: binary reads into a
  far allocation, seek/read across64KB and at69,696, short/zero EOF reads,
  read-only files, CWD changes after open, absent/directory/invalid targets,
  capture/viewer mutual exclusion, replacement refusal and100close/reopen
  cycles. Both file payloads remain byte-identical and the original C: CWD is
  restored. DOSBox's expected attribute sidecar and readonly host mode are
  checked explicitly on the generated fixture.
- 25 cases execute the actual linked owner, capture validator/reservation and
  assembly boundary with modeled DOS responses. They cover canonical/attribute/
  open/device/read/seek/close errors, invalid handles, invalid device classes,
  impossible read counts, wrong seek positions, primary+secondary failures,
  reservation contention, exactly-once cleanup and retained quarantine. Far
  spans, aliases, output preservation, busy-guard refusal, DS=SS/BP/SI/DI and
  cdecl return are checked. The open mode is asserted as3DA0. These are injected
  errors, not observed physical disk or SHARE failures.
- A fresh export of the14 declared public source/header/Python inputs reproduces
  `VIEWFILE.EXE` byte-for-byte without originals, configuration, REA databases
  or previous objects.

Earlier fixtures are retained but not counted: one compared a stale snapshot
after closing an idle owner; two outer verifiers rejected DOSBox attribute
metadata after the DOS diagnostic itself passed. The corrected fresh run
requires all original897 checks, unchanged payloads and exact expected metadata.
No owner or DOS-open policy was relaxed to obtain those passes.

Reproduce with fresh output paths:

```sh
./tools/dev --command python standalone/build_viewer_file.py \
  --output build/viewer-file-new
./tools/dev --command python standalone/test_viewer_file_dos.py \
  --program build/viewer-file-new/VIEWFILE.EXE --output build/viewer-file-dos-new
./tools/dev --command python standalone/check_viewer_file_linked.py \
  --program build/viewer-file-new/VIEWFILE.EXE --output build/viewer-file-linked-new
```

## Remaining composition

The [paging controller](FILE_VIEWER_SESSION.md) now composes the owner/decoder
with bounded read-ahead and cached/rescanned checkpoints. Next comes the
serviced foreground UI, original footer/frame/cursor behavior and Alt-V.
Child/exit admission must recognize a pending/uncertain viewer owner before
this is enabled. Validate live UART/parser service, capture/HOLD/printing,
Enigma/Synchronet editor return, cancellation, disconnect/reconnect, transfers
and DOS/media errors. Configured external viewer, DOS6.22/SHARE and physical
Boca/SPA2102/SynthModem acceptance stay open alongside full original parity.
