# Startup layout through the staged Telnet handoff

The current source-built parent now has an actual DOS-to-proxy size handoff at
all supported startup heights, with status visible and hidden. This extends the
[earlier24-row handoff](MENU_SIZE_BRIDGE.md); the same staged collector/proxy
bytes are used. Neither the installed SynthModem nor its configuration changed.

| Physical rows | Font pixels | NAWS rows, status visible | NAWS rows, status hidden |
| --- | --- | --- | --- |
| 25 | 16 | 24 | 25 |
| 28 | 14 | 27 | 28 |
| 43 | 8 | 42 | 43 |
| 50 | 8 | 49 | 50 |

Every case imports an owned PRM with selector2, requested height, video-mode0
and the selected status state. The actual startup owner applies that layout
before UART/dial. The actual8086 BIOS keyboard and COM3/3E8/IRQ5 path sends ATZ,
ATD1 and local `loc` selection. The staged proxy owns one CSI18t query before
opening TCP; DOS emits its canonical logical dimensions. An independent Telnet
parser decodes exactly one NAWS80×logical-height record from real loopback TCP.
No terminal reply or size metadata is fabricated by the test peer.

After negotiation, the owned TCP peer sends a bottom-clamped BRIDGE-AREA marker,
a home-row banner and CPR/DA requests. Actual DOS replies and a typed z reach the
TCP peer while size metadata remains local to the menu owner. Full8000-byte
video captures establish logical-bottom placement and status ownership; a separate
DOS observer reads actual BIOS/BDA height, font, mode, columns and page. PRM and
image bytes remain unchanged, normal DOS return succeeds, and the42-byte sampled
UART/PIC/vector state matches before/after.

The final snapshot occurs after Alt-X, so visible status correctly starts with
Disconnected rather than Alt-Z FOR HELP. An initial matrix used the wrong label
expectation; it is excluded. The complete accepted matrix was rerun with that
specific post-exit expectation. No application behavior was changed to satisfy
the test. The synthetic Hayes boundary still forwards +++ATH at shutdown; its
exact bytes are checked, but this is not an analog escape/hangup or carrier test.

## Evidence and reproduction

The [receipt](validation/menu-size-layouts.json) binds the unchanged parent,
569 public application inputs, staged bridge identities and source/capture hashes.
Seventeen existing bridge groups pass again, including failure/cancellation,
stale socket/timer, bounded collector, NAWS refusal and opaque256-byte/lookalike
payload tests. Eight actual DOS workflows cover the table above. Independent
verification re-derives dimensions from raw PRM words, rebuilds the BIOS observer
and per-case sampler, decodes raw TCP without the candidate codec, and checks
exact UART/application bytes and physical video/hardware records. A separate
ordinary invocation retains the harness's default25/24-row behavior and4000-byte
snapshot contract; it is not part of the eight-case independent audit. The generic
modem fixture fills otherwise unused display words withA5A5. That older default
correctly failed startup admission once display startup was enabled. The harness
now supplies explicit valid selector2/25-row/visible/video0 defaults for such
parents; no application validation was relaxed. The entire final matrix was
rerun after this harness change to bind one current source revision.

```sh
./tools/dev --command python lab/bbs/patches/synthmodem-menu-size/check.py \
  --runtime /home/bstar/projects/synthmodem --output build/NEW-stage
./tools/dev --command python standalone/test_menu_size_layouts_dos.py \
  --stage build/NEW-stage --terminal build/ORDINARY/TERMINAL.EXE \
  --output build/NEW-layouts
./tools/dev --command python standalone/check_menu_size_layouts_artifacts.py \
  --run build/NEW-layouts --terminal build/ORDINARY/TERMINAL.EXE \
  --output build/NEW-independent
```

The matrix requires imported-display startup and normal line controls in the
selected image. Actual application bytes remain
`6f9148ccdbd5cd6d8260d1c7fb6dee6e70a6836a1bdd1926b1bc39d6fb4b31a9`;
resident CS65,514/22 spare, near data/stack65,120. Exact source rebuild and matching
ASPECT-child evidence remain bound by the [line-control receipt](validation/line-control.json).
This checkpoint changes only owned test tooling/evidence, not application code.

## Remaining application gates

Owned Enigma and Synchronet fixtures were confirmed listening on loopback, but
no authenticated BBS workflow is part of this matrix. A BBS accepting NAWS is not
proof that its active art-backed editor reflows; the earlier
[editor comparison](TELNET_EDITOR_RESIZE.md) demonstrates that distinction.
Next, compose this actual pre-session probe with owned login, main-screen,
editor/focus/modal-return and transfer workflows, retaining cell/cursor and binary
reference checks. Tracked-online local resizing remains refused. Live setup/HOOK
adoption, full-route failure/reconnect/transfers, broader original feature parity,
physical Cirrus/mouse/Boca/SPA2102/SIP/DSP/audio and verified deployment stay open.
No physical PC/card files, selected connection-test package, private settings/call
history, installed services, host networking or packages changed. Goal active.
