# Checked overlay reads

The opt-in `--checked-io` overlay build rejects incomplete executable-code and
relocation reads. The previous interpreter70f6e1e7 hangs in the owned DOS test
when one loader read reports zero bytes without a DOS error. Normal loader open
and read errors terminate that interpreter with255, after which the full parent
can restore terminal input and its resources. The failed short-read receipt stays
failed; it is not an expected-success test or a hardware observation.

## Maintained adapter and startup format

`src/aspect/overlay_io.asm` supplies the existing Open Watcom overlay I/O ABI using
DOS open, seek, read and close calls. Open preserves the loader's sharing and
DOS3+ noninheritance policy. Reads retain their requested count and return a
negative tiny-result on a mismatch. The existing loader reports its I/O error and
terminates the script with255; the terminal's ordinary return/revocation path
owns subsequent cleanup. This is maintained toolchain integration, not original
PCPlus code recovered by decompilation.

The pinned Open Watcom source at `bld/wl/ovlldr/c/ovlio.c`, `ovlboth.c` and
`ovlldr.c` establishes this interface and its fatal-error behavior. Its original
code/relocation readers check DOS error status, without comparing returned count.
The linker also uses the reader for the initial far-field/DGROUP preload, which
includes BSS and stack bytes absent from the file. Rejecting every short read
therefore failed startup in the first trial. A disposable trace measured a40688
byte request returning25776 bytes. The initialized prefix is25772 bytes; the
remaining requested memory is uninitialized storage, not missing code.

The final adapter permits that one preload buffer identity at offset0 to end
only after the complete initialized prefix through linker `_edata`. It rejects
an incomplete prefix too. Other code/relocation buffers require exact counts.
The builder checks the far-storage start, BSS boundary, unchanged206-byte field
state and DGROUP/stack layout, and records the preload bounds in its manifest.
No runtime patch, original executable input, smaller buffer or limit is used.

## Current identities and tests

- Unchanged parent: a0e1b082; disabled interpreter:70f6e1e7, byte-identical to the
  preceding build. Enabled interpreter:668e9722.
- Enabled near code64548, DGROUP40464, stack8192 and all bank sizes are unchanged.
  Exact DOS minimum is125392 bytes,48 above the disabled build; page rounding is
  recorded separately and is not a runtime heap claim.
- CLI help, argument refusal and a script pass from both C: and D: (30 checks).
- Five full-parent cases pass201 checks: ordinary execution, startup open error,
  RUN-time read error, RUN-time zero-byte read, and a missing initial data prefix.
  Tests inject one owned DOS refusal/report; no actual card/media fault is claimed.
- An isolated1064-file source export reproduces all eight selected products and
  replays four loader cases (161 checks), two compilation/GET cases and the
  combined Help case. The additional initial-prefix refusal passes outside that export.
- Source startup/EXECUTE compilation and GET pass91 checks; the combined nested
  DOS-child/held-FILE/Help workload passes63, including frame guards and release.

The observer separately records lease ownership immediately after child EXEC
return and at the first parent exit. Fatal RUN return leaves ownership2 before
parent revocation, then ownership/snapshot/attachment are all0 at parent exit.
Normal return still requires balanced child begin/end. Parent mouse/menu action,
keyboard, JFT, sink owners, configuration, UART restoration and hangup are checked.
The first-parent-exit sample is frozen so a later collector reusing the same PSP
cannot overwrite it. These results do not claim graceful interpreter cleanup or
flushing its buffered FILE streams after the loader's fatal termination.

[The validation record](validation/aspect-overlay-io.json) binds exact hashes,
source/fixture identities, positive and negative receipts and source replay.

## Remaining scope

This is an experimental profile. Nonzero partial reads, relocation-specific and
seek failures, same-parent script relaunch after a loader failure, complete stream
lifetime/error composition and broader input/error interleavings remain open.
Full-profile Help RPC faults also remain open. The prior Enigma/Synchronet results
apply to70f6e1e7;668e9722 needs its own BBS and complete connection-package checks.
No installed selector, card, private settings/history, live bridge or workstation
network changed. Physical Boca/SPA2102/SIP acceptance, full ASPECT and other
original feature parity remain unverified. Host remains last.
