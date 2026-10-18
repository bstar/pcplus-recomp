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

## Live receive checkpoint

Frozen `29da4799847e45ec1144195412a8ed0ceff74136878ffe86617375538de1b196`
repeats both actual DOS recipes under `editor-live-receive-final`, after the
far-storage and live receive integration. Synchronet passes12 behavior checks
and all eight key-wire checks. ENiGMA emits all eight expected sequences and
enters the stock editor, but Home and Insert behavior still fail; it closes
unsaved and the server confirms no post. Both runs restore sampled hardware
and preserve the synthetic PRM. The prior816e runs are retained separately.
Neither normal DOS exit nor correct outgoing key bytes make the ENiGMA editor
a pass. The immediate modem model and stock server decoder remain unchanged.

## Ordinary upload checkpoint

Frozen `036a80922c783887249224122f1f44b856d0ff8ae22a106ffe843cb5c9f1cdad`
repeats both DOS editor recipes under `editor-upload-ack-final`. Synchronet again
passes12 behavior and eight wire checks; ENiGMA still fails Home/Insert behavior
with all eight wire sequences present. It closes unsaved with no post. The
unchanged immediate bridge/stock decoder boundary remains visible. Separate
ordinary upload tests do not make editor compatibility pass.

## Checked capture checkpoint

`editor-capture-final` repeats both actual DOS editor recipes on frozen
`6b69f9b0bd7a79a3123c3e0a20e35ca950ed807c406444fc2004010278ef4dc6`,
after adding the text-capture owner and separating serial service from keyboard
polling. COM2/19200/HARD is unchanged. Synchronet passes its12 behavior and eight
wire-key checks, including Ctrl-Q abort. ENiGMA still enters the stock editor
and emits all eight sequences, but fails Home positioning and Insert mode. It
closes unsaved; the authoritative server session confirms no post. Both restore
hardware and preserve the synthetic PRM. Earlier-runtime cases remain retained
in `docs/validation/bbs-editors.json`; the editor aggregate remains false.

## Screen-file checkpoint

`editor-snapshot-final` repeats both actual DOS recipes on frozen
`fd68875ea86d9da6b237ee6c302ec380a33711bccba4a218cf67f5dd0ed4e78c`,
after adding native row helpers, the private frozen screen and two checked file
owners. COM2/19200/HARD is unchanged. Synchronet passes12 behavior and eight
wire checks, including abort. ENiGMA enters the stock editor and emits all eight
sequences but still fails Home/Insert behavior. It closes unsaved and the server
records no post. Both preserve the synthetic PRM and restore hardware. The
separate successful snapshot/capture tests do not make ENiGMA editing pass.

## Explicit modem-buffering experiment

The same fd68875e DOS binary now passes the ENiGMA Home/Insert checks when the
lab modem explicitly groups raw serial bytes for up to30ms. An immediate control
reproduces both failures. Both runs transmit all eight expected key sequences,
restore sampled hardware, preserve the PRM and close without saving a post.
This is separate evidence, not a replacement for the stock immediate aggregate.
See [experiment, commands and limitations](packetization.md) and
`docs/validation/bbs-enigma-packetization.json`. Physical modem behavior and
TCP receive boundaries remain unverified.

## Live monitor checkpoint

`editor-monitor-final` repeats both immediate-bridge editor recipes on frozen
9d90aa1a after adding the raw monitor, third checked file context and key router.
Synchronet passes12 behavior and eight wire checks, including Ctrl-Q abort.
ENiGMA emits all eight expected sequences but still fails Home/Insert behavior.
It closes unsaved with no new post. Both restore sampled hardware and preserve
the synthetic PRM. The separate buffered fd68875e experiment above remains
historical evidence and is not a current immediate-editor pass.

## Source-built screen-print checkpoint

Frozen terminal
`d4cfa4dcb27edd375195ccd9345dd1513844855840f3e673ab9a2ac7288cf16a`
was copied read-only to
`build/bbs-lab/frozen/editor-screen-print-current/TERMINAL.EXE`.
The current Synchronet `editor-screen-print-eventfix` run passes all12 semantic
checks and all eight exercised key-wire checks, including actual FSEditor
entry and Ctrl-Q abort. ENiGMA's immediate `editor-screen-print-immediate` run
still fails Home positioning and Insert-mode behavior: five of seven semantic
checks pass, all eight key sequences are emitted, and no post is saved.
The corresponding30ms buffered run passes all seven behavior checks. Both
use the same executable, retained unsaved recipe, synthetic PRM and
COM2/19200/8N1/HARD; DOSBox's virtual CTS remains ready. This is a local
packetization experiment, not physical modem validation or a blanket editor
compatibility pass.

`docs/validation/bbs-editors.json` selects only the new Synchronet run and
immediate ENiGMA run, preserving older runtime cases. The earlier menu matrix
retains its own executable identity and was not rewritten. The separate paired
report retains older buffering experiments; see [packetization.md](packetization.md).

The initial current Synchronet attempt reached login but was immediately
logged off with “Time's up” after a forced05:00 MSGMAINT event shortened its
time. `NO_EVENTS` prevented event execution, but the pinned stock
`src/sbbs3/data.cpp:getnextevent()` still considered forced events unless their
`EVENT_DISABLED` bit was set. That server prerequisite failure remains under
`editor-screen-print-current`, separately classified from editor compatibility.

`lab/bbs/synchronet_event_policy.py --apply` now sets only `EVENT_DISABLED`
(bit3/value8) on scheduled events in the owned lab's copied `ctrl/xtrn.ini`.
It preserves every other flag and backs up changed config before/after with
hashes. The normal lab setup and serve commands apply this idempotent policy,
so the existing `NO_EVENTS` intent also covers time-left calculations. The
owned listener was gracefully restarted before the fresh passing retry.
No account quota, stock editor/server executable or remote/public BBS was
changed. Evidence and source hashes are included in the current editor report.

## Dedicated-controller checkpoint

The immutable source-built DOS terminal
`51b94da6b6c8f489fa646a220e7d7a77457459f96e73bec98687b19a1f338c90`
repeats the retained editor recipes on the same owned stock servers. Synchronet
`editor-controller-51b9-rerun` passes all12 behavior checks and all eight key-wire
checks, including real FSEditor entry and Ctrl-Q abort. ENiGMA
`editor-controller-51b9-immediate` still fails Home and Insert behavior despite
all eight outgoing keys being present; no post is saved. Its paired
`editor-controller-51b9-buffer30-rerun` passes all seven behavior checks with
explicit30ms modem buffering. Both use the same DOS executable, synthetic PRM,
keyboard recipe and COM2/19200/8N1/HARD. The server/user state was not reset
between these sequential runs. Physical modem/CTS timing and arbitrary TCP
chunk boundaries remain outside this result.

Initial controller-label attempts used the server-only Nix shell, which lacks
NASM, and stopped before DOS launch. Their setup logs remain separate from the
selected successful harness runs. DOS probes use `./tools/dev`; server setup
uses `./tools/bbs-dev`. The editor-only recording command preserves the menu
matrix and its independently tested executable identities:

```sh
./tools/dev --command python3 lab/bbs/record_checkpoint.py --editors-only \
  --editors editor-controller-51b9-rerun \
  --enigma-editors editor-controller-51b9-immediate
./tools/dev --command python3 lab/bbs/record_packetization.py \
  --buffered editor-controller-51b9-buffer30-rerun \
  --control editor-controller-51b9-immediate
```

The public editor aggregate remains false. Current hash-bound evidence appears
in `docs/validation/bbs-editors.json` and `bbs-enigma-packetization.json`; prior
checkpoints remain in their histories.

## Static far-code checkpoint

The bdeb347c source-built runtime moves the dedicated controller into a separate
CS and preserves the resident keyboard/serial interfaces. Actual DOS editor
recipes are repeated against the same owned servers. Synchronet
`editor-farcode-bdeb` passes12 behavior checks and all eight outgoing key checks;
Ctrl-Q abort succeeds. ENiGMA `editor-farcode-bdeb-buffer30` passes all seven
behavior checks with explicit30ms buffering. Its immediate control
`editor-farcode-bdeb-immediate-retry` reaches the stock message editor, emits all
eight expected keys and again fails Home/Insert behavior. No post is saved.

The first immediate attempt, `editor-farcode-bdeb-immediate`, reached the page/
private-mail flow instead of the message editor. It saved no post and restores
hardware normally, but its Home/Insert failures cannot characterize the intended
editor. The same recipe was retried after the concurrent DOS regression ended;
that ordering does not prove CPU contention caused the navigation failure. The
public editor history retains the failed prerequisite. The paired recorder now
rejects any run that did not enter the stock editor.

```sh
./tools/dev --command python3 lab/bbs/record_checkpoint.py --editors-only \
  --editors editor-farcode-bdeb \
  --enigma-editors editor-farcode-bdeb-immediate-retry \
  --prior-enigma-editors editor-farcode-bdeb-immediate
./tools/dev --command python3 lab/bbs/record_packetization.py \
  --buffered editor-farcode-bdeb-buffer30 \
  --control editor-farcode-bdeb-immediate-retry
```

Both public current reports bind the full runtime hash
`bdeb347c99168c8f745c312abfd40468250959ffdfd82af562476a6d29bea2c8`.
The menu and transfer matrices retain their separate earlier runtime identities.

## Private UI-storage checkpoint

The immutable `8b38144e6c1a62ed0c41967acfe56b6f2c310b9f8a1f27504eb0c7494955964d`
DOS runtime repeats the actual server editor recipes after moving independent
browser, editor and PROGRAM screen frames outside DGROUP. Synchronet
`editor-ui-8b38` passes all 12 behavior checks and eight outgoing-key checks,
including actual FSEditor entry and Ctrl-Q draft abort. ENiGMA
`editor-ui-8b38-immediate` reaches its stock editor and emits all eight keys,
but again fails Home positioning and Insert behavior. No post is saved.
The explicit 30 ms `editor-ui-8b38-buffer30` comparison passes all seven
audited checks and eight outgoing-key checks without saving a post. It uses
the same executable, synthetic PRM, serial settings and retained unsaved
keyboard recipe. See
[current outcomes and limits](modern-compatibility.md) and the hash-bound
paired report; older attempts remain historical evidence.

## Separate modem-CS checkpoint

The7a0ea9d3 runtime repeats actual stock editors after moving the controller
and paced sender into MODEM_CODE. Synchronet `editor-modem-7a0e` passes all12
behavior checks and eight wire checks, including draft abort. ENiGMA
`editor-modem-7a0e-immediate-recipe` reaches the editor, emits all eight keys,
but fails Home/Insert again. The matching30ms
`editor-modem-7a0e-buffer30-recipe` passes all seven audited checks. No post is
saved. Hardware/configuration restoration passes for all completed runs.

The first ENiGMA attempt failed before DOS launch because report-derived
keyboard wrappers accumulated past the ADDKEY limit. It is retained separately.
The current pair uses canonical checked-in input; it does not keep extending
historical generated output. See [current results and recipe provenance](modern-compatibility.md).


## Setup-startup checkpoint

Build0fea93ec repeats all12 Synchronet checks and eight wire checks in
`editor-setup-0fea`. ENiGMA `editor-setup-0fea-immediate-noscan` enters the editor
and fails Home/Insert with all eight sequences present; the paired
`editor-setup-0fea-buffer30-noscan` passes all seven checks. Both disconnect
without posting. The initial immediate run was diverted by login new-item
scanning, while its following buffered run reached the editor. They are retained
as separate preparation evidence, not accepted as a pair. The canonical input
now explicitly selects N at the scan prompt, then dismisses User Stats. See
[the current checkpoint](modern-compatibility.md) for hashes and retained runs.


## Live-settings checkpoint

Build7f481c92 passes all12 stock Synchronet audit checks with HARD COM2/19200
in `editor-live-7f48-hard-clean`. The canonical test now clears a synthetic
autosaved body line before its measured key sequence. Prior SOFT and resumed-
draft attempts remain recorded: SOFT consumed Ctrl-Q as XON; the first HARD
retry inherited that draft and invalidated empty-line column expectations.
The current ENiGMA immediate/buffer30 pair repeats the known Home/Insert
boundary: all eight key sequences are present, immediate forwarding fails those
two behavior checks, and30ms buffering passes all seven. No ENiGMA post is saved;
the accepted Synchronet draft is aborted. See [current evidence](modern-compatibility.md).

## COM-switching checkpoint

Build0666c496 repeats stock editor tests after confirmed COM/profile changes.
Synchronet passes all12 behavior and eight key-wire checks under HARD
COM2/19200, including prepared body-line clearing and actual Ctrl-Q abort.
The matched SOFT control keeps the same COM/baud/line, runtime, recipe and PRM
except flow flags:11/12 behavior checks pass, but the modeled modem consumes
the one outgoing Ctrl-Q as XON, leaving no Ctrl-Q at the BBS and no abort.
The following HARD control delivers it and aborts. This isolates flow selection
in the local model; the earlier7f48 comparison also differed in port and rate.
Server/user state was not reset. See [flow-control.md](flow-control.md).

The current ENiGMA immediate/buffer30 pair reaches the stock message editor in
both runs, emits all eight measured keys and closes without posting. Immediate
forwarding fails Home and Insert behavior;30ms buffering passes all seven
audited checks. The immediate aggregate remains failed. Physical UART/firmware,
multiline scrolling and complete BBS feature coverage remain open.

## Explicit XLT checkpoint

Build2cdff8a2 repeats the stock editor probes after adding explicit XLT startup
selection and a normal receive owner. These BBS runs use XLT disabled. Synchronet
`editor-com-2cdf-hard` passes all12 semantic and eight key-wire checks, including
Ctrl-Q abort. ENiGMA `editor-com-2cdf-immediate` again fails Home/Insert behavior
while emitting all measured keys; `editor-com-2cdf-buffer30` passes all seven
audited checks. Neither ENiGMA run saves a post. The immediate aggregate remains
false, and the earlier COM/flow and packetization experiments remain retained.
See [the current checkpoint](modern-compatibility.md).
