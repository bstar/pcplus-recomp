# Connection notices on accepted status rows

The optional `--row-notices` component places connection notices on the current
canonical physical status row at25/28/43/50 rows. It requires the composed row,
PROGRAM-display and status owners. It changes no line-switch key or startup
preference policy and is not selected for physical deployment here.

Each notice retains the first15 status cells and their byte offset. Show/repaint/
restore use `ui_flow_video_base`; admission uses the existing pure canonical
row/status helper and requires visible status. A replacement notice on the same
row retains the original underlay. If another owner missed retirement and changed
the row, restore discards the old lease; show captures the new row, and native
STATUS refresh drops the old lease before painting. Old row contents cannot be
replayed into a different status-row position. A hidden or inconsistent layout
refuses before acquiring video or stopping a viewer.

Screen Pause and Auto Answer keep their existing fixed-row gate through
`terminal_status_row_admit_far`. Their layouts have not been generalized by this
notice component. The new admission preserves registers and returns only CF;
DS=SS remains the existing caller ABI. Status refresh retains the visible notice
while replacing its saved underlay with the refreshed native status cells.

## Evidence

The [receipt](validation/row-connection-notices.json) binds exact images, manifests,
raw captures, checkers and independent source-only rebuilds.

-72 linked inputs execute actual parent/UI instructions with declared BIOS/UART/
 DOS setup boundaries. They cover all four heights, hidden/visible status,
 replacement and restoration, native repaint, deferred Pause/Elapsed actions,
 different-row stale leases and40 inconsistent-layout refusals. Full logical
 metadata/history planes and video/register/stack invariants are checked where
 applicable. The public shared gate still refuses larger heights. Notices send
 no UART bytes.
-The previous notice regression suite passes, including27 rejected-layout and81
 stale-layout combinations and its ordinary/replacement/retirement/defer groups.
-24 actual DOSBox-X8086 COM3/IRQ5 sessions cover profiles4/6 at all four heights:
 query/render/return, RIS and a cooperative script window with lower live updates.
 The normal parent/ASPECT and real parser generate replies. Post-shutdown notices
 now show Disconnected on every selected physical status row. The artifact checker
 independently matches every logical screen cell, cursor/profile and sampled far
 history across EXEC, proving that relocated notices do not overwrite row25 when
 it belongs to a larger logical screen. Synthetic PRM/staged inputs, expected
 directory accounting, JFT/sink ownership and42-byte UART/PIC/vector restoration
 are retained. These cases exercise normal notice show/retire and local shutdown;
 they do not establish remote DCD-loss acceptance.
-Six parent images reproduce exactly from569 current public sources in empty
 trees without originals or ancestor Git, through pinned Nix. Disabling this
 component retains the preceding ordinary image exactly.

The ordinary internal image is SHA256
`e7fd9abeba288e2e3694d56be5f4e6222ed51826e871f1454e5f5b1a9415e9b9`.
Resident CS is65448 bytes (88 spare); near data/stack65120 bytes. The row lease adds
2 data bytes; segment alignment accounts for the16-byte near-layout increase.
The four session diagnostics retain64 resident bytes spare and are rejected by
application packaging. The disabled control is
`644c76d66e3a07118e278c00ddb94dccb26f02e1466645d7e18b8ef715f111bf`.
The matching ASPECT child remains the source-built23caac93… image from the
[native PROGRAM checkpoint](NATIVE_PROGRAM_28_ROWS.md).

## Reproduce and remaining work

Build with the receipt's exact flags via `./tools/dev --command python
standalone/build_terminal.py ... --output-dir build/NEW`. Use
`standalone/check_large_notice_live.py --terminal ORDINARY --output build/NEW`
and `standalone/check_notice_row_live.py` for linked checks. The existing
`standalone/test_aspect_large_session_dos.py` uses manifest-selected footer
expectations; run both profiles with the four separate startup-height diagnostics.
Use `standalone/check_aspect_large_session_artifacts.py` for independent complete
logical-frame/history checks, and `standalone/prove_terminal_variant.py` for
source-only rebuilds. All outputs must be new; exact paths/hashes are in the receipt.

Next cover partial CSI/errors/cancellation, remote carrier loss and reconnect,
in-flight traffic/flow stalls and transfers at larger heights. Other fixed-height
modal contracts and normal Ctrl--/startup preference integration remain open.
Owned Enigma/Synchronet, SIP/analog and physical Boca/SPA2102 acceptance are separate.
No physical machine/card, private settings/call history, installed bridge/service,
selected package or deployed application changed. Full original feature parity
and the overall goal remain open.
