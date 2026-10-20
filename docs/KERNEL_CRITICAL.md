# Critical errors under a booted DOS kernel

The keyboard terminal now has a real DOS-kernel critical-error validation path.
It boots the official FreeDOS1.4 floppy distribution, whose kernel reports
DOS7.10, inside DOSBox-X. BIOS-backed FAT12 media is mounted writable or
write-protected. File operations reach the kernel and emulated BIOS; no INT24
call or application state is injected by the test.

This checkpoint adds runtime tests and evidence. The application binaries and
trap policy from6148be4 are unchanged. The selected `terminal-traps-probe-0`
product only writes a passive post-cleanup witness; its foreground event probe
is disabled. This is not a claim that the full PCPlus application is complete.

The [independent receipt](validation/kernel-critical.json) accepts all four
combinations, with42 independent DOS-parent assertions:

| Operation | Media | Observed outcome | DOS exit |
|---|---|---|---:|
| New capture | Writable | Creates CRIT.LOG with the exact16-byte body | 0 |
| New capture | Write-protected | Real critical Fail; no target created; complete image preserved | 16 |
| Append capture | Writable | Preserves10-byte seed and appends the exact16-byte body | 0 |
| Append capture | Write-protected | Logical write accepted; close fails; original seed/image preserved | 12 |

Both protected operations record AX3901h/DI0000h in the application's actual
critical handler. AH permits Fail and AL identifies B:. Creation returns file
owner statusCF_OPEN6/DOS5 without acquiring a handle. The append case first
opens successfully and accepts16 bytes through DOS. At close, the checked owner
recordsCF_CLOSE9/DOS6/close_error6, marks the handle uncertain and forbids a
retry. The final snapshot is taken while the PSP/MCB is still owned, after trap
ownership has closed. It is not a read of freed child memory.

Status12 is the established capture-cleanup error. The final trap poll preserves
an existing nonzero error instead of replacing it with16. The initial append
assertion incorrectly assumed every critical event must produce16; the live
final snapshot establishes the close-failure precedence. Neither the application
nor its error policy was changed to make that assertion pass. A successful DOS
write count alone does not prove durable capture; this test checks the close
error and complete resulting media independently. Append rollback on other
partially writable media is not promised.

The independent parent checks raw DOS child status, INT1B/23/24 restoration and
the original extended-break flag. The flag is1 in these FreeDOS runs. Passive
INT1C observation validates the linked handler/PSP/MCB before sampling the
96-byte file owner and screen, and stops sampling released ownership. It makes
no DOS call in the timer and patches no product field. Raw post-cleanup trap,
first-open, final-file and UART/PIC/vector snapshots are decoded by a separate
auditor. Both actual CPR/DA replies and configured modem initialization/dialing
must appear on the wire. Writable controls prove real capture content; protected
controls must preserve the entire1.44MB data image byte-for-byte.

The audit also extracts KERNEL.SYS and FreeCOM from the executed boot images and
compares their hashes with the original distribution. Product/PRM bytes must
remain unchanged. Sources, linked map, manifest and executable are frozen before
execution, with strict current-source checks afterward. Failed timing/compile
attempts remain in ignored history. Early hotkeys arrived during dialing; the
final fixture schedules the capture prompt after the observed connection and
retains command timing and the actual filename screen.

The optional lab uses only tools already in the pinned Nix shell: Open Watcom,
NASM, mtools, Python and DOSBox-X. The official archive URL is
[FD14-FloppyEdition.zip](https://download.freedos.org/1.4/FD14-FloppyEdition.zip),
with SHA256
`45b1fa7c52dd996c3bfa5e352ffcd410781b952a6ad629f15a4c9ec4bbaefc5a`,
as published in the project's
[verification list](https://www.freedos.org/download/verify.txt).
The [download page](https://www.freedos.org/download/) identifies the floppy
edition and supported older CPU families. The lab boots its8086 kernel and uses
the emulator's8086 CPU mode; this does not establish physical timing behavior.
Only owned images under ignored `build/freedos-kernel-lab` are modified. No
mounted CF card, proprietary DOS installation or original PCPlus executable is
used. Distribution/image binaries are not added to Git or ordinary build inputs.

```sh
./tools/build test-kernel-critical
```

Individual repeats can use `--operation create|append`, `--case writable|protected`
and a fresh `--label` through `tools/dev`. The recorded audit is reproducible
against these retained labels:

```sh
./tools/dev --command python standalone/record_kernel_critical.py \
  --label kernel-proof-create-writable-01 \
  --label kernel-proof-create-protected-01 \
  --label kernel-proof-append-writable-01 \
  --label kernel-proof-append-protected-01 \
  --output docs/validation/kernel-critical.json
```

This validates the witness-enabled keyboard parent and selected FreeDOS capture
create/append/close boundaries. Other DOS kernels, real devices, mouse-driver
ownership under a booted kernel, ASPECT/nested PROGRAM critical paths and the
non-Fail critical holding policy remain separate. Complete modern BBS workflows,
physical modem acceptance, normal publication and all whole-application gates
remain open. Existing immediate-forwarding ENiGMA Home/Insert failures are
unaffected by this kernel validation.
