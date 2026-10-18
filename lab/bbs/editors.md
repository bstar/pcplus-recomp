# Local full-screen editor probes

These probes enter the actual stock editors on the owned loopback servers with
synthetic accounts. Independent reference peers use **Discard** (ENiGMA) or
**Ctrl-Q Abort** (Synchronet). Current DOS ENiGMA probes close the unsaved
connection. An earlier DOS discard attempt unexpectedly saved a synthetic
local message; that failed test is documented below and retained.
The independent Python peers provide a protocol reference, not a DOS renderer.
All captures and server data stay in ignored `build/bbs-lab/`.

Run the existing servers first, then:

```sh
./tools/bbs-dev --command python3 lab/bbs/editor_probe.py
./tools/bbs-dev --command python3 lab/bbs/synchronet_editor_probe.py
```

ENiGMA commit `6c25317168b762f7d9088a54d3f8295438827a0e`:
`config/menus/loc-message_base.hjson` defines message menu **P** to
`messageBaseNewPost` / `msg_area_post_fse`, To and Subject header fields,
body editor, Escape menu, and Save/Discard/Help/Upload actions.
The lab's copied `loc-` menu files retain those stock editor definitions.
The synthetic user must first select the existing **Lab** conference and
**General** area with J/Enter and C/Enter. Its earlier unset current conference
caused a server-side `hasMessageConfAndAreaWrite` exception on P; the retained
`editor-reference-no-current-area` result records that failed prerequisite.
No DOS compatibility conclusion follows from that server exception.

`core/client.js` decodes CSI1~/2~/3~/4~/5~/6~ into Home/Insert/Delete/End/PageUp/
PageDown; CSI H/F also provide Home/End. `multi_line_edit_text_view.js`
implements the editing operations and Tab/Ctrl-Y. Actual reference output
confirms Home changes cursor column6 to1, End to7, Delete removes the final E,
Insert changes INS to OVR, Tab advances to a tabstop, and Ctrl-Y clears the
line. Escape/Right/Enter returns to `messageBaseMainMenu` through Discard.
The one-line PageUp/Down checks exercise only document boundaries; scrolling
requires a separate multiline fixture.

Synchronet commit `9de2c48d0265b07e1a8406d8a55d31df4fad7ee8`:
`ctrl/xtrn.ini` registers FSEDITOR as `?fseditor %f`;
`exec/fseditor.js` identifies itself as FSEditor v1.105. The synthetic LABUSER
previously used the internal line editor despite the new-user default. Set
its explicit external editor with the stock local `jsexec` User API before
the probe:

```js
var u = new User(system.matchuser('LABUSER')); u.editor = 'FSEDITOR';
```

The initial **Notices** sub-board is SYSOP-post-only; select the existing
local **General** sub-board before P. The probe only advances from Notices
and otherwise requires General, so it cannot accidentally select a network
area. Enter Subject to reach the real full-screen editor. Source maps Home,
End, Delete, Insert, PageUp/Down, Tab, Ctrl-Y and Ctrl-Q; the reference captures
show H inserted at line start, insert toggling Overwrite Mode, and `Aborted.`
after Ctrl-Q. Page keys beep at the one-line document boundaries. The failed
Notices and internal-line-editor prerequisite captures remain retained.

Each result lives under
`build/bbs-lab/results/{enigma,synchronet}/editor-reference/`, with per-step
raw display bytes, complete client/server wire captures, transcript and
semantic audit. A reference pass establishes editor entry/abort and the
captured key responses only. It does not establish DOS input mappings,
physical UART behavior, document scrolling, saving, attachments or transfers.

## Actual DOS baseline: failures retained

Frozen terminal SHA256
`1ddb64bdba5e94b1522cc51898eb8e6a4a4d77256d76a6c01dac287cfa9a9964`
was copied to ignored `build/bbs-lab/editor-binaries/1ddb64bd/TERMINAL.EXE`.
`editor_dos_probe.py` redirects only the maintained harness's executable path,
allowing the original executable to remain immutable while development proceeds.
Both actual editor runs used COM2/19200/8N1/HARD, CTS ready in DOSBox nullmodem.

The corrected `editor-baseline-keys` runs show **Home, End, Insert, Delete,
PageUp and PageDown emitted no serial bytes**. Tab and Ctrl-Y were emitted.
These are failed compatibility results, separate from the earlier menu matrix.

Synchronet reached real FSEditor, then Ctrl-Y caused incoming `ESC[M` (delete
line) to hit explicit unrecovered service **0xdaf2**. Actual linked CPU replay
of the complete incoming serial capture stopped at offset17970 with
`csi_unimplemented_service=0xdaf2`; DOS video says
`Unsupported terminal function; terminal stopped.` Ctrl-Q abort was therefore
never reached. The captured editor had offered recovery of a previous local
unsaved draft; future deterministic probes must clear or explicitly decline that
synthetic draft first. No save action was sent by this run.

ENiGMA reached `messageBaseNewPost` and normal DOS cleanup, but attempting
Escape/Right/Enter **saved the synthetic local KEYTEST message** instead of
Discard. The authoritative server log records UUID
`1f921f8a-1823-5538-8f9f-3a21c7718f28`. Its audit deliberately fails
`no_post_saved`. This happened only on the owned loopback Lab/General board;
there was no public or external message. Preserve the failure evidence. Do not
use an action-menu Enter for further DOS tests until actual key decoding is
verified; close the unsaved connection instead.

The actual server decoder has an independent packet-fragmentation problem.
Run `enigma_fragmentation.py` for a safe unsaved reference comparison. Sending
`ESC[D` in one write moves column6 to5. After End restores column6, sending
Escape, `[` and `D` as separate writes with200ms gaps immediately opens the
editor action menu and does not move the cursor. This matches
`core/client.js` parsing each `data` event without retaining incomplete escapes.
The probe closes without entering any action-menu command; five semantic checks
pass and no message is saved. TCP packet boundaries are not a terminal protocol;
the immediate modem bridge case must remain visible, even if a separately
labelled modem coalescing experiment is added later.

Results and explicit failure audits:

- `build/bbs-lab/results/enigma/editor-baseline-keys/`
- `build/bbs-lab/results/synchronet/editor-baseline-keys/`
- `build/bbs-lab/results/enigma/editor-fragmentation/`

`check_editor_dos.py NAME --label LABEL` audits captured key sequences and editor
state; a normal DOS exit alone cannot pass it. Initial `editor-baseline` and
`editor-baseline-short` experiments used unsupported ADDKEY key names and are
inconclusive harness failures. A dedicated synthetic BIOS key logger proved
that ADDKEY accepts **ins/del/pgup/pgdown**, while **insert/delete/pgdn** silently
stop subsequent queued keys, including Alt-X. The exact verified BIOS values
for `home end ins del pgup pgdown tab c-y a-x` are
`4700 4f00 5200 5300 4900 5100 0f09 1519 2d00`. The immutable-binary adapter now
rejects those invalid aliases and oversized command recipes before launching.

## Final network-policy build

Terminal `84019437bd2342f7053692abc42040ee91f666461f6a3aa51d544763113f2a7b`
was tested from a separate immutable executable copy. It transmits all eight
exercised key bindings. The actual original `0xdaf2` operation is an ANSI
alternate discard-until-Control-N/local-Escape wait, **not** the ordinary delete
line helper. The ordinary original delete/insert helpers are `0xd73c`/`0xd668`.
The maintained default `/A:NETWORK` intentionally maps ANSI CSI M to bounded
region deletion; `/A:ORIGINAL` preserves the alternate operation with a serviced
36-tick deadline. This distinction must not be presented as exact unchanged
original ANSI behavior.

`standalone/check_line_edit_live.py` executes the actual current linked UART,
keyboard, input/CSI dispatcher, line operations, erase and cursor instructions
with hardware-only BIOS video/keyboard/UART/tick models. Eight source-only
synthetic groups pass: NETWORK both profile branches, margins/count clipping/
column preservation, omitted/zero counts, high-bit count bounds, no-op invalid/
protected regions, explicit attribute-repair failure before mutation, original
column-home semantics, serviced alternate wait exits/deadline/wrap/modem-yield,
and wrapper ABI. The optional explicitly selected earlier Synchronet capture
adds a ninth passing group, consuming the complete stream through the former
failure at offset17970. No captured wire or original executable is a default
test input.

Actual Synchronet `editor-network-final` passes **12 semantic checks and eight
wire-key checks**. The response confirms Home inserts H at the line start, End
places E at the end, Delete removes it, Insert toggles Overwrite, Tab advances
to the next stop, page keys beep at the one-line document boundaries, and Ctrl-Y
renders CSI M without aborting. Ctrl-Q reports `Aborted.` and returns to the
main menu. UART/PIC/IRQ restoration and synthetic PRM preservation also pass.
The prior synthetic recovery draft was moved into the baseline evidence folder
before this run. No draft was saved in this run.

Actual ENiGMA `editor-network-immediate` remains a **failed editor interaction**
with the unchanged immediate bridge. All eight expected keys appear correctly
on the DOS serial wire, but the server treats fragmented Home as a literal H,
End as F, Left as D, Delete as `3~`, Insert as `2~`, and page keys as `5~`/`6~`.
Home fails to reposition and Insert never changes to Overwrite. Ctrl-Y clears
the body and the remaining `UNSAVED` text is visible. This run closes the
connection without an editor-menu Enter and the server confirms no new message
was posted. The normal DOS exit and restored hardware do not make editor
compatibility pass. The independent coalesced-versus-split reference probe
continues to identify the server's per-data-event parsing as a separate defect.

```sh
./tools/dev --command python3 standalone/check_line_edit_live.py
# Opt-in ignored local capture:
./tools/dev --command python3 standalone/check_line_edit_live.py \
  --wire build/bbs-lab/results/synchronet/editor-baseline-keys/serial-sent.bin
./tools/dev --command python3 lab/bbs/check_editor_dos.py synchronet \
  --label editor-network-final
./tools/dev --command python3 lab/bbs/check_editor_dos.py enigma \
  --label editor-network-immediate --disconnect-unsaved
```

The ENiGMA audit deliberately exits nonzero. These editor results do not change
the narrower successful login/menu-navigation results, and do not establish
multiline paging, message saving, transfers or physical modem behavior.


## Meta/character checkpoint

`editor-meta-character` repeats both actual DOS editor recipes on frozen
terminal36b14af2. Synchronet passes12 semantic checks and8 key-wire checks,
including Ctrl-Q abort. ENiGMA direct login succeeds and reaches the real editor,
but Home and Insert behavior fail again while all8 key sequences reach wire.
No post was saved. See current `docs/validation/bbs-editors.json` and its retained
previous-runtime cases. The separate current ENiGMA matrix/menu test also fails;
its earlier successful menu tests remain historical evidence only.

## PROGRAM/reset checkpoint

Frozen terminal `7b9ca14b` repeats the real DOS editor checks on COM2/19200/HARD.
`editor-program-reset` passes Synchronet's12 behavior checks and8 wire-key
checks, including Ctrl-Q abort. ENiGMA's initial `editor-program-reset` and
configured-uppercase-N retry `editor-program-reset-casefix` both reach the
stock editor and emit all8 expected key sequences; Home positioning and Insert
mode still fail. Both close unsaved and the server records no new post.
The current editor aggregate remains false. Hardware restoration and synthetic
PRM preservation pass in both servers. The separate menu matrix passes after
its retained ENiGMA timed-workflow retry; that does not make editing pass.
