# Application trap ownership

The [booted-kernel follow-up](KERNEL_CRITICAL.md) validates actual FreeDOS
write-protection critical errors during capture creation and buffered append/
close. The four writable/protected controls preserve the existing error
precedence and application hashes; other DOS/kernel/device paths remain open.

The [foreground cancellation follow-up](TERMINAL_CANCEL.md) adds checked dialog
key waits and polls the trap flag in serial-only and transfer service paths.
Its30 actual DOS cancellation cases include accepted partial-transfer cleanup
and the separate script error-return wait.
Shared epilogues preserve the earlier retained allocation floors; the process
bank is now661 bytes. See that follow-up for current sizes and BBS results.

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

The [trap-aware retry receipt](validation/terminal-trap-retry.json) adds16
COM/flow routes and1056 checks. A passive32-byte snapshot records phaseCHILD,
captured/actual1B/23/24 vectors, break flag and child window at the first EXEC.
The second EXEC sees the caller's original INT1B before and after return. The
observer validates the retained MCB and exact linked callback address, then
uses a far call with an interrupt frame to that known ISR; its counter changes
1 to2. Neither callback probe changes the three trap vectors; the surrounding
harness still hooks INT21/1C for observation. The application itself never
calls a retained diagnostic ISR. Two untrapped controls preserve their previous
vector policy and pass126 checks. Rebuilt control binaries retain their hashes;
the initial stale-manifest refusals are preserved separately.

The [stock editor receipt](validation/terminal-trap-editors.json) tests the
keyboard trap-enabled client on COM2/19200/HARD. Synchronet immediate forwarding
passes its12 semantic checks and aborts the draft. ENiGMA with explicit30ms
modem buffering passes seven checks. The matched immediate-forwarding ENiGMA
run emits every measured key but fails Home positioning and Insert/overtype.
Both ENiGMA runs close without saving a post. This preserves the known stock
server packet-fragmentation limitation and does not claim it is fixed.

Actual device critical errors, other DOS kernels, physical UART/modem behavior,
complete BBS workflows and nonlocal application-error recovery remain separate.
The retry proof covers one retained failure and one successful retry, not
unlimited quarantine or reclamation. No full application gate closes.

At the initial trap-owner checkpoint the keyboard/mouse near-code spare
is686/536 bytes; DS=SS spare is672/640. The process bank is676 bytes there.
All linked code banks contribute to the
retained minimum and retain the checked near/far EXEC bridge.

Use the pinned Nix toolchain:

```sh
./tools/build terminal-traps
./tools/build test-terminal-traps
./tools/build test-terminal-traps-ui
./tools/build test-terminal-traps-source
./tools/build test-terminal-traps-retry
```

Each DOS test uses a fresh label. At checkpoint3fbb2e7, the original independent
receipt can be regenerated against its frozen local evidence with:

```sh
./tools/dev --command python standalone/audit_terminal_traps_dos.py \
  trap-matrix-keyboard-01 trap-matrix-mouse-01 \
  --normal-keyboard traps-normal-kbd-01 --normal-mouse traps-normal-mouse-01 \
  --mouse-owners traps-mouse-owners-01 --source-label traps-source-01 \
  --output docs/validation/terminal-traps-dos.json
```

The follow-up retry audit uses the current observer and these frozen labels:

```sh
./tools/dev --command python standalone/record_trap_retry.py \
  --keyboard-label trap-retry-keyboard-01 --mouse-label trap-retry-mouse-01 \
  --keyboard-control trap-retry-untrapped-kbd-02 \
  --mouse-control trap-retry-untrapped-mouse-02 \
  --output docs/validation/terminal-trap-retry.json
./tools/dev --command python lab/bbs/record_trap_editors.py \
  --synchronet traps-synchronet-editor-01 \
  --enigma-buffered traps-enigma-editor-buffered-01 \
  --enigma-immediate traps-enigma-editor-immediate-01 \
  --output docs/validation/terminal-trap-editors.json
```

The editor recorder succeeds when evidence is recorded consistently; inspect
`immediate_ENiGMA_passed`, which is false in this checkpoint. It does not convert
an expected compatibility failure into an application acceptance pass.

The Fail permission follows the
[INT24 reference](https://fd.lod.bz/rbil/interrup/dos_kernel/24.html).
The tested character-read result is evidence for the pinned DOSBox-X kernel,
not a cross-kernel return-value guarantee.
