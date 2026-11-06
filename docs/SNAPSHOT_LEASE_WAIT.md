# PROGRAM WAIT with borrowed screen storage

The unchanged capability18 parent `61757956` and normal ASPECT `b61f3a03`
pass two repeated graphics-child SAVE/WAIT calls per terminal session, continued
with Space or Escape. Escape is a normal “any key” response here; these runs do
not claim ASPECT script cancellation.

Four actual DOS workflows pass: normal8086 Space and Escape without the passive
observer, plus separate386/XMS/UMB Space and Escape runs with the observer.
After each first WAIT, six simultaneous file streams and missing-file recovery
complete. The second nested graphics child also returns through WAIT, followed
by normal keyboard transmission and hangup. The final1920-cell viewport is
exact, staged/private inputs are unchanged and the42-byte UART/PIC/vector
snapshot is restored.

The observed runs add an optional INT16 hook to the existing exit observer.
It accepts only AH=0 blocking reads from DS=SS matching the attached ASPECT
child, with `native_program_waiting=1`. It reads the actual parent/child fields
before chaining to the original BIOS and records the returned key. It supplies
no key, alters no product field and makes no DOS requests inside the hook.
Both reads in each run show:

- Parent PROGRAM owner2 and snapshot owner1.
- Child display/program/wait owners1, serial active1 and detached0.
- Exact BIOS key3920h for Space or011Bh for Escape.

Every ASPECT invocation exits with zero error, cleanup error, external scope
and display/program/process ownership. The observer raises memory usage; its
UMB runs do not establish normal8086 memory capacity. The separate unobserved
8086 runs cover actual operation without that observer.

The assembled keyboard observer passes28 modeled predecessor/ABI cases across
DF/CF combinations: matched input, another BIOS function, no attachment,
another child, foreign stack, inactive WAIT and a full record buffer. Register
and key forwarding, bounded writes and read-only product fields are checked.
The existing INT21 observer retains its36 passing ABI/filter cases. These
component checks are separate from actual DOS execution.

Reproduce with fresh output directories:

```sh
./tools/dev --command python standalone/test_aspect_heap_startup_dos.py \
  --terminal build/terminal-lease18-final-20261106/TERMINAL.EXE \
  --runner build/aspect-lease18-unwind-disabled-20261106/ASPECT.EXE \
  --nested-program --nested-graphics --nested-wait escape \
  --cpu 8086 --output build/wait-repeat
```

For passive telemetry add `--exit-watch --exit-watch-high --cpu 386` in place
of `--cpu 8086`. `--nested-wait space` selects the other tested key. Exact
receipts and hashes are in
[`validation/snapshot-lease-wait.json`](validation/snapshot-lease-wait.json).

This is no production application change or deployment. WAIT transport errors,
script cancellation, larger-row WAIT composition, current-pair carrier-loss
regressions and physical modem acceptance remain open.
