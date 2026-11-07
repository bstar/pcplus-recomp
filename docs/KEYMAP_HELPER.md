# Foreground keyboard-mapping helper

The source-built `PCKEYMAP.EXE` now joins the recovered screen, dispatch,
field editor and binary notation with checked KBD persistence. It accepts the
original caller's profile/filename arguments:

```dos
PCKEYMAP 6 PCPLUS.KBD
```

Profile6 is ANSI. PgUp/PgDn/Space select profiles; the corresponding physical
key selects its definition. Enter accepts a field, Escape cancels it, Tab clears
it and Alt-S saves. Alt-O opens another existing KBD by basename. A dirty exit
or open asks whether to save; Escape cancels that request. About/reserved-key
messages are present. All other profiles, slots and opaque suffix bytes remain
unchanged by a field edit.

The helper's ready screen matches the original blank ANSI screen's full4000
character/attribute bytes in a passive DOS VGA capture. Existing component
proofs cover all65536 dispatch inputs and1246 original field states. The new
[workflow receipt](validation/keymap-helper.json) covers14 actual DOS8086 cases:
ready-screen equivalence, field cancel, explicit save, discard, save on exit,
cancel exit, next/previous profile wrap, opening another file, legacy BIOS
input, long-binding refusal, stage-file conflict and read-only target refusal, and discarding edits before a failed open.
Each case verifies exact files and restoration of all screen/cursor/shape bytes.

Enhanced BIOS reads preserve grey/navigation key identities. The original's
selection and typing normalizers are different; both rules were recovered in
REA and used in the foreground helper. Consequently enhanced grey PgUp selects
its mapping, whereas the legacy PgUp code changes profile. `/LEGACY` as an
optional fourth argument selects classic BIOS reads; that path is tested.
Automatic BIOS capability selection and other hardware keyboards remain open.

The [file diagnostic](validation/kbd-editor-file.json) passes219188 checks,
19 injected save boundaries and eight load cases on full31284-byte synthetic
files. Load requires exact size, terminated slots, EOF and a checked close
before committing any destination bytes. Save compares every old byte, writes
an exclusive same-directory `KBDSTG.$$$`, closes and reads it back, rechecks
the source, moves it to `KBDBAK.$$$`, then installs the stage. Failures roll
back where possible. Uncertain close, failed rollback or retained recovery
causes the foreground helper to exit14 after a visible recovery notice.
Silent stage corruption is detected before either rename. The source-read
counter saturates at65535; the31284-byte write count remains exact.

This is an optimistic DOS/FAT replacement, not power-loss atomicity or external
locking. File timestamps/attributes are not preserved; read-only targets are
refused. Existing recovery files are never overwritten. Factory defaults are
not imported, missing files are not silently created, and ambiguous or expanded
bindings that do not fit the original field remain unchanged and uneditable.

A17-file isolated export reproduces helper SHA256
`0280f9942a5eb9739a28af21405f50ab91be13c2a70b7ac98c5db38fb010ce51`.
The linker reports69584 bytes, with explicit far heap images used for the
baseline and load staging. Open releases the old baseline only after accepting
a filename, uses that memory for transactional load staging, then reconstructs
the baseline from the accepted or retained image. A confirmed No discards edits
at that point; a failed open retains the previous saved file and creates nothing.
This removes a simultaneous third31284-byte allocation. Earlier direct edit/save
worked under the parent while Open failed; the reduced-peak build passes both.
Separate [direct parent](validation/keymap-helper-parent.json) and
[parent Open](validation/keymap-helper-parent-open.json) checks
launch this exact helper through the existing PROGRAM path of the installed
shared parent's exact `5b634d5c…` bytes in DOS8086. It verifies both direct edit/save and opening another file before editing and
saving. Each saves exactly one slot, returns, resumes serial keys and restores
hardware; the open case preserves the first file byte for byte. The runtime is copied to
owned media; private settings and the installed package are not touched.
This demonstrates that this tested parent/helper combination fits and runs;
it is not an Alt-F8 or worst-case fragmented-memory acceptance result.

```sh
./tools/dev --command python standalone/build_keymap_helper.py \
  --output build/keymap-helper
./tools/dev --command python standalone/test_keymap_helper.py \
  --build build/keymap-helper --output build/keymap-helper-workflows
./tools/dev --command python standalone/test_kbd_editor_file.py \
  --output build/kbd-editor-file
```

Original binaries/evidence are absent from all helper build inputs. REA records
for key normalization are retained privately under ignored analysis storage;
original source bytes, private KBDs and factory defaults are not public inputs.
The parent harness's generic raw report calls the deliberately edited SYN.KBD
"changed"; the separate acceptance receipt instead requires the exact intended
four-byte edit and preserves all other file/hardware checks. An early partial
PRM fixture was rejected for invalid mouse scales before connecting; it is not
a child-run result. The accepted fixture supplies valid mouse/display settings.

Remaining gates include dedicated Alt-F8 ownership/admission, matched helper
packaging, strict post-return mapping reload/live publication and parent failure
handling. Full native intro/about/prompt styling, wider DOS filename prompt
characters, new-file/default behavior, monochrome/other geometries and physical
acceptance remain open. Current foreground support requires color80x25 page0;
it does not change video mode. No new parent or helper has been deployed;
RA608E10 remains installed and its pending hardware test is unchanged.
