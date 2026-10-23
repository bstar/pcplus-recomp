# Owned DOS HOOK exchange

The standalone HOOK owner now allocates a native-shaped exchange block, executes
a source-built DOS helper through the maintained banked EXEC implementation,
collects returned bytes and releases the allocation. It is not yet linked into
the running terminal: KEY kind2 remains unsupported. This extends the
[exchange codec](HOOK_EXCHANGE.md); it does not close a full application gate.

## Ownership and caller contract

`src/process/hook_owner.h` defines an84-byte caller-owned far state. The state
must reside within the retained parent PSP block, including far code storage if
needed. The caller zeroes it before first initialization and supplies trusted
process PSP, minimum and keep-paragraph limits covering every live code, data,
stack and runtime heap allocation. A stack-bound check rejects obvious unsafe
shrinks; it cannot discover all live allocations on the caller's behalf.
Foreground admission requires DS=SS, interrupts enabled and direction flag clear.
External serial, screen, input and file owners must already be suspended safely.

The lifecycle is IDLE → ACQUIRING → READY → EXECUTING → RETURNED → IDLE.
Open allocates133 DOS paragraphs, containing16-byte guards on each side of the
2,094-byte exchange. Its three native far pointers address20 integer bytes,
810 string bytes and1,264 opaque PRM bytes. Guards bind the PSP, generation and
context. Access checks also inspect the allocation's MCB type, parent PSP owner
and exact size, rejecting physical aliases with owner state and output buffers.
These checks detect mistakes and damage; a DOS helper has unrestricted memory
access and is not sandboxed.

Execute reconstructs the bounded native command tail from owned state and uses
the existing `process_run_far` banked EXEC backend. Missing helpers, busy process
ownership and child exit status remain distinguishable. Collection is atomic
staging only: it checks string termination and preserves opaque bytes, without
applying PRM settings. The caller must decide whether to accept a child result
and validate returned settings before changing the application.

Close is idempotent when idle. Failed DOS frees retain ownership for retry.
Damaged guards or MCB ownership reject access and release; the component does
not free a foreign block or silently erase an uncertain owner. Automatic recovery
from arbitrary asynchronous interruption is not implemented.

## Accepted evidence

`./tools/dev --command make test-hook-owner` builds and runs two source-only
8086 DOS fixtures. The accepted runs in
[the independent receipt](validation/hook-owner.json) passed239 diagnostic
checks over25 allocation generations and236 checks over26 generations using
the normal backend without fault-injection controls. Each parent and helper
executable reproduces from a second fresh compilation and link.

The real helper mutates all three banks. Cases cover unterminated returned
strings, guard damage, changed MCB ownership, a nonzero child exit, a missing
helper, actual out-of-memory failure and16 repeated executions. Diagnostics
also exercise injected allocation/resize/free failures. Independent raw-byte
checks verify the returned frame, JFT and FILE preservation, interrupt vectors,
heap and foreign-block canaries, restored largest free block, and rejection of
IF0, DF1 and foreign-DS entry. The production backend contains no test controls.

Earlier fixture attempts exposed incorrect far declarations and a faulty
resident bound: first an address was used instead of the runtime stack limit,
then a live CRT heap buffer was omitted. Accepted fixtures retain the maximum
runtime stack/heap bound, and the backend rejects a bound below the active
stack. These failures and their frozen evidence remain recorded in the receipt.
They reinforce the requirement for a complete caller-supplied resident extent.

## Terminal integration remaining

The directory/ASPECT terminal can now select the shared banked EXEC backend:

```
./tools/dev --command python3 standalone/build_terminal.py --external-render --mouse --notice-sound --notice-input --aspect-keys --directory-keys --process-bank
```

This produces `build/terminal-directory-keys-process-bank/TERMINAL.EXE` with
660 near-code bytes free (594 more than the preceding terminal), unchanged
65,520-byte data/stack usage and a635-byte PROCESS_CODE bank. Its near caller
bridge and far entry share one executor.292 linked binding checks, three DOS
workflows (COM1 keys, COM2 ASPECT/serial return, invalid resource rejection), and
an empty-tree664-source/four-product reproduction pass. The
[receipt](validation/directory-process-bank.json) records raw captures and source
custody. This variant does not enable the separate exit-guard/trap composition,
nor does it install the HOOK owner or accept KEY kind2.

1. Place HOOK state/code without exceeding segment limits, using the now-shared
   banked executor, and reconcile the combined exit-guard/trap lifecycle.
2. Route KEY kind2 and relevant PROGRAM actions through the guarded foreground
   handoff, preserving UART, screen, input, file and exit-guard ownership.
3. Establish native register-bank lifetime and ASPECT child handback. Fresh zero
   banks per invocation are not established as native behavior.
4. Project the actual active PRM state, including directory/session overrides,
   then validate and transactionally apply supported returned settings.
5. Test terminal helper success, rejection, failure, repeated execution and
   serial/display continuation, followed by current ENiGMA/Synchronet sessions.

General asynchronous recovery, other DOS kernels, physical modem integration
and every full application acceptance gate remain open. No BBS or hardware
compatibility claim follows from this standalone checkpoint.

[Supported PRM projection](PRM_PROJECTION.md) now stages explicit active serial,
modem and transfer settings over an opaque baseline with2,660 DOS checks and
an exact complete-image oracle. It is not yet bound to terminal capture and
does not cover all native fields; item4 remains open.

[Shared terminal capture](SESSION_CAPTURE.md) now supplies the live setup path
and a separate session policy. It captures actual runtime fields, but inactive
modem groups and divergent shared fields need explicit projection policy before
the HOOK owner can consume it. KEY kind2 remains disabled.
