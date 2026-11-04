# Scripted size reporting and authenticated BBS editor checks

The source-built parent now answers ordinary CSI18t during a checked attached
ASPECT receive scope, through the child's existing serial callbacks. This resolves
an actual pre-session size-probe/login deadlock found while composing the
[startup handoff](MENU_SIZE_LAYOUTS.md) with stock Synchronet's scripted login.
The parent also passes a fresh stock ENiGMA editor reference through that probe.
This remains paced loopback evidence, not physical modem acceptance.

## The failure and change

The previous parent consumed the proxy's size query without replying whenever
ASPECT/program ownership was active. The script selected `loc`, then waited for
Login; the staged proxy waited for the terminal's size response before opening
BBS TCP. It timed out. The real script trace was BRIDGE|FAIL-LOGIN|, with one
size query delivered, no size response and no BBS TCP connection. Normal DOS
return and restored hardware did not make that a successful login.

The maintained size-report extension now distinguishes a checked attached parser
scope from ordinary program ownership. It retains quit/transfer/geometry gates,
requires active scope1 and calls the existing ASPECT command preflight before
formatting a reply. That revalidates script kind, parser depth, owners, layout and
lease policy; a failed preflight follows the established typed abort. Ordinary
program/pending ownership still refuses the report.

An attached reply uses the existing `terminal_render_send` and resident callback
path, as CPR/DA already do. It never writes the inactive parent TX ring. Callback
serial failures follow the existing typed-abort boundary, so the byte prefix may
have been sent before failure; this branch does not promise an atomic child
transmission. The ordinary foreground path retains its complete-response queue
reservation, provenance and corrupted/full-ring refusal. Neither branch changes
geometry, cursor, attributes, saved state or raw preferences. This is maintained
protocol integration, not a byte-exact recovery of an original PCPlus feature.

## Actual editor evidence

Both final runs use the same new source-built parent, actual8086 BIOS keyboard,
COM3/3E8/IRQ5,19200/8N1/HARD configuration, synthetic Hayes boundary and staged
SynthModem proxy. Imported selector2/video0/25-row/visible preferences apply
before dial. One real CSI18t reply seeds80×24 Telnet NAWS before connection.
The test adapter's optional byte-transparent loopback relay captures the actual
TCP bytes sent to each stock BBS. Independent decoding verifies the advertisement
and that terminal size metadata was not forwarded as editor input.

| Stock owned fixture | Delivered bytes at CPR boundary | Reference/actual cursor | Differing cells |
| --- | --- | --- | --- |
| ENiGMA | 48,367 | 9;8 | 0 of1,920 |
| Synchronet | 22,138 | 5;8 | 0 of1,920 |

ENiGMA authenticates the synthetic account, enters the editor and exercises
Home/End, insert/overtype, delete, tab, page keys and Ctrl-Y before leaving an
unsaved draft. Server session logs independently confirm80×24 NAWS, authentication,
editor entry and no posted message. It exits the unsaved connection; this is not
a test of its discard menu.

Synchronet's actual ASPECT child now reaches every recorded login/menu/subject/
editor stage. Native BIOS input exercises the stock editor; held continuation
independently verifies normal Ctrl-Q abort and return behavior. Static fixture
inputs, message bodies and total post/email/feedback/transfer counters remain
unchanged. Page keys in these one-line drafts test document boundaries, not
multiline scrolling. Existing separate multiline evidence is not relabelled as
acceptance of this new route.

The independent cell audit pairs the complete delivered prefix with the real
final CPR and final physical snapshot. Later output is held by the fixture,
retained separately and excluded from the matching prefix. The fixture consumes
only its own actual CPR reply. ENiGMA's single declared default-CP437 font probe
is projected out for the pinned pyte oracle; font pixels are not verified.
Synchronet's RIP query passes unchanged. Fourteen copied-artifact controls
(seven per peer) accept unchanged captures and reject character, attribute,
cursor, truncated prefix, unsupported font and truncated proxy-input mutations.

## Bound checks and reproduction

The [receipt](validation/aspect-size-probe-bbs.json) binds exact sources, parent,
child, staged proxy, reports and capture identities. Thirty-five linked inputs
execute actual parent report/preflight/resident dispatch with an authored far
callback ABI peer. They cover four heights, both status states/profiles, invalid
ownership/depth and every possible serial-failure prefix. Failure checks stop at
the actual typed-abort entry and do not claim subsequent cleanup. Product
instructions are not replaced. BIOS/DOS/UART setup is modeled. The same image
passes44 ordinary report inputs and271 larger-row ASPECT admission inputs:
350 linked inputs in this checkpoint.

The ordinary image reproduces exactly from569 current public inputs in a fresh
Git-free tree without originals. The existing fresh288-source ASPECT child still
matches all current inputs and retains its accepted bytes; no child source changed.
Parent SHA256:
`a2fd6a3fcdcc30138426d747d8cde400d9fc6eb9ca5fca84d1656aeaf17caa77`.
Resident CS remains65,514/22 spare, near data/stack65,120. DISPLAY_CODE grows
5,525→5,576; no new resident code or near static state is added.

```sh
./tools/dev --command python lab/bbs/test_synthmodem_proxy_dos.py \
  --runtime build/STAGE/candidate --terminal build/PARENT/TERMINAL.EXE \
  --label NEW-ENIGMA --byte-delay-ms 20 --framing-ms 250 \
  --screen-reference --size-probe
./tools/dev --command python lab/bbs/test_synchronet_screen_reference_dos.py \
  --runtime build/STAGE/candidate --terminal build/PARENT/TERMINAL.EXE \
  --runner build/CHILD/ASPECT.EXE --label NEW-SYNC --size-probe
./tools/dev --command python lab/bbs/audit_size_probe_screen.py \
  --output build/bbs-lab/results/enigma/NEW-ENIGMA \
  --bridge build/bbs-lab/NEW-ENIGMA-proxy
```

Repeat the audit for Synchronet. The staging recipe and pinned bridge inputs
remain in [menu-size integration](MENU_SIZE_BRIDGE.md). The optional adapter
probe is off by default; ordinary harness behavior remains available. Explicit
`--display-rows`/`--status-hidden` only change owned test PRM files. Compiled
initial geometry remains the reference fixture's expected24-row contract, not
the source of the size advertisement; raw DOS replies and raw TCP prove that.

## Remaining gates

This checkpoint establishes one authenticated80×24 final editor frame per peer.
The custom LoC main screen, larger authenticated layouts, every intermediate
frame, full-route sustained transfers/cancel/carrier/reconnect and less-paced
transport need separate checks. Live setup/HOOK adoption, online local resize,
other profiles/emulations/commands/ASPECT/Host parity and physical Cirrus/mouse/
Boca/SPA2102/SIP/DSP/audio acceptance remain open. No selected deployment package,
physical PC/card files, private configuration/call history, installed SynthModem/
BBS service, host network or package changed. Full goal remains active.
