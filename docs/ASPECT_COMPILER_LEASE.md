# Backed parent-memory lease component

The next [cold-module/full-parent checkpoint](ASPECT_COMPILER_MODULE.md) loads
this bank successfully in the harness, but finds that the complete parent still
needs a smaller resident footprint to preserve ordinary interpreter startup.

The experimental banked component runs the real DOS compiler with profile-sized
parent/interpreter allocations and restores the exact161,152-byte parent tail.
Its resident footprint is2,241 bytes before alignment, down from the original
7,133-byte component. A1,792-byte temporary code bank lives inside the released
region itself. The compiler overwrites that bank; the resident core restores
and verifies the whole tail before executing the bank again.

This advances the [measured residency failure](ASPECT_COMPILER_MEMORY.md).
It is not integrated into the production parent/child bridge or deployed.
The code is maintained integration code, not recovered PCPlus instructions.

## Residency and transitions

The optional `COMPILER_LEASE_BANKED` build separates three parts:

| Section | Bytes before alignment | Lifetime |
| --- | ---: | --- |
| LEASE_CORE | 1,211 | Resident begin/end/info, identity checks, resize and CRC/readback |
| LEASE_IO_CODE | 518 | Resident far DOS wrappers |
| LEASE_STORAGE | 512 | Resident metadata, absolute path and256-byte readback scratch |
| LEASE_BANK | 1,792 | Trusted init, preparation, backing creation/write/verification and final cleanup |

The unbanked variant remains available and passes its regression matrix.
Banking reduces only this new component's private scratch space; it does not
reduce existing UI/history/stack/UART/variable capacities. It uses no CRT or heap
during the lease, and consumes no new DGROUP state. Far DOS calls are declared
separately; generated-object checks reject accidental near calls, DGROUP
constant references and unexpected external call targets.

The foreground caller has DS=SS, IF enabled and DF clear. The trusted parent
initializes its boundary; init is not a child bridge operation. The integration
must prove that the resident code, storage, stack and asynchronous consumers
remain below that boundary. The bank can be above it only when every reference
to it is excluded while lent or invalid.

1. Resident begin authenticates the token, current child PSP and parent link,
   and refuses active/reentrant leases without calling the bank.
2. Banked preparation checks the MCB, reserves an exclusive no-inherit file
   under an absolute path, writes the complete tail, closes/reopens it, and
   compares every readback byte with the still-owned original. It publishes
   PREPARED and returns completely out of the bank.
3. Resident begin shrinks the checked parent and publishes LENT/invalid. There
   is no surviving bank return address on the execution path after shrinking.
4. Resident end regrows the actual parent allocation, streams all tail bytes
   back and checks CRC16 plus exact EOF. Failure retains invalid state and the
   private descriptor; no bank finalization or tail consumer may run.
5. Only verified restoration publishes valid/CLEANUP and calls the bank to close
   and remove the owned backup. Cleanup failure blocks reuse until retried.

DOS resize scopes CurrentPDB to the checked parent and restores the child on
success and error. The public [MS-DOS4 allocator source](https://github.com/microsoft/MS-DOS/blob/main/v4.0/src/DOS/ALLOC.ASM)
shows why: SETBLOCK shares allocation logic that assigns arena ownership from
CurrentPDB. Failed growth can partially coalesce a prefix. The component retries
from the actual intermediate extent; it never patches MCB ownership directly.

The DOS4 extended-open descriptor is exclusive and no-inherit. Close-error
handling treats the handle as closed to avoid closing a reused descriptor, as
supported by the [MS-DOS handle implementation](https://github.com/microsoft/MS-DOS/blob/main/v4.0/src/DOS/HANDLE.ASM).
Existing-name preflight avoids the pinned DOSBox-X2026.07.02 failure path that
opens an existing file and returns error80 without closing it; see the
[pinned emulator source](https://github.com/joncampbell123/dosbox-x/blob/dosbox-x-v2026.07.02/src/dos/dos_files.cpp).
Final creation remains exclusive. An intervening-create race on that old
emulator is outside this evidence. The emulator/toolchain is not updated here.

## DOS execution evidence

The harness uses real DOS PSPs: parent30,107 paragraphs (481,712 bytes), retained
parent20,035 paragraphs (320,560 bytes), client8,539 paragraphs (136,624 bytes).
These match measured profile allocations; the harness body is not the full app.
Link markers place the actual compiled bank at image byte320,304, precisely the
first released byte after accounting for the PSP. Artificial padding implements
this fixture layout; it is not a proposed production allocation. The map proves
resident sections and callback addresses are below the cut.

Across three separate client invocations,1,416 checks pass:

- Without the lease, actual ASPCOMP EXEC fails with ENOMEM and only2,704 bytes
  available. With it, the largest block is161,136 bytes and the real compiler
  produces ASX byte-identical to host compilation. A bank-prefix comparison
  confirms that compiler execution overwrites the bank.
- A separate EXE cannot read the backup descriptor, establishing no inheritance
  in the tested DOS environment.
- A512-paragraph freed prefix and one-paragraph obstruction cause real grow
  failure, partially expanding the parent to20,548 paragraphs while preserving
  its ownership and invalid status. Freeing the obstruction permits retry.
- A trusted fixture changes the resident expected CRC before restore. End
  rejects the fully read-back tail as corrupt, retains RESTORING/invalid and the
  descriptor, and refuses another begin. Correcting the injected expected-CRC
  fault permits another complete read/verify and cleanup. This tests checksum
  rejection and retry; it does not simulate arbitrary disk/partial-write faults.
- Before each child invocation, an independent snapshot captures every byte of
  the tail, including relocated bank instructions. All161,152 bytes match on
  return in every round. Non-bank bytes use address/round patterns incorporating
  both segment bytes; a latched mismatch flag cannot wrap.
- CWD changes, PSP identity, MCB ownership, JFT entries and INT0/23/24 remain
  correct. Invalid tokens/owners and duplicate begin/end are refused. All64
  existing candidate names remain unchanged with no handle leaks.

```sh
./tools/dev --command python standalone/test_compiler_lease_dos.py --banked \
  --compiler-dir build/GET_COMPILER --output build/FRESH_LEASE
./tools/dev --command python standalone/prove_compiler_lease_source.py \
  --checks build/FRESH_LEASE/result.json --compiler-dir build/GET_COMPILER \
  --output build/FRESH_SOURCE
```

A31-source cold export without originals/private files/prior objects or ancestor
Git reproduces exact parent/client/compiler executables, placement and DOS
observations. The unbanked regression still passes1,386 checks. The
[receipt](validation/aspect-compiler-lease.json) binds current sources/results;
the [previous receipt](validation/aspect-compiler-lease-unbanked.json) preserves
the initial unbanked checkpoint. Execution uses8086/FPU-off DOSBox-X integrated
DOS, not booted MS-DOS or physical hardware.

## Production admission remains open

The small resident component is now implemented, but production bank placement
and bridge admission are not. Its section total excludes linker alignment,
bridge/versioning code and other integration costs; fitting the harness does
not establish complete-parent startup at640KB.

Next audit all production tail consumers and outer `process_loan_begin/end`
bookkeeping, arrange capacity-preserving bank residency and versioned pre-header
child admission, and run positive startup/EXECUTE source compilation under the
full parent. Remaining cases include real UART/flow/in-flight traffic,
files/effective environment, complete UI/history/overlay restoration,
disk-full/short-I/O/actual backup corruption and fatal containment, compiler
faults/TSRs, repeated same-child leases and asynchronous reentry. Lower DOS
versions remain unadmitted. The raw backup needs resident metadata; it is not a
persistent restart journal or a DOS security sandbox. CRC16 checks accidental
corruption, not authenticity. No package promotion, physical modem/BBS or
whole-language/application acceptance follows from these component results.
