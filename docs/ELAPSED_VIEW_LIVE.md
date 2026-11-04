# Serviced original Elapsed Time window

The optional `--elapsed-view`, with `--call-timer --local-controls
--original-reference`, enables Alt-T, the original Alt-Z Elapsed Time entry and
the command browser's View item. The original39-command reference is retained;
this adds one available command. The current no-directory candidate has15
unavailable original entries. Whole application parity remains unfinished.

The window shows wall time, date, and ELAPSED TIME THIS CALL or LAST CALL using
the [live original timer](CALL_TIMER_LIVE.md). Opening it does not reset the
anchor. As in the recovered149-byte DB04 handler, the caption and date are
selected at entry, elapsed updates stop after disconnect, and one dismissal
key stays local, including Escape, Alt-X, arrow keys or another local command.
A subsequent Alt-X exits normally.

## Display and ownership

The native DS:3294 descriptor specifies rows8..14 and columns25..60. Time is
at row10/column30, date at10/47, the caption at12/27 and duration at12/51. Fresh
REA descriptor Evidence is
`ev_647951e8636fc4ce62d3314f1c35de7ed73c58efafbdc5f91c54ea60f1889053`;
the ten bytes are independently checked against the genuine overlay32 image.
The synthetic overlay analysis MZ is never executed. The maintained blue box,
CP437 border and shadow use these positions; exact original pixel/animation,
international date formats and other display geometries are not established.

This is a serviced state-machine integration of the recovered display contract,
not a claim that DB04's blocking UI helpers are byte-equivalent to this owner.
The exact220-byte timer remains linked unchanged. The existing Redisplay live/
view frames own the screen: received bytes update the live frame underneath,
including text hidden by the box, and native parser replies continue. Opening
waits for parser/other foreground ownership. Clock painting is bounded to once
per18 BIOS ticks; no private4KB screen allocation or XOFF pause is introduced.

The saved cursor and updated live cells are restored before releasing the
window. Connection notices wait until frame ownership is released, using the
shared deferred-notice owner. A lost-carrier notice therefore neither closes
the window prematurely nor captures the box as its own saved underlay. Reopening
after loss displays the frozen LAST CALL duration.

## Validation and candidate

Candidate SHA256:
`340cb4bac4394d946f0bcbb52adacd922d7f8d8fec9665e117ff1f9cd8b95f6d`.
Near data/stack64864, resident code65194 with342 bytes spare. The existing far
frames are reused. A feature-disabled build reproduces the preceding call-timer
candidate2192f454 exactly. A source-matched ASPECT rebuild remains byte-identical
to84160498; an attempted stale-interpreter test was refused before execution.

The [receipt](validation/elapsed-view-live.json) separates:

- 22 linked CPU cases: direct/reference/browser routes, one-key dismissal,
  live parser/CPR and hidden-underlay updates, bounded repaint, carrier loss,
  last-call reopen, parser deferral, unsupported BIOS states and external stop.
- Four actual DOS8086 COM3/IRQ5 workflows: direct, reference, partial parser and
  sustained incoming traffic. A passive BIOS timer observer records actual
  window cells twice. Hidden text survives close, all64 sustained cursor queries
  are answered, and the key never reaches the wire. DOS exit, hardware/PRM and
  binary preservation retain the existing harness gates.
- Six live-clock groups,41 existing Screen Pause cases and five timer-bank far
  fixups with all220 native bytes normalized for declared linkage.
- Fresh owned Enigma multiline/editor and Synchronet ASPECT/editor sessions
  through the installed SynthModem proxy. Independent final-cell/cursor audits,
  call-log and discarded-draft checks remain separate from window tests.

Initial checks exposed a based-pointer conditional that omitted the caption;
an explicit far caption call fixes it. The test fixture was also corrected to
model hardware IRQ input and BIOS tick memory explicitly, and to count all23
caption characters. Failed intermediate builds/results are retained; no gate
was relaxed to accept missing labels, data, replies or restoration.

No live bridge/BBS service is restarted, no package is selected for installation,
and no physical DOS file is changed. [Clean-source/package/SETUP gates](ELAPSED_VIEW_PACKAGE.md) now pass on the
same image. Physical BUSY/reboot and Boca/SPA2102/SIP/audio/flow acceptance
remain open. Other
terminal controls, file/DOS, directory/key tools, Chat, emulations/protocols,
Host and the full original-feature inventory remain in scope.

```sh
./tools/dev --command python standalone/check_elapsed_view_live.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-elapsed-view
./tools/dev --command python standalone/test_elapsed_view_dos.py \
  --terminal build/SELECTED/TERMINAL.EXE --label new-elapsed-dos
```
