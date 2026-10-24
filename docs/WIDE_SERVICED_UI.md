# Serviced local views over a wide terminal

The command menu, history viewer and filename clipboard can now open over the
132-column terminal in either pane. Their local layouts remain physical
80-column screens. The live logical display, field planes and pane selection
continue to belong to the parser. This extends the
[active-field width checkpoint](ACTIVE_FIELD_WIDTH.md); normal peer width
requests and broader application/child composition remain unfinished.

The frame owner already restored its saved live screen before incoming bytes
and captured the updated screen before repainting a local view. Its old entry
guard refused wide geometry, and the pane owner refused all open viewers. The
new read-only entry check admits an owned 132-column layout through the existing
viewport validator. Narrow entry retains its previous checks.

`redisplay_live_ready` is initialized to zero in the loaded image. Event2 grants
it only after restoring the live physical screen and BIOS cursor. Event3 revokes
it before painting the saved local frame. Every close/stop path clears it.
While a view is open, pane copying requires both the active viewer and this
live-screen grant. A visible overlay cannot be saved into the hidden terminal
shadow. Inconsistent owner/grant states refuse before copying. Other modal
owners keep their existing exclusions. Public width transactions still refuse
throughout an active view, including the background-input interval.

No terminal geometry is temporarily changed to render a menu. Incoming cursor
moves can select either pane; field-aware character edits, scrolling and replies
use their normal owners against the restored live screen. Closing the view
returns to that updated pane and cursor. History is a frozen recorded-text copy
and wraps at 80 columns; clipboard extraction sees its physical 80-column
underlay. These are local-view policies, not a 132-column history/clipboard UI.

## Validation

The [receipt](validation/wide-serviced-ui.json) binds an initially build-free
source rebuild at `build/wide-viewer-source-01`. Four application products, CSI,
both ASPECT runners and the DOS compiler are rebuilt from declared source.
No original or prebuilt executable enters a build.

Each transaction parent checks 144 primary menu/history/clipboard sessions:
profiles4/6, both panes, plain/wrapped/protected fields and1/5/24/25-row layouts
with visible/hidden status. The same 396 input streams execute against a control
terminal without a local view. Complete logical video, both4096-byte metadata
planes, hidden/status canaries, pane/cursor caches, BIOS cursor/shape and wire
output must agree. History snapshots stay frozen while native history continues.

Each primary session refuses a read-only pane admission and a width transaction
while its overlay is visible (288 refusals). Six separate destructive-call cases
verify typed pane-copy refusal without changing overlay or shadow; those aborted
fixtures are never resumed. Another16 cases defer Alt-Z and two arrows until the
parser boundary and preserve the exact logical screen. Five inconsistent
viewer/menu/grant combinations refuse without copying.

The ordinary 80-column checks repeat39 viewer inputs,153 menu inputs and36
pending-menu inputs. Existing viewport replay repeats80 cursor transitions,
60 parser/erase cases and186 pre-copy refusals. The previous field-width,
character/scroll, shared-screen ownership, rollback and CSI relocation checks
also repeat. The flat CSI dispatcher remains exactly2018 bytes at
`3a1524f4c69e7e9da59fd67babc99c94dfdcff097c337dfd79f198705f4535b5`.
The inspector checks the relocated far admission call and the initial grant word.

Eight DOS8086 workflows cover base/branded parents and visible/hidden status:
four existing field-width/character/scroll cases and four new serviced UI cases.
The new declared fixture invokes explicit width once with active field modes.
After that, its timer observer only reads lifecycle words and physical text
rows; its exit observer captures the full physical screen, shadow and planes.
The product executable is unmodified.

The new workflows open the menu, select history, request Alt-Z during an actual
split CSI, queue arrows locally, then open/close the clipboard. The serial peer
sends the split prefix and a completion delayed1.4 seconds from one ordered
trigger. This stays inside the native36-tick parser wait and avoids unrelated
streams interleaving into a partial command. The initial failed pilot used
independent wall-clock updates; one interrupted the partial CSI and correctly
left its late completion as ordinary text. It remains in ignored build history.
The synthetic peer now supports ordered relative response chunks; byte responses
used by existing tests keep their old behavior.

Passive samples must contain all three actual views and observe both the pending
menu request and two queued arrows while the parser is busy. Real background
panes, protected DCH and CPR replies continue. Final logical pixels and both
planes must match an independent initialized field oracle plus a control parser
replay. The replay never supplies data or replies to the DOS process. The checks
also require ordinary keyboard output after closing, no arrow escape sequences
on the wire, unchanged PRM and the independent42-byte UART/PIC/vector baseline.

Five nested compiler cases repeat under the new branded parent, including the
chooser/editor-to-program workflow. Rejected source must show ASPCOMP's actual
compile diagnostic. The compiler/runners remain unchanged; their prior grammar,
workspace and stack evidence is inherited by exact source/product identity.

- Ordinary terminal: `68936e5db734a26b50b0db948e0bdf6f6b43fe9a4fc6903e60f6d9cf3e511f54`.
- Base transaction: `3d5864474315fa3da92b28a807c52e9bbb0420a9725217b3bd364ceb1327baa4`.
- Branded transaction: `7fb45c5a215db65d2f24edbc70ccdd1bd5bb12d908d221012e5b6d6e9966952e`.

The branded minimum allocated module is403,264 bytes, with298 resident code bytes
free. The base near data/stack group has64 bytes spare. There is no new screen
allocation; the previously guarded chooser/PROGRAM sharing is retained.

```sh
./tools/dev --command python3 standalone/prove_wide_viewer_source.py --output build/UNIQUE_WIDE_VIEWER_PROOF --nested
./tools/dev --command python3 standalone/record_wide_viewer.py --proof build/UNIQUE_WIDE_VIEWER_PROOF --output docs/validation/wide-serviced-ui.json
```

Other modal UI, keyboard/child/ASPECT rendering at132 columns, unsupported field
configurations, partial-width wrapped scrolling and width-changing BBS sessions
remain open. This does not certify every menu action at wide width. The card
package is unchanged. Physical modem, throughput, reconnect and transfer
acceptance remain separate requirements.
