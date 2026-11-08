# Help after a nested DOS program: remaining capacity gap

The current source-built overlay child822897f0 still has a reproducible Help
capacity gap. Ordinary Help and the previously accepted GET/BBS workflows pass;
adding a successful nested DOS program before the failed PROGRAM/Help sequence
fails Help screen allocation. Holding a script FILE across that sequence makes
the shortage larger. This prevents complete overlay/Help acceptance or package
promotion. No application change from this investigation is retained.

## Handle evidence and passing reference

`notice_close_handles_child.asm` is an owned DOS COM helper. It records its own
first20 JFT entries and its parent's first20 entries, attempts to close only
its own live handles5..19, records the parent table again, appends a72-byte
HANDLES.BIN record, writes SUCCESS.OK and exits. It never edits another PSP/JFT.

The ordinary Help sequence with this helper after Help passes55 checks on the
unchanged parent/interpreter, without video/allocation instrumentation. At the
observed EXEC boundary, parent slot5 is live (SFT3), while child slots5..19 are
all FF. No nonstandard handles were inherited or closed; the parent's table is
unchanged. Full Help/search/cursor/mouse/menu/typing/hangup checks still pass.
This proves the observed handle-isolation boundary. It does not identify a
particular open file by name or prove arbitrary loader I/O-failure recovery.

## Required combined regression: still failing

```sh
./tools/dev --command python standalone/test_notice_help_dos.py \
  --label my-handle-roundtrip \
  --parent-dir build/chat-send-mode-parent-v2-20261108 \
  --child-dir build/early-help-final-overlay-20261108 \
  --help-resource --cpu 386 --close-inherited-handles --handle-roundtrip
```

This required combined workload keeps FILE4/LEASE.DAT open, writes BEFORE|,
runs the helper, attempts an absent program and opens Help, then must run the
helper again and append AFTER. Its complete checks remain unchanged requirements:
two helper records, exact stream contents, Help lifetime/search/restore, resumed
parent input and cleanup. The test currently exits1; the child exits10 after
notice service4/MOUSE_MEMORY, before a Help frame or second helper execution.
The ordinary reference still passes51 checks. The first child reports intact
parent JFT and no inherited nonstandard handles; it is not a handle-close failure.

The same failure occurs with the optional allocation observer absent. The fixed
observer preserves caller IF/carry and records the precise failing DOS request:

| Workload | Requested frame | DOS largest free block | Observed shortfall |
| --- | ---: | ---: | ---: |
| Extra nested program, no held FILE | 252 paragraphs /4032 bytes |244 /3904 bytes |128 bytes |
| Extra nested program, held FILE |252 /4032 bytes |211 /3376 bytes |656 bytes |

`--without-held-stream` is a diagnostic control requiring `--handle-roundtrip`.
It removes exactly the held FILE operations from the same compiled script; it
also fails and is not credited as complete acceptance. Near-heap watermarks
are44444 without the FILE and44972 with it, with nheapbeg40464. The precise live
allocation/fragmentation cause is not yet established; these are measurements,
not proof of a leak or a minimum budget for every script.

## Rejected experiments and next gate

A disposable near-heap shrink experiment lowered curbrk only30 bytes and still
failed the4032-byte frame allocation. It also added code and reduced the largest
free block to195 paragraphs. A separate unused-far-heap release experiment also
failed (210 paragraphs available). Their exact sources and outputs remain in
ignored fixture exports; neither change remains in application/build sources.
The existing process backend's warning about preserving near-heap growth
capacity still applies. No buffer, stack, frame guard, FILE limit or test gate
was reduced to get a pass.

Next work must establish the live allocation/layout budget and fund the complete
combined Help workload, then repeat these cases. Overlay-file open/read failures,
full handle lifetime coverage, complete release/package coverage and physical
Boca/SPA2102/SynthModem/Enigma acceptance remain open. Host remains last.
[The validation record](validation/aspect-help-nested-capacity.json) binds the
passing reference, failing combined/control cases and rejected experiments.
