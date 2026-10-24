# Native viewport panes and data-segment repair

REA recovery now supplies the 75-byte pane-switch group at CS:4816..4861 and
108-byte far-copy routine at CS:644C..64B8. All 183 flat instruction bytes match
the selected original. Relocatable OMF builds use named geometry, video/shadow
pointers and the already recovered CGA blank/unblank helpers.

These services implement horizontal panes over a wider shadow screen. The
copy's low flag bit selects the right offset; bit15 selects shadow-to-video
instead of video-to-shadow. Each row copies the physical column count, then
advances the shadow pointer by the extra logical width. Enter saves the right
pane when needed and restores the left; leave saves the left when needed and
restores the right. The caller, rather than these wrappers, changes active-pane
state and cursor offsets. A logical132-column screen therefore need not be a
physical132-column video mode.

## Observed native bug and maintained repair

The native copy changes DS to video or shadow memory. At64AE it calls the CGA
unblank helper before restoring caller DS. That helper reads the configured
status-port word through DS. A nonzero decoy at the corresponding foreign offset
makes the original emit its mode-control byte to an unrelated port. This was
reproduced both in the source-built native control and in original instruction
replay. It is not a claim about observed physical CGA failure.

`VIEWPORT_PRESERVE_DS` restores SI, DI and caller DS before calling the actual
unblank helper, whose contract preserves those registers. Native flat control
bytes remain unchanged. All160 cases preserve identical video/shadow data
between the control and repaired product; the repaired callbacks always see
caller DS. The native control is not executed in DOS acceptance testing.

The [receipt](validation/viewport-panes.json) records:

- 160 source-only native/maintained cases and160 paired original comparisons,
  covering left/right, both copy directions, ignored flag bits, active-pane
  branches, relocated/nonzero shadow offsets,24/25 rows, CGA-disabled and modeled
  retrace configurations. Exact buffer contents and guards, DS=SS, stack and
  preserved registers verify.
- Six real native cursor transitions through these pane routines and the actual
  hidden-status refresh. Logical cursor, visible column, physical video offset,
  attribute offset and both memory planes verify after each transition.
- Four calls from the recovered width adapter into actual native reset on the
  stable80-column ANSI path. Configuration restoration and real clear/home pass.
  A DEC wide request reaches the explicit860F allocation boundary; its temporary
  setting remains because the native adapter did not return. Allocation and an
  abandonment/unwind owner remain required.
- Two actual DOS8086 maintained far/video copies, plus byte-identical empty-tree
  reproduction of the maintained fixture, native control and reset composition.
  The existing default reset executable matches a build from pre-change sources
  exactly; its47 original comparisons still pass.

The initial decoy fixture used the original CGA-field offset instead of its
relocated offset and failed its expected-port assertion. A later DOS pilot
failed because the far-segment fixture had not explicitly established DS=SS.
Both remain failed and preserved. The corrected fixture follows the actual
symbol offset and sets SS/SP during startup. These are test-fixture corrections,
separate from the native foreign-DS bug and its maintained repair.

## Reproduction and remaining integration

```sh
# Source-only pane checks, real cursor/reset composition, DOS and source rebuild:
./tools/build test-viewport
# Explicit verified original for controlled instruction comparison:
./tools/build test-viewport-compat
```

The optional composition is `standalone/build_terminal_reset.py --viewport`;
the ordinary diagnostic remains byte-identical. Complete inline REA evidence
is retained under ignored `analysis/viewport-*-20261024.rea.json`, with identifiers
and digests in the receipt. Original image identity remains
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Normal builds do not read originals, images or REA databases.

Positive dimensions, clear DF, valid owned buffer extents and nonaliasing remain
caller preconditions. This component does not yet supply allocation, reset-error
rollback or admission to the interactive terminal. Full width integration must
also audit renderer, scroll/erase/attribute planes, capture/history, modal UI and
ownership across external children. Physical CGA behavior, live BBS width changes
and whole-application acceptance remain open. The Special Edition package and
disconnected card were not changed.
