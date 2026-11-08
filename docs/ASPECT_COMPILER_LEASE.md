# Backed parent-memory lease component

The experimental component now lets the real DOS compiler execute with a
profile-sized parent and interpreter allocation by temporarily backing and
releasing a161,152-byte parent region. It restores the exact bytes and allocation
after compiler return. This advances the [measured residency failure](ASPECT_COMPILER_MEMORY.md);
it is not integrated into the production parent/child bridge or deployed.

The component is maintained integration code, not recovered original PCPlus
instructions. It uses no CRT or heap during the lease. C implementation and DOS
wrappers have distinct far code segments, and all state/buffers live in explicit
far storage. Generated-object checks refuse near calls to the far DOS wrappers
or near DGROUP constant references. The calling foreground has DS=SS, IF enabled
and DF clear. The trusted parent initializes its boundary; the integration/linker
must prove that every executing instruction, stack and asynchronous datum stays
below it. Init is not a child bridge operation.

Begin verifies the token, current child PSP, immediate parent link and MCB
identity/extent. It reserves an exclusive no-inherit backing file using an
absolute path, writes the complete region, closes/reopens it, and compares the
entire readback against the still-owned parent bytes before shrinking anything.
The open backup descriptor remains private across compiler EXEC. End regrows the
actual parent block and streams all bytes back, checking CRC16 and exact EOF
before publishing validity. The file is raw backing storage; resident metadata
is required. It is not a persistent restart journal or a DOS security sandbox.

A resize scopes DOS CurrentPDB to the checked parent, then restores the child on
both success and error. This matters because MS-DOS SETBLOCK shares allocator
logic that assigns the arena owner from CurrentPDB. The implementation follows
the public [MS-DOS4 allocator source](https://github.com/microsoft/MS-DOS/blob/main/v4.0/src/DOS/ALLOC.ASM).
It does not write MCB ownership words itself. Failed growth may coalesce a
prefix; a retained lease permits a bounded retry from that intermediate extent.
Any failed end forbids resuming parent-region consumers.

The backing descriptor uses the DOS4 extended-open no-inherit/exclusive mode.
Close-error handling treats a handle as closed rather than risking a later
close of a reused descriptor, consistent with the
[MS-DOS handle implementation](https://github.com/microsoft/MS-DOS/blob/main/v4.0/src/DOS/HANDLE.ASM).
Existing-name attribute preflight avoids the pinned DOSBox-X2026.07.02 extended
open failure path, which opens an existing file and returns error80 without
closing it. The [pinned emulator source](https://github.com/joncampbell123/dosbox-x/blob/dosbox-x-v2026.07.02/src/dos/dos_files.cpp)
shows that path. Exclusive create still
protects the final operation. The component does not patch/update the emulator.
An intervening create race on that old emulator remains outside this check.

## DOS execution evidence

The test uses two real DOS PSPs. The synthetic parent is sized at30,107
paragraphs (481,712 bytes), retains20,035 paragraphs (320,560 bytes), and the
client retains8,539 paragraphs (136,624 bytes). These model the measured profile
allocations; the parent body is a harness, not the production application.

Across three separate client invocations:

- Without a lease, real ASPCOMP EXEC fails with ENOMEM; largest free block is2,704 bytes.
- With the lease, the largest block is161,136 bytes and actual ASPCOMP produces
  ASX byte-identical to host compilation. A separate EXE cannot read the private
  backup descriptor, proving no inheritance in the tested DOS environment.
- A512-paragraph prefix and one-paragraph obstruction force real grow failure.
  The parent reaches an intermediate20,548-paragraph extent, remains owned by
  the parent and invalid for consumers, then recovers after the obstruction is
  freed. Every161,152-byte region matches its independent address/round pattern.
- Working-directory change before end leaves backup cleanup correct. Parent and
  child PSP identity, parent MCB ownership, file tables and INT0/23/24 remain
  correct. A second begin and invalid token/owner are refused.
- All64 candidate names are populated with owned collision fixtures. Begin
  refuses without shrinking, modifying/deleting those files or leaking handles.
  The test verifies every file before removing its own fixtures.

The final matrix passes1,386 client checks. Its per-byte mismatch flag cannot
wrap, and each paragraph's pattern incorporates both segment bytes so repeated
4KB patterns cannot disguise reordered chunks. Backing comparison is exact;
CRC16 is an accidental-corruption check, not an authenticity claim.

```sh
./tools/dev --command python standalone/test_compiler_lease_dos.py \
  --compiler-dir build/GET_COMPILER --output build/FRESH_LEASE
./tools/dev --command python standalone/prove_compiler_lease_source.py \
  --checks build/FRESH_LEASE/result.json --compiler-dir build/GET_COMPILER \
  --output build/FRESH_SOURCE
```

A28-file public-source export, without originals/private files/prior objects or
ancestor Git, reproduces exact parent/client/compiler executables and the DOS
observations. The [receipt](validation/aspect-compiler-lease.json) binds the
sources, maps, results and exploratory failures. Execution uses8086/FPU-off
DOSBox-X integrated DOS, not a booted MS-DOS4 image or physical hardware.

## Production admission remains open

The prototype is not safe to link permanently into the present full parent.
Its code, DOS wrappers and far storage occupy2,263+518+4,352=7,133 bytes before
alignment. The old full-parent/interpreter startup has roughly3KB headroom.
Adding this resident footprint would move the failure earlier, before the
interpreter could ask for a lease. The integration needs a banked implementation
with a small resident resize/restore boundary, not a larger permanent allocation
or reduced history/UI/stack/ring capacities.

The next implementation must audit all production tail consumers and outer
`process_loan_begin/end` bookkeeping, arrange safe code/data residency and
versioned pre-header child admission, and run positive startup/EXECUTE source
compilation under the full parent. Required remaining cases include real UART
and flow/in-flight traffic, files/effective environment, full UI/history/overlay
restoration, disk-full/short-I/O/corruption and restore-fatal containment,
compiler faults/TSRs, repeated same-child leases and reentry. Lower DOS versions
are not admitted by this component. No full-parent, physical modem/BBS, package
promotion or whole-language/application acceptance follows from these results.
