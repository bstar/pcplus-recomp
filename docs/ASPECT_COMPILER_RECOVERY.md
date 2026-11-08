# Full-parent compiler restore recovery

The next [lifecycle checkpoint](ASPECT_COMPILER_LIFECYCLE.md) verifies restored
backup-unlink failure and repeated compiler leases in one interpreter, using the
same application artifacts. The restore-recovery evidence below keeps its scope.

The experimental compiler bridge now recovers from an injected parent regrow or
restoration-read failure at both source startup and EXECUTE. During failure it
keeps the compiler scope and serial pause, displays its BIOS-only recovery
notice, and waits for a key. After retry it verifies memory, restores the exact
text display and cursor, then resumes the interpreter. No package is promoted.

This advances the [refusal checkpoint](ASPECT_COMPILER_REFUSALS.md). The
[validation record](validation/aspect-compiler-recovery.json) binds exact
artifacts, probes, source closure and scope.

## Injected failures and quarantine evidence

`--source-lease-recovery-cases` runs four cases using the actual full parent and
interpreter. The owned DOS observer injects exactly one failure, authenticated
by the parent PSP/MCB, actual compiler EXEC and caller CS inside the loaded kernel:

* Regrow: AH4A, ES=parent, BX=original full paragraphs, current MCB=retained cut;
  return DOS8/CF without calling the DOS allocation routine.
* Read: AH3F, first4096-byte restoration buffer at parent+keep, DX0, MCB already
  full; return DOS5/CF. Compiler input and unrelated DOS reads are not affected.

The fixture requires the actual BIOS recovery text and five timer ticks of
stable interpreter steps and kernel state before inserting a retry key. It
samples only child/retained data while the tail is invalid. Both paths retain
valid0/busy0, the authenticated owner and child CurrentPDB, compiler scope1,
serial pause1 and live PROGRAM ownership. Regrow holds phase2/MCBkeep; read holds
phase3/MCBfull. The sampled DOS error must match the supplied failure.

The next matching operation must occur after the key. Retry uses the real DOS
operation and complete kernel CRC/EOF verification. The compiled ASX then runs
GET input, password transmission and cursor replies, with stream cleanup,
parent history/file-owner retention and ordinary terminal keyboard return.
Backing files and compiler log/staging files retire normally.

This tests failed-operation control flow. The regrow failure is synthetic and
does not exercise real DOS partial coalescing or actual memory-pressure failure.
It does not establish repair of corrupt media or an indefinitely repeating fault.

## Display bug found and fixed

The first four tests restored memory successfully, but the BIOS recovery notice
remained on the BBS screen after source EXECUTE. BIOS output bypasses the parent
renderer, so merely restoring its cached state did not remove that text.

After the compiler acquires arena kind4, BEGIN now captures the physical text
frame, cursor position and cursor shape in the first8006 bytes of existing
snapshot storage. The kernel starts at offset16384, so both areas are disjoint
and below the retained cut. END restores the captured display only after the
kernel attests valid memory, before releasing the arena claim. No heap or stack
allocation, UART reset or BBS/parser repaint occurs inside the video copy.

Admission requires BIOS mode3/page0/80 columns with25,28,43 or50 physical rows;
the frame reservation supports8000 cell bytes and6 metadata bytes. These
integration cases verify25 rows. Other rows and physical adapters remain
separate acceptance gates.

Before failure the observer compares every one of the2000 character/attribute
cells with the captured frame. At the child INT0 scope-restore call, after END
and before serial resume, it compares all2000 cells again and verifies BIOS
cursor position/shape and valid memory. Final screen capture must contain no
recovery notice. This catches restoration to an incorrect cached view too.
SETVECT temporarily uses its ISR segment as DS; that probe authenticates the
child SS/PSP instead of requiring the argument DS to equal SS.

## Memory budget and observer correctness

The first display implementation added192 resident bytes and caused the source
EXECUTE case to fail for near heap. The live build now omits unused startup-only
load/init/info/release diagnostic entries. All live context/MCB/IRQ/ownership
checks remain. Startup diagnostics are still available through the separate
arena-probe build, and its actual ten-check load/init/release case passes.
The build rejects combining live bridge and startup-only probe flags.

The final frontend is1206 bytes,36 fewer than before this checkpoint; aligned
parent size decreases32 bytes. DGROUP remains65520 bytes, the child still uses
256-byte heap growth, and all application capacities/history/stacks/UART buffers
remain unchanged. No passing gate is obtained by shrinking limits.

The inherited exit observer previously sampled parent history on the nested
compiler's termination, while that tail was lent. It now counts nested exits
without touching parent history or interpreting compiler data as ASPECT data.
Only the immediate interpreter child produces those probes after restoration.

## Validation and remaining gates

The same final parent passes all four recovery cases, the two normal source
controls, eight refusal cases and27 GET regressions:41 emulator cases. A clean
1,038-file public source export rebuilds the exact parent/child/compiler and three module
files and replays the four recovery, two control and eight refusal cases.
The cold replay compares exact serial bytes, artifacts and invariant probes.
The kernel CRC covers mutable parent data; it is verified within each run, not
required to have the same value across runs.

Restored END cleanup errors, failed BEGIN file operations, repeated/partial
restore faults, corrupt-backup repair and unexpected-child termination still
need full-parent injection. Repeated compilation and shared-arena reuse within
one parent remain open, as do full language/application parity and selected
package compatibility. These tests use an owned emulator peer, not physical
Boca/SPA2102/SynthModem/Enigma or Synchronet acceptance. The selected package,
DOS card, boot configuration, dialing files and call history are unchanged.
