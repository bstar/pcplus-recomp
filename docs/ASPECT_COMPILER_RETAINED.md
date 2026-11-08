# Compact compiler lease and retained-arena experiment

The next [whole-kernel loader checkpoint](ASPECT_COMPILER_ARENA.md) now loads
this arrangement in the complete parent at startup and restores all27 existing
GET regressions. The compact-resident failures below remain historical; live
source-compiler bridge admission is still open.

The compact resident implementation restores ordinary interpreter startup under
the full parent, but richer scripts still fail for memory. The next experiment
places the entire kernel in modeled existing snapshot space and retains it during
compiler EXEC. That harness runs the real compiler and restores109,792 bytes
without increasing its fixed parent allocation. Production arena ownership,
loading and the child bridge remain unimplemented; no release is promoted.

This advances the [cold-module admission failure](ASPECT_COMPILER_MODULE.md).
The [source compilation](ASPECT_COMPILER_MEMORY.md) and complete application
compatibility gates remain open.

## Smaller resident boundary

The maintained8086 assembly core uses explicit far cdecl entries and saves
BP/BX/CX/DX/SI/DI/DS/ES. It shares MCB and CRC primitives with the C cold loader.
Begin returns from preparation before shrinking. End executes only resident
instructions until regrowth and complete readback/CRC/EOF checks succeed, then
calls bank finalization. Rejection retains invalid status and the private backup.

DOS wrappers share their register-save/restore code. The near setup return is
removed before creating the original far-call frame, preserving stack arguments
and CurrentPDB scoping. AX is the return register; input parameters are on the
stack. The private workspace is256 bytes:128-byte verification scratch shares
space with CWD storage because path construction finishes before verification.
The absolute cleanup name has separate storage. Existing application capacities,
UART buffers, stacks, history and DGROUP sizes are unchanged.

The compact cold-module variant totals2,177 resident bytes before alignment:
CORE1,795 (including256-byte state), IO368 and expected metadata14. Its full
parent adds2,192 bytes after alignment, versus2,912 previously. The component
passes1,416 checks and three exact161,152-byte restorations, missing/corrupt
module refusal and the earlier no-inherit/collision/retry/quarantine cases.
A34-source cold export reproduces exact executables, module and DOS results.
The unbanked regression also passes1,386 checks.

## Full-parent outcome: partial recovery, still unaccepted

The current-source full parent is byte-identical to the tested compact parent,
SHA `e9464f631fc8826469eb6c3a4c881b720de6ce1493f6d6bd20c6a8a05a383544`.
A736-source export reproduces the full layout and all three module files.
Rebased Line/Port noop and Meta edit tests pass with the synthetic serial peer.

All six ordinary GET cases now pass. The largest free block before ASPECT EXEC
is138,160 bytes. The child reaches its512-byte initial near-heap growth and
executes the expected script/field behavior, including typed refusals for the
unsupported float and malformed input cases.

However, both lifetime cases and both WHEN cases fail. The repeated-field and
EXECUTE cases return runtime error8/ENOMEM with native allocation diagnostic101,
two allocation attempts and no script steps. WHEN cases advance into their
scripts but fail with the same heap error. No compatibility gate is relaxed.
The remaining GET suites were not rerun against this already failing candidate.
Passing the six simple cases is insufficient for promotion or bridge admission.

## Retain the kernel inside existing temporary storage

A separate `--retained-arena` fixture places all kernel code/state at and after
image byte360,688, corresponding to the earlier parent's snapshot arena plus
16KB. This is modeled placement using DOS-loaded code and explicit padding;
it is not a production runtime module loader or a proven exclusive arena owner.

The fixed parent remains30,107 paragraphs, and the child remains8,539. The
retained boundary moves to23,245 paragraphs, leaving109,792 bytes for the lease.
The kernel occupies3,361 bytes before alignment:1,792 preparation/finalization
bank,1,187 assembly core/state,368 DOS wrappers and14 metadata bytes. No C cold
loader is compiled into this fixture. Every component instruction/state byte
and stack is mapped below the new cut. The code bank remains owned during EXEC.

Across three actual client invocations,1,416 checks pass:

- ASPCOMP fails without the lease, then runs with109,776 bytes as the largest
  available block and emits byte-exact host-equivalent ASX.
- Each complete109,792-byte tail matches its independent pre-child snapshot.
  The bank prefix stays unchanged during compiler execution.
- A real obstruction causes partial growth to23,758 paragraphs and a retryable
  restore refusal. Freeing it permits recovery. Injected expected-CRC rejection
  keeps RESTORING/invalid and the descriptor until a complete successful retry.
- PSP/MCB ownership, JFT, vectors, no-inherit handles, absolute cleanup and all64
  filename collisions retain their checks.

A34-source cold rebuild reproduces these binaries and observations without
originals/private files/prior objects or ancestor Git. The parent allocation is
unchanged in the fixture, not proof of a zero-overhead production frontend.

```sh
./tools/dev --command python standalone/test_compiler_lease_dos.py \
  --retained-arena --compiler-dir build/GET_COMPILER --output build/FRESH_ARENA
./tools/dev --command python standalone/prove_compiler_lease_source.py \
  --checks build/FRESH_ARENA/result.json --compiler-dir build/GET_COMPILER \
  --output build/FRESH_ARENA_SOURCE
```

The [receipt](validation/aspect-compiler-retained.json) binds both successful
component arrangements, the six passing full-parent cases and four failing
richer cases. Components use8086/FPU-off DOSBox integrated DOS; the full parent
uses DOS386/UMB and a synthetic serial peer. No physical/booted-MS-DOS/BBS or
whole-language/application acceptance is claimed.

## Next integration target

Load the whole lease kernel into the existing inactive arena through a checked
frontend, and retain that arena while lending only the later tail. Reuse existing
loader code where practical instead of adding the whole kernel permanently.
Runtime admission must exclude every other snapshot/Meta/Line/reset user and
retire or reload module pointers safely when the arena changes owners. The
bridge needs versioned pre-header PSP/token/MCB admission, safe parent callbacks,
outer PROGRAM-loan coordination and restore-failure containment.

Then require the full ordinary/lifetime/WHEN/error/storage/width matrix to pass
before positive source-startup/EXECUTE, live UART/flow/in-flight, environment and
stream/UI/history restoration checks. Hardware/package/full-parity gates stay
open. Do not shrink user capacities or increase conventional RAM to obtain a pass.
