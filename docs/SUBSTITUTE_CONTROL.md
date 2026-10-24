# SUB control and interrupted peer requests

The recovered SUB provider fixes a real DOS failure in the profile 4 path.
Previously, SUB inside a partial `ESC[?3` reached the unsupported 1248 boundary
and terminated the ASPECT child with error 3. The same source-compiled,
windowed case now handles SUB, resynchronizes on the following ESC, completes
a fresh width request and returns to keyboard/serial processing.

## Native evidence

Original SHA256: `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
The resident 1248..127c span contains 53 bytes at file offset 2448h, SHA256
`5b2571477ed4c15ca96375422965c8eef406e476e4d62ec6a3d03ca5c8eaaa6b`.
The explicit analyst comparison checks every byte. Ordinary builds assemble
the source and verify its recorded size/digest without reading an original
executable or analysis database.

REA dossier: `ev_569fc63c4a44ed77abaf3a0282ecdf4f47fc71a15851e3c4e72dcaa2db68f520`.
Ghidra did not discover the indirect-table target in the original import.
A static-only copy changes just header IP/CS to 1248h/0, preserving all code
bytes; its SHA256 is
`89b73614735f46dabb0554fece9afde77e4101cc3676227eb9894311c7eadbf8`.
That analysis image is never executed. Ghidra reports 51 body bytes across the
53-byte span because two padding NOPs fall outside its body ranges. Assembly
and exact byte comparison establish the near-call ABI; pseudocode alone does
not establish the original stack layout.

For signed profile values below 20, the provider's branch priority is direct
output → clear the window, mode9026 → cursor up, newline mode9020 → cursor
down, otherwise return unchanged. Up retains native wrapping. Profile values
at least 20 call an unresolved provider with argument 59; that branch remains
explicitly unsupported. Application admission covers profiles 4 and 6.
ASPECT preflight no longer applies CAN's unrelated protocol-edit restrictions
to SUB. MZ/map inspection normalizes four state addresses and four near-call
destinations before verifying the complete native digest.

## Dispatcher semantics and the corrected oracle

The native input dispatcher can render low controls as CP437 glyphs instead
of dispatching their providers. Profile 6's default setting renders SUB and
advances the cursor once; profile 4 defaults to the recovered no-op provider.
Four linked dispatcher cases check both profiles with that setting on and off.
The historical parameter reader processes these controls without independently
abandoning the partial CSI. The subsequent ESC performs resynchronization.
These tests do not claim that CAN/SUB alone cancel an ANSI sequence.

The source-02 campaign ran the full matrix but failed ten profile 6 assertions
because its fixture incorrectly expected no cursor movement. The corrected
oracle requires exactly `1;17R` for that setting, and `1;16R` for the no-op
path. Application binaries did not change during this correction. The earlier
source-01 run ended with signal 15 before finishing and has no completed receipt.

## Verified source and DOS checkpoint

The [sealed receipt](validation/substitute-control.json) binds 870 declared
source files and 4,172 artifacts. `build/substitute-source-03` starts from a
build-free source tree, reproduces four exact parent products, both unchanged
interpreters, the unchanged DOS compiler and unchanged flat CSI diagnostic.
No original executable, private configuration, disk image or REA database is
a build input. All 177 DOS workflows pass: 101 earlier cases and 76 new
refusal/interruption cases across both profiles, status states, window states,
source/precompiled children and applicable main-loop paths.

Both transaction parents pass 768 SUB branch/geometry cases, five signed
profile cases, four control-glyph dispatcher cases and four foreground UART
interrupt cases retaining all 512 queued bytes. All previous display, field,
scrolling, ownership and IRQ regressions repeat. Expanded pure policy checks
pass 58,978 DOS assertions and 56 independent CPU probes. Compiler and
interpreter stacks and grammar/workspace limits remain unchanged. The full
parent retains 401,488 bytes including its PSP, with 76 resident-code bytes
spare and 1,440 near-data bytes spare.

Rejected children exit 3 with unchanged 80x25 geometry and idle parser/scope/
native-bank owners. RIS restores startup defaults and the diagnostic marker;
a subsequent request produces an exact 132-column cursor reply. The ordinary
fatal-refusal path exits 2 and restores sampled hardware; its discarded parser
frame counter belongs to a terminating process. Only the declared startup
cursor-backend refusal fixture changes a setting. Subsequent observation is
passive; no executable instruction, return value or serial reply is patched.
The compact failure cases do not claim complete screen/metadata snapshots or
forced native-body/output-failure coverage.

The source gate can be reproduced with fresh output names:

```sh
./tools/dev --command python3 standalone/prove_substitute_source.py \
  --output build/substitute-source-NEW --nested
./tools/dev --command python3 standalone/record_substitute.py \
  --proof build/substitute-source-NEW \
  --output docs/validation/substitute-control.json
```

Selected [ENiGMA ASPECT/BBS sessions](../lab/bbs/enigma-aspect-width.md) and
[Synchronet main-loop width navigation](../lab/bbs/synchronet-peer-width.md)
are separate evidence. Stock ENiGMA immediate-forwarding fragmentation still
fails; buffered and explicitly patched-decoder passes retain their own scope.
Active Synchronet/ASPECT width composition, carrier/OS cancellation, unsupported
profiles, broader application families, wide transfers and physical modem/card
acceptance remain open. This source checkpoint is not a card release.
