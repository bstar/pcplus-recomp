# Foreground external-program fault recovery

The experimental ASPECT interpreter now reclaims PROGRAM resources after a
foreground divide fault, native typed abort or direct dispatcher longjmp. A
second script then runs in the same process with the same attached UART and
renderer. The first script's error remains visible to the caller.

The [validation ledger](validation/aspect-unwind.json) records 92 fault-suite
DOS cases, 13 attached-parent regressions and 56 raw regressions: 161 actual DOS
cases. Separate linked policy tests cover 124 modeled inputs. A blank declared
source tree reproduces 27 DOS products. The 20 process/display/serial components
match their independently recorded preceding checkpoint; normal capability6
TERMINAL and 105-slot ASPECT also remain byte-identical. The experimental build
still has 108 slots and a separate capability7 parent. This does not publish
DOS/RUN/SHELL in the normal interpreter or close a whole-application gate.

## Recovery ownership

`external_unwind.asm` records the foreground SS, SP and FLAGS at the near-cdecl
external-command boundary. The application's DS=SS ABI supplies the data segment.
An own-stack INT0 rewrites its interrupt return to the checkpoint trampoline;
IRET restores the interrupted flags before the trampoline restores the saved
C stack and invokes cleanup. Foreign DS is supported. A foreign DOS child's
different stack retains neutral DOS exit12 and never jumps into its parent's
near stack. The native recovered dispatcher owns final nonlocal register
restoration; cleanup does not return to the interrupted C call chain.

The native abort adapter takes the same checkpoint route while an external
operation owns resources. Runtime cleanup/finish also test the checkpoint
before releasing VM strings or closing files, covering a dispatcher longjmp
that bypasses the abort adapter entirely. Recovery marks the checkpoint as
recovering before cleanup; diagnostic fault probes do not fire recursively.
Kernel/BIOS/allocator corruption or a further fault inside cleanup is outside
this proof.

Persistent owner records live outside the VM arena that an environment fallback
may overwrite. Teardown follows the actual ownership dependencies:

1. Restore process PSP, INT0/23/24, native execution words and any borrowed VM
   arena; free tracked near/far process allocations.
2. Reclaim the UART before drawing, restore mode/snapshot/cursor, discard pending
   snapshot storage, and retire PROGRAM ownership. Recovery never enters WAIT.
3. Restore selected private JFT entries before CRT file validation. A partially
   masked or restored table accepts either the owner's FF mask or its saved byte;
   a foreign third value remains an error. Unrelated entries remain untouched.
4. Validate the actual buffered ASX reader and numbered streams, retire the
   stream bracket, and return the actual parent PROGRAM lease.
5. Retire the VM scope only after successful teardown and the final interrupt
   vector check. Failure retains quarantine rather than admitting another script.

A far environment backup becomes valid only after its copy completes. A fault
after allocation but before copying must free that allocation without restoring
uninitialized bytes into the live VM. Display allocation likewise has a pending
owner before the recovered snapshot routine publishes its final pointer.

A retained linked counterexample exposes the final-vector ordering error: END
returned STATE10 but had already cleared the scope, and repair/retry failed.
The corrected actual scope code retains its owner through rejection, then permits
retirement after the vector is repaired. Additional linked cases cover every
partial JFT restoration position and foreign-entry rejection. Failed stream
teardown separately retains scope quarantine.

## Actual DOS execution

The main matrix executes all 22 boundaries with four real failure paths: an
8086 DIV by zero, DIV with foreign DS, the native typed-abort adapter, and a direct
native dispatcher longjmp. These are actual DOS executions using an 8086 CPU,
not modeled successful cleanup calls.

| Phases | Boundary |
| --- | --- |
| 1–4 | VM scope, parent lease, stream bracket, completed JFT fence |
| 5–8 | Saved view, detached UART, process/vector bracket, tracked near allocation |
| 9–12 | Overwritten VM arena, child return, reclaimed UART, entry to WAIT handling |
| 13–16 | Restored view, restored JFT, retired streams, retired parent lease |
| 17–20 | Pending snapshot allocation, partial JFT mask, partial JFT unmask, uninitialized far backup |
| 21–22 | Inside the actual WAIT key helper, inside snapshot restore/free |

That is 88 fault cases. A separate foreign-DS child-divide control proves that
the child's raw exit12 is not mistaken for a parent interpreter fault. Three
additional divide cases cover COM2 with both flow controls at arena overwrite,
COM1 software flow while detached, and COM2 without flow control after child
return. Together these make 92 cases. COM1/HARD carries the full fault matrix;
the separate 13-case parent and 56-case raw regressions cross both ports with
all N/S/H/B policies. This is not an exhaustive fault×port×flow cross-product.

An independent 8086 REP MOVSB snapshots all **15,050 arena bytes** before external
mutation. C `_fmemcmp` checks that independent baseline after recovery. The
8,363/8,364-byte fallback actually exceeds the live frame's 6,944-byte offset;
the overwrite probe observes changed bytes and recovery restores them. The
uninitialized-backup probe observes unchanged bytes and does not copy garbage.

The first invocation opens the actual six numbered streams, with five prefetched
inputs and pending output. The real DOS child checks private handles are absent,
reads the flushed output and changes UART/IRQ/PIC and DOS vectors. After each
fault, the driver checks exact PSP/JFT/INT0/23/24 and all VM/resource owners, then
runs another real script before closing the attached terminal services. That
second script opens all six streams, runs another DOS child, verifies buffered
input/positions, renders a recovery marker and continues serial interaction.
It succeeds while the first invocation still reports DIVIDE12 or typed error5.

The WAIT probes receive no key until the later host schedule. Recovery must
finish in fewer than 36 BIOS ticks, so accidentally waiting during cleanup cannot
pass by consuming that delayed key. Far/near process allocation and display
allocation/free counts balance. The passive parent observer compares **10,276
exact bytes** and retired leases; independent final hardware snapshots and parent
JFT/file-owner comparisons also pass. These checks do not establish physical
modem timing or data retention under arbitrary incoming load.

## Build and repeat

Use the pinned Nix toolchain from the repository root:

```sh
./tools/build test-aspect-external-unwind
./tools/build test-aspect-external-unwind-policy
./tools/build test-aspect-process
./tools/build test-aspect-parent-process
./tools/build test-aspect-external-unwind-source
```

The first command runs the 92 fault-suite cases. Fresh labels retain earlier
attempts. Individual cases accept `--phase`, `--kind`, `--port` and `--flow` in
`standalone/test_aspect_unwind_dos.py`; kind D/A/F/L selects the four failure paths.
The source proof builds the compiler, normal interpreter/terminal, attached
interpreter/terminal, raw diagnostic, fault diagnostic and 20 native components.
It starts without build objects, original executables or REA databases.

The fault diagnostic is `build/aspect-fault/ASPECT.EXE`; it is separate from both
the ordinary experimental child and normal ASPECT. Size optimization `-ob -os`
applies only to the experimental C link. The fault diagnostic nearly fills its
near code segment; its linker map places `_TEXT` at paragraph1 with 65,525 bytes.
The actual DOS proof supports that legal nonzero code base. Earlier overflowing
links are retained and do not count as executions. Normal compiler flags remain
unchanged.

`standalone/record_aspect_unwind.py` checks current source/product hashes against
the accepted runs and fresh rebuild before publishing the ledger. It also
authenticates the preceding source-proof receipt before comparing those 20
component binaries. Earlier successful captures from a different source revision
remain historical, rather than being substituted for current execution.

Remaining requirements include original macro keyboard/mouse/window/error-notice
ownership, broader views, full UI/language coverage, current live ENiGMA and
Synchronet workflows, loaded-input behavior, actual DOS kernels and physical
RS-232 Wi-Fi modem/hardware validation. The separate ENiGMA input-decoder defect
is unchanged by this interpreter work.

The [current source/carrier checkpoint](CURRENT_DOS_CARRIER.md) refreshes stale
helper manifests, fixes the fault diagnostic's five-byte code overflow with an
equivalent interrupt-number table, and validates seventeen ordinary plus five
guarded recovery/control cases. The canonical mouse source-proof Make target
now declares its required diagnostic and reproduces all 31 products without
manual helper preparation. These are separate current-version results; the
older checkpoint's hashes and broader requirements above remain explicit.
