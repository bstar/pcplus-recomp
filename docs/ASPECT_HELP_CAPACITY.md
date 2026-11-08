# Help after a nested DOS program: capacity and sequential snapshot reuse

The previous source-built overlay child822897f0 has a reproducible Help
capacity gap. Ordinary Help and the previously accepted GET/BBS workflows pass;
adding a successful nested DOS program before the failed PROGRAM/Help sequence
fails Help screen allocation. Holding a script FILE across that sequence makes
the shortage larger. This prevents complete overlay/Help acceptance or package
promotion. The initial heap-trimming experiments were discarded. The opt-in fix below now
passes this combined workload; the historical failures remain evidence.

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

## Historical disabled combined regression: failing

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

## Rejected experiments and original next gate

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


## Sequential parent snapshot reuse (2026-11-08)

The opt-in `help_parent_snapshot=True` interpreter uses the existing capability23
snapshot service for the Help frame. `native_program.c` restores and releases the
native program's saved screen before opening its error notice. Help can therefore
borrow that same retained parent buffer afterward. It does not overlap a live
native snapshot or add a parent RPC. The terminal remains byte-identical a0e1b082;
the enabled interpreter is70f6e1e7. Disabling the option reproduces822897f0 exactly.

The4032-byte frame and its32 guard bytes, stack and six512-byte FILE buffers are
unchanged. Valid attached SAVE context uses the existing authenticated snapshot
begin/pointer/end operations. Offline or NOCLEAR contexts retain the private DOS
allocation path. Invalid attached context fails admission. A failed release keeps
its ownership state rather than silently declaring the buffer free.

The combined test now schedules its serial payload after the preliminary helper,
immediately before the absent program, matching the original reference's receive
phase. Previously the extra VM services could consume the WAITFOR marker early.
Distinct BAD1/BAD2/BAD3 markers identify first-child, WAITFOR and second-child
failures. Both nested children and the open FILE remain required. The byte-exact
disabled control still fails frame allocation with this corrected fixture.

Three enabled full-parent DOS386 cases pass:63 checks with allocation/loan
observation,56 without those optional observers, and53 with BIOS-only input.
The read-only timer witness sees the parent snapshot owned while the child's
native display snapshot is released, intact frame guards throughout the visible
Help interval, the pointer within the retained parent MCB, and retirement before
child/parent return. Two source-compiler-loan/GET cases add91 checks. A cold export
of1062 source files, with neither original executables nor ancestor Git, reproduces
all eight selected products and replays those three Help cases (172 checks) and
two compiler/GET cases successfully.

[The snapshot validation record](validation/aspect-help-parent-snapshot.json)
binds identities and receipts. This closes the measured combined capacity case,
not all overlay acceptance. Malformed pointer publication, lease-release refusal,
overlay-file I/O failures, other workload combinations and the fallback contexts
still need explicit coverage for this profile. The prior Enigma/Synchronet receipts
apply to822897f0; new-child BBS and complete package checks remain open. No installed
selector, card, private settings/history, live bridge or workstation network changed.
Physical acceptance and full ASPECT parity remain unverified; Host remains last.


## Failure and bundle follow-up (2026-11-08)

The same70f6e1e7 interpreter passes missing-resource47 and malformed-resource48
full-parent checks, including exact screen restoration and resumed terminal input.
The ten-product schema2 lab bundle passes13 companion integrity/semantic checks.
An isolated1073-file source export reproduces all ten products, replays all five
Help cases (267 checks) and both source-compiler/GET cases. Eight additional
startup/EXECUTE cases reject missing, corrupt or truncated compiler modules and
source syntax errors (352 checks), preserving typed exits and parent return.

`test_help_snapshot_allocator_dos.py` compiles the production `resource_heap.c`
with stub parent/private allocation services and executes it on an8086 DOS CPU.
Its22 assertions exercise refused acquisition, wrong-pointer release, repeated
allocation, release refusal followed by retry, retained ownership after failure,
and choosing the releasing service from the original allocator even if the
context changes. The test fixture uses explicit far NULL returns: Watcom's
conditional near-pointer conversion otherwise produces DS:0, which is not a
far NULL. The initial fixture failures were corrected without changing the
application. This test does not exercise RPC pointer publication, the real parent
refusal path or complete outer unwind; those full-profile fault gates stay open.


The new interpreter also passes the Enigma virtual-carrier/retry test and
Synchronet editor/screen regressions. See the
[integration record](validation/aspect-help-snapshot-integration.json) for their
exact scope and identities. Full connection-release and physical gates stay open.
