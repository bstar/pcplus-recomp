# Screen Pause on accepted display heights

The composed row-geometry build now places Screen Pause on the reserved last
physical row at25/28/43/50 rows. Alt-N and the original reference-menu path retain
the recovered pause sequence: request XOFF, save the row, hide the cursor, consume
one local resume key, restore the row and shape, and request XON. The native
[original evidence](SCREEN_PAUSE.md) and UART/protocol engines are unchanged.

## Display ownership

Admission checks DS=SS, IF1/DF0, the existing pure canonical row/status layout,
visible status,80 columns, narrow video/attribute strides and no viewport. BIOS
must agree on height, color text mode2/3 and page0. A zero legacy BDA height means
25 rows. Builds without the row-geometry component retain the fixed-row gate.
The shared Auto Answer admission was not broadened by this change.

The existing160-byte saved row and exact incoming cursor shape remain on the
stack. Two additional stack bytes bind the captured video offset. Acquisition
refuses an existing Pause owner. Before restoring cells or cursor shape, the
same pure admission runs again and must return the captured offset. A malformed
or coherently different layout releases Pause and requests fatal shutdown7,
preserving an existing exit code. It does not replay a stale row or flush a
queued notice into that unknown display. Normal restore releases Pause before
applying its deferred connection notice, so the prompt cannot become the
notice's saved underlay.

## Flow and modem command mode

The previous Pause adapter could request XON after the connection controller had
already retired a lost carrier. A maintained CONFIG-bank wrapper now uses the
existing logical-lifetime and immediate-readiness policies. A short DCD drop
retains the desired XON for a returning carrier without emitting into command
mode. A qualified loss retires flow ownership and cannot acquire a new pending
control at resume. DIRECT/untracked behavior and normal flow-pressure policy
remain unchanged. The original resident UART adapter remains intact.

This does not make Pause a way to receive unlimited data from a peer that ignores
XOFF. Input remains bounded by the existing receive buffer. The shared DCD
qualification interval is unchanged; checking before output also cannot remove
the physical race between a final carrier read and transmission.

## Evidence

The [receipt](validation/large-screen-pause.json) binds the exact images, public
sources, raw captures and independent rebuild proofs.

-117 linked inputs execute actual foreground/row/notice/control code. They cover
 profiles4/6, all four heights, ordinary/Escape/Alt-X/arrow resume keys,
 THRE/CTS/peer-XOFF pressure, complete8000-byte video, canonical planes and
 63000-byte history, stack/register ABI, hidden/inconsistent geometry, BIOS and
 flag refusals, stale/coherently changed layouts, and transient/sustained DCD.
 The exact restored underlay and injected fault timings are model evidence.
-47 existing Pause regressions and58 carrier-readiness regressions pass.
-The ABI verifier checks all four resident adapters, five existing service calls
 and the two new cross-bank lifetime/readiness calls and relocations. It refuses
 11 separately damaged, unexecuted images. It now reads each function's actual
 map segment rather than assuming every service resides in resident CS.
-15 actual DOS8086 workflows cover direct/reference/partial-parser entry in the
 ordinary image and in four startup-height diagnostics. A passive timer captures
 two complete paused frames a second apart; both must be identical. The owned
 peer sends bounded queued input and a query, which must wait for XON. Lower-row
 queries, resume-key consumption and ordinary keyboard traffic are checked.
-Eight additional actual DOS8086 virtual-modem workflows cover HARD/SOFT at each
 height. The peer observes XOFF, leaves time for the passive Pause snapshots,
 sends a partial CSI and closes TCP. DOSBox-X supplies actual virtual DCD and
 NO CARRIER. Pause resumes locally, the original Connection-menu redial runs in
 the same parent, and both modem initializations must receive clean OK replies.
 Exact command lists reject stray flow bytes and modem ERROR. Two recorded calls,
 preserved previous call history, directory accounting and hardware restoration
 remain checked by the existing passive log observer.
-An independent artifact verifier passes all23 DOS workflows:46 full paused
 frames,16 virtual modem connections in the carrier subset, raw call records,
 hardware snapshots, lower-row/parser replies and query/XON order. It rebuilds
 the passive observer and compares its exact bytes with every used fixture.
-Five isolated569-source parent rebuilds reproduce exactly without original
 executables or ancestor Git. All startup-height diagnostics remain rejected by
 application packaging.

The ordinary image is SHA256
`b760943921d0b0155716d6f3d858d9878ed7501e88a2fdad42887f85c9a5da85`.
Near data/stack remains65,120 bytes; resident CS remains65,500 bytes with36 spare.
The CONFIG bank grows from59,313 to59,457 bytes. Diagnostics retain10 resident
bytes spare. No new static data, resident code, UART instructions or protocol
framing are introduced; the saved-row stack allocation grows from162 to164 bytes.

The first exploratory DOS probe omitted its owned lower-row banner from initial
connection setup. Its lower-row assertion correctly failed. Supplying that
banner to the existing peer fixed the fixture; the accepted workflows were
rerun. No application change was made to accommodate the missing fixture.

## Reproduction and remaining work

Use the pinned Nix environment and the receipt's exact build flags to build fresh
parents with `standalone/build_terminal.py`. Run
`standalone/check_large_pause_live.py --terminal ORDINARY --output build/NEW`,
the existing Pause/ABI/carrier-readiness checks, and
`standalone/prove_terminal_variant.py` for source-only reproduction.

```sh
./tools/dev --command python standalone/test_screen_pause_dos.py \
  --terminal build/NEW/28/TERMINAL.EXE --rows 28 --label NEW-unique-label
./tools/dev --command python standalone/test_large_pause_carrier_dos.py \
  --build build/NEW --rows 28 --output build/NEW-carrier/28
```

Use lowercase labels and fresh output directories. Repeat at the other heights,
and run the ordinary parent separately. The receipt records exact accepted paths
and hashes; `standalone/check_large_pause_artifacts.py` checks their immutable
captures independently.

These results do not establish Boca/SPA2102/SynthModem audio, Enigma/Synchronet
or physical acceptance. Auto Answer's fixed-height ownership, normal line
controls/startup preferences and broader original feature parity remain open.
No selected connection-test package, physical DOS files/card, private settings,
installed bridge/BBS/service or networking were changed. The full goal is active.
