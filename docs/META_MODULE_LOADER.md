# Matched Meta editor disk module

`--meta-editor-module` now builds a source-only parent, `PCMETA.OVL` and its
resident loader. The full parent can execute the loaded editor through a
startup-only diagnostic: load, edit, save, refuse unload while claimed, close,
overwrite the code, reload, and read the saved KEY baseline. This does not yet
add ordinary Alt-M/menu access or commit staged definitions to the live terminal.
No package selector or installed DOS machine was changed.

## Source-linked extraction and composition

`meta_overlay.py` extracts the linked `META_EDITOR_CODE` segment and its declared
MZ relocation words. It removes the source bank from the parent, remaps the
remaining segments/relocations, and patches the loader's 20-byte expected record.
The record identifies version, exact code length, fixup count, CRC32, code/data
segments and the retained arena. No original executable, inferred fixup scan or
runtime allocation is involved. CRC32 identifies matching bytes; it is not an
authentication scheme.

The file is code followed by sorted 16-bit relocation offsets. The parent uses
an executable-sibling lookup for `PCMETA.OVL`, independent of CWD and PCPLUS.
The final map marks `META_EDITOR_CODE` as `OVERLAY`, so the memory verifier does
not misclassify borrowed snapshot storage as resident executable code. Linked
inputs remain ignored `.bin`/map audit artifacts and are not executed.

The existing PCLINE payload must also be rebased when META is extracted. The
extractor updates its declared segment words, parent expectation and checksum.
Both modules target offset 16,384 in the same 63,000-byte arena; they require
exclusive ownership and cannot execute concurrently. Actual Line/Port DOS
regressions pass against the resulting matched pair.

The standalone bank is 21,619 bytes; the full-parent layout is 21,612 bytes because
its object order changes padding. Both have 17 fixups. The caller's Meta state
uses 12,870 bytes below 16,384, and code/fixup staging ends below the saved screen
image at 61,000. These sizes do not prove a safe live-terminal arena handoff.

## Loader contract

The loader and its state live in retained FILE_CODE. It adds no DGROUP storage.
Begin requires a caller-proved exclusive arena grant, validates DS=SS and the
parent load base/PSP relationship, and opens only the matched sibling file.

- Reading: at most 512 bytes per admitted step, with incremental CRC32. EOF is
  checked explicitly; short reads, extra bytes and IO errors refuse entry.
- Verification: the owned descriptor receives exactly one close attempt. CRC
  must match before any fixup or bank entry. Close uncertainty becomes HELD.
- Fixing: at most 32 fixups per step. Bounds, strict non-overlap/order and segment
  overflow/video-memory limits are checked. This phase may be canceled.
- Ready/Active: only fully verified and fixed code can be entered. Release calls
  the bank's pure owner predicate; an active registration refuses unloading.
- HELD: no retry, restart, cancel, entry or release is permitted until DOS exit.
  The handle selector reports whether a close attempt remains, not proof that
  an uncertain kernel descriptor is closed. Editor fatal recovery can likewise
  latch HELD while retaining code/state and callbacks.

Cancel before activation closes an owned file once and discards partial code;
READY/ACTIVE require checked release. The parent still must finish the editor,
copy its proposal, validate/adopt live state and restore its modal frame before
unloading. The loader does not implement those application transactions or the
global file/EXEC admission gate.

## Validation and memory

Both direct-kernel and fault-wrapper DOS8086 diagnostics pass the 3,069-assertion
editor workflow and 68 loader checks. Checks include step admission refusal,
read/fixup cancellation, exact in-memory relocation, code overwrite/reload,
active-lease refusal, clean release and sticky HELD. Counts include individual
bytes/cells and read-loop iterations rather than distinct user scenarios.

An independent Python reconstruction of every patched word matches the entire
loaded code image before entry. Twenty actual DOS refusal cases cover missing,
short, trailing, checksum/foreign files; invalid fixup bounds/order/overlap/
segments; malformed expected headers; read/short-read faults; and close errors
both before and after the real kernel close. Only expected-record metadata is
changed for fixup tests; damaged module code is never executed.

The actual full-parent startup probe passes 19 checks and independently produces
the exact 540-byte synthetic KEY. A competing fixed capture claim invokes the
loaded bank callback and is refused, checking the real resident/bank boundary.
The next loaded instance reads the saved baseline through the resident strict
reader while preserving the supplied unsaved in-memory definitions.

A 733-file isolated source export reproduces both diagnostic EXEs, the parent
probe and all META/PCLINE payloads exactly, then repeats normal workflows,
parent save/read and 20 refusal cases. A separate 725-file source export
reproduces the normal optional parent and both overlays exactly, then passes
four actual DOS Line/Port cases: save, serviced traffic, read-only refusal and
port-busy recovery. No original/private/prior-object/Git inputs are available;
the outer pinned Nix environment supplies tools.

The normal module-enabled parent requires 480,608 retained bytes, versus 479,024
for the unchanged disabled control. Resident code remains 65,024 bytes (512
spare), DGROUP 65,520 (16 spare), FILE_CODE 26,992 and CONFIG_CODE 63,263. Stack,
receive/history, snapshot and other far-storage capacities are unchanged.
The 21 KB payload occupies already-retained borrowed storage rather than a new
permanent allocation. Probe-only code has a separate larger diagnostic build.

The disabled parent still reproduces exactly as
`ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399`.
See [the receipt](validation/meta-module-loader.json). Reproduce with fresh labels:

```sh
./tools/dev --command python3 standalone/build_meta_overlay.py --output build/meta-loader-direct-LABEL
./tools/dev --command python3 standalone/build_meta_overlay.py --faults --output build/meta-loader-fault-LABEL
./tools/dev --command python3 standalone/test_meta_overlay_rejections.py --direct build/meta-loader-direct-LABEL --fault build/meta-loader-fault-LABEL --output build/meta-loader-refusals-LABEL
```

## Application work still required

The startup probe owns unused storage before UART enable and exits immediately;
it is not a normal command or a deployment build. The ordinary module-enabled
parent has no editor entry. Next are exclusive live arena arbitration against
Line/Port/Redisplay/Chat, menu/direct Alt-M, serviced modal/frame/cursor ownership,
internal own-lease IO admission, expected/runtime action-table comparison and
atomic live adoption, then connected Enigma/Synchronet and physical tests.
Original pixel equality, every geometry and full application parity remain open.
