# Application trap ownership

The opt-in `terminal-traps` and `terminal-traps-mouse` products install owned
INT1B/23/24 handlers before configuration and UART acquisition. They use the
banked EXEC backend and final-exit allocation guard. Normal publication is
still open; these are source-built DOS applications, not a complete PCPlus
replacement.

Handlers only record cancellation. Foreground polling requests shutdown with
exit16, after which normal UART/file/mouse cleanup runs before restoring the
captured vectors and break flag. Handlers accept foreign DS/SS interrupt frames
without DOS calls. The critical-error handler returns Fail only when AH bit3
permits it. Otherwise it holds execution rather than letting DOS Abort free
live callbacks. DOS3 or later is required.

The parent disables extended DOS break checking while it owns the terminal;
normal BIOS keyboard handling retains responsibility for transmitting control
characters. Before every maintained EXEC, the owner restores its captured
caller vectors and break flag. After EXEC the backend restores DS/SS/SP under
CLI, reinstalls owned handlers before enabling interrupts or calling DOS, and
restores the parent PSP and protected break policy. Child changes are never
adopted as the caller baseline. This policy deliberately changes what an
observer should expect from a child that retains its own INT1B handler.

Normal close restores the captured baseline. An unknown current trap vector
causes quarantine without invoking it or making DOS calls through it. The
final-exit guard retains the validated current allocation with DOS31/error15.
The quarantine path can leave extended break checking disabled; it does not
promise normal restoration after unknown ownership. Failed mouse restoration
uses the same allocation validation, with error14. No automatic unloading of
retained callbacks is provided.

The [hash-bound receipt](validation/terminal-traps-dos.json) records:

- 20 actual8086 DOS cases: keyboard/mouse, initial break0/1, normal exit,
  explicit synthetic INT1B, kernel-delivered Ctrl-C through DOS08, synthetic
  critical-error Fail, and foreign-vector quarantine. A raw startup child
  observes the suspended baseline, changes all three traps and its exit PSP
  vectors, then returns. The parent must reacquire ownership. The independent
  C parent checks kernel return status, restoration and retained ISR survival
  after allocating and overwriting the largest free block.
- An independent auditor decodes the raw62-byte parent and22-byte child
  witnesses and checks frozen source/product hashes. Kernel Ctrl-C records
  pending1 and DOS08 returns byte03 after the handler's IRET on the tested
  DOSBox-X kernel. Earlier failed status-call and following-key assertions
  remain in ignored attempt history.
- Linked instruction checks with modeled DOS version/PSP/break services:
  both break settings, invalid admission, foreign interrupt frames, all three
  quarantine vectors, self-baseline rejection, IF0/foreign-PSP return, pending
  child rejection and reentry. Unfailable critical-error holding is modeled.
- 26 existing attached ASPECT workflows pass1166 checks. Four mouse workflows
  cover PROGRAM, startup repair, live settings and retained callback shutdown.
- A fresh tree containing only declared source inputs reproduces18 products:
  twelve trap applications/probes and six unchanged controls. No original
  executable, installed configuration, REA database or prior object is copied.

Actual device critical errors, other DOS kernels, physical UART/modem behavior
and full Synchronet/ENiGMA acceptance remain separate. The trap-aware retained
ASPECT retry observer is still needed: a retained child's known ISR can remain
valid even though the application has restored the caller's baseline vector.
The current adapter explicitly rejects `--traps --exit-probe`; existing
untrapped retry evidence does not prove this new policy.

The keyboard/mouse near-code spare is686/536 bytes; DS=SS spare is672/640.
The process bank grows to676 bytes. All linked code banks contribute to the
retained minimum and retain the checked near/far EXEC bridge.

Use the pinned Nix toolchain:

```sh
./tools/build terminal-traps
./tools/build test-terminal-traps
./tools/build test-terminal-traps-ui
./tools/build test-terminal-traps-source
```

Each DOS test uses a fresh label. The independent receipt can be regenerated
against the recorded local evidence with:

```sh
./tools/dev --command python standalone/audit_terminal_traps_dos.py \
  trap-matrix-keyboard-01 trap-matrix-mouse-01 \
  --normal-keyboard traps-normal-kbd-01 --normal-mouse traps-normal-mouse-01 \
  --mouse-owners traps-mouse-owners-01 --source-label traps-source-01 \
  --output docs/validation/terminal-traps-dos.json
```

The Fail permission follows the
[INT24 reference](https://fd.lod.bz/rbil/interrup/dos_kernel/24.html).
The tested character-read result is evidence for the pinned DOSBox-X kernel,
not a cross-kernel return-value guarantee.
