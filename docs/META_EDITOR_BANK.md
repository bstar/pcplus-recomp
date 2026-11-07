# Meta editor code bank

The composed editor now runs in a separate `META_EDITOR_CODE` segment with
explicit entry and resident-service adapters. Both a direct DOS-kernel build and
a failure-injection build pass on DOSBox-X's 8086 CPU. This establishes the code
bank ABI; the interactive PCPlus parent still does not load this editor.

The ten editor C units and three product assembly units add **zero DGROUP bytes**.
Their calculated paragraph-aligned payload is **21,475 bytes**. The inspect-only
state remains **12,870 bytes**. A proposed state offset0 and code offset16,384
would end at37,859 within the existing63,000-byte redisplay snapshot, before its
screen image at61,000. This calculation is not a linked-parent capacity or arena
lifetime gate. The diagnostic retains its own state and a deliberate64KiB code
gap; its bank also contains test-only code (23,043 bytes direct,23,795 injected).
No receive, stack, history or directory capacity was reduced.

## ABI and DOS boundaries

`meta_bank_abi.inc` declares nine caller-cleaned entries and fifteen imports.
All calls retain DS=SS. Cross-segment calls use far adapters; internal near calls
stay in their own code segment. The static checker audits every C object's direct
near call/jump against its local labels and linked target segment. Four altered
target mappings are rejected by the same checker without executing invalid code.
Indirect transfers are counted; this checker does not prove callback lifetime.

Watcom far `memcpy` and `memcmp` use four register words and a fifth stack count.
Their targets remove that count with `RET 2`. The resident adapter forwards a
copy, and the bank thunk removes the original. Renamed generic calls also need ES
preserved across CRT services. The diagnostic tests both obligations, including
zero-length and guarded copies, against actual linked routines. These adapters
must not be replaced with unqualified CALL/RET forwarding.

The diagnostic resident helpers compile with `-ecc`. Production adapters must
bind to the parent's actual conventions and code placement, especially its
register-based filesystem helpers. The existing strict KEY reader stays in the
resident segment with its private-read flag; it must not acquire near calls to
bank-owned file hooks. Such a mistaken test-hook binding caused a real failed
bring-up and is now covered by the call audit.

`meta_bank_kernel.asm` supplies near-cdecl INT21 file operations inside the bank:
read-only deny-write/private open with optional O_NOINHERIT, exclusive create,
read/write/close, attributes, non-overwriting rename and delete. Invalid open
modes refuse before DOS. FindFirst/FindNext temporarily select the caller's
43-byte DOS continuation and restore the DTA selected on entry, including error
and exhaustion paths. Tests interleave two searches while protecting a separate
128-byte DTA sentinel. This is ordinary foreground DOS execution, not reentrant
DOS or an external-process lock.

The two KEY scratch-name literals move into code only with `META_EDITOR_BANK`;
far copies avoid introducing22 resident string bytes. The ordinary build remains
byte-for-byte identical to the previously accepted composed controller.

## Validation

- Direct kernel: 166 ABI/file/DTA checks and3,069 composed workflow assertions.
- Fault kernel: the same 166/3,069 checks plus981 assertions retaining a fatal owner
  after an injected close uncertainty. Assertions include individual cells and
  bytes, rather than thousands of distinct user scenarios.
- A 52-file isolated source export:both executables reproduce exactly and all DOS
  checks and direct-call audits repeat. No originals, private files, old objects,
  generated analysis database or ancestor Git is available to that rebuild. The
  outer pinned Nix environment supplies tools.
- Ordinary controller regression: 3,069/981 assertions pass and its EXE remains
  SHA-256`c47b615b04f8a156af4bc5b9840a03179379fd23c00a9bb09f3e0102c58fb862`.

See the [receipt](validation/meta-editor-bank.json). Reproduce with fresh labels:

```sh
./tools/dev --command python3 standalone/build_meta_editor_bank.py --direct --output build/meta-bank-direct-LABEL
./tools/dev --command python3 standalone/build_meta_editor_bank.py --output build/meta-bank-fault-LABEL
./tools/dev --command python3 standalone/prove_meta_editor_bank_source.py --direct build/meta-bank-direct-LABEL --fault build/meta-bank-fault-LABEL --output build/meta-bank-source-LABEL
```

## Next parent integration gates

The parent still needs a matched transient payload/loader, production service
bindings, a proved exclusive empty-snapshot arena lifetime, menu/direct Alt-M,
internal file handoff and atomic live action-table adoption after successful
close. Line/Port and other users of that arena cannot run concurrently with the
editor. A HELD/FATAL owner keeps callbacks into this bank registered: retain both
code and state until DOS exit; never unload or recycle them. Its external EXEC
refusal must not gate its own admitted internal IO into a deadlock.

Full parent memory retention/capacity, UART servicing, same-process modal return,
Enigma/Synchronet regressions and physical acceptance remain open. These bank
checks do not establish loading/unloading, actual VGA integration, connected
latency or original pixel equality. No terminal package, remote service or
installed RCE81708 file changed at this checkpoint.
