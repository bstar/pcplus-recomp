# ASPECT rendering over a wide terminal

The later [protected erase checkpoint](PROTECTED_ERASE.md) implements the
protected ED/EL provider that this earlier checkpoint still refused. The
following evidence describes the earlier checkpoint's scope.

The guarded parent renderer now admits 80- or 132-column logical displays,
1–25 content rows and supported field modes. Physical video remains 80 columns.
ASPECT continues to own the serial port while the suspended parent executes its
normal parser through the existing checked resident bridge. This extends the
[serviced local view checkpoint](WIDE_SERVICED_UI.md).

Pane admission requires PROGRAM kind4, an active ASPECT rendering scope, an
attached renderer, an occupied resident bridge, and a hidden script overlay.
Other child programs and visible local overlays cannot acquire pane copying.
The attachment/busy/overlay aliases refer to existing state; they allocate no
new screen or owner buffer. The cooperative script window hides before parser
output and restores its updated underlying frame afterward.

The renderer checks cursor caches, viewport geometry, row bounds and status
ownership instead of requiring a fixed 80×25 screen without field markers.
Double-width lines, vertical/reverse field wrapping and configurations requiring
the missing font provider remain rejected. Protected ED/EL remains unsupported:
a command preflight rejects it before dispatcher homing or display mutation.
The parser and field-aware character/scroll kernels remain the parent owners.
Peer-requested width changes are still disabled.

Width conversion also now projects the separate origin top/bottom margins.
Previously a visible-status conversion from25 startup rows to24 content rows
reset scrolling margins but left the origin bottom at24, outside the content.
The checked projection now contains37 word fields plus its separate erase byte;
it resets both margin pairs while preserving origin mode.

## Current evidence

The [validation receipt](validation/wide-aspect.json) binds a clean, initially
build-free source rebuild at `build/wide-aspect-source-01`. It reproduces four
application products, both ASPECT runners, the DOS compiler and the CSI baseline
without original binaries. These are checkpoint results; release and card
deployment remain separate. Build artifacts stay under ignored `build/` storage.

* `standalone/test_aspect_wide_dos.py` runs an unmodified branded parent and its
  source-built custom-IRQ ASPECT child in DOS8086. A declared startup fixture
  activates explicit width and field modes once. An owned ASPECT script
  receives split CSI through the actual child UART and parent renderer. Eight
  workflows cover24 visible-status and25 hidden-status content rows, with and
  without the cooperative script window, using precompiled scripts and actual
  DOS source compilation. Four precompiled cases use the full-plane observer;
  four source cases use the compact observer to preserve compiler memory.
  In the precompiled cases, complete logical display and both
  metadata planes match a separate normal-parser replay. Source cases require
  exact DOS-compiled ASX, final geometry, replies and successful child return;
  they do not capture complete planes. All cases check root DS=SS and
  subsequent keyboard output.
* `standalone/aspect_wide_watch.asm` passively samples renderer attachment,
  bridge activity and physical overlay visibility after its declared startup
  fixture. Precompiled cases saw 29 attached ticks without a window and 30
  with one; source cases saw 30 and 31 respectively. Window cases recorded
  7–8 overlay ticks, while cases without a window recorded zero.
* The compiled pure policy driver passes54,806 checks, including all25 row
  counts, both panes, status policies, profiles4/6, field-mode combinations and
  protected J/K refusal versus permitted P. Independent relocated CPU probes
  separately exercise wide geometry and command refusal. These tests control
  policy globals; genuine attachment comes from the DOS workflows above.
* The linked pane-ownership guard passes768 controlled read-only states. Only
  the complete ASPECT scope admits; unrelated child kinds, missing lease/bridge
  flags and painted overlays refuse without changing video or field planes.
* The existing actual DOS 80-column ASPECT suite also passes all11 cases,
  including display reset, translation, seven-bit input, atomic mode rejection,
  media-copy rejection, timeout and Escape recovery. Its current run is
  `build/aspect-renderer-dos/wide-policy-regression-01/checks.json`.
* The width transaction model passes25 commits,112 row/margin/save cases,
  20 IRQ/fault rollbacks and63 refusals. Both margin pairs are checked.
* The active-field width model also passes420 conversions,240 native repaints,
  240 post-width character edits,2 private repair IRQ cases and8 rollbacks.
* The standalone CSI baseline remains2018 bytes at
  `3a1524f4c69e7e9da59fd67babc99c94dfdcff097c337dfd79f198705f4535b5`;
  its relocation replay passes at three placements.
* All five ordinary-display nested compiler cases pass: explicit source,
  fallback, chained execution, rejected source and chooser-to-source launch.
  They retain COM/IRQ variation, exact ASX and existing-log collision checks.
  Both transaction parents also repeat the complete prior field/scroll/UI
  regressions, shared-screen ownership checks and eight DOS field/local-view
  workflows. The inspector binds the pre-dispatch guard, three CS-qualified
  lease words and37-field margin projection in the actual linked products.

Current branded parent: `2deab097e860ff53d50d1d8c79c9fac3f7bc9bb5c6d012d04ae7eb81a97e4e60`.
Its minimum retained allocation is403,632 bytes; resident code has282 spare
bytes. Child/compiler binaries were not changed in this checkpoint.

## Remaining acceptance

Peer-requested width changes, missing protected erase/font providers, other
child/UI families, partial-width wrapped scrolling and complete application
parity remain unfinished. Wide source compilation currently has compact
geometry/reply/return observation; full plane snapshots belong to the separate
precompiled cases. Physical modem, adapter and end-to-end BBS interoperability
acceptance remain open. This checkpoint has not been copied to the SD card;
UUID54CC-9C77 was absent when checked.
