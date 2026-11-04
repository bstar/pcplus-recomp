# Recovered BIOS row service in actual DOS

The standalone row component now runs the recovered capability, font, scanline
and geometry services under actual8086 DOSBox-X BIOS implementations. It is a
prerequisite for the unfinished original Toggle Lines command, and is not linked
into the maintained terminal or included in a deployment package.

Two newly recovered units contribute102 exact original bytes: detection6CD8
(66) and the virtual-display-buffer probe7E34(36). The probe uses the original
EGA BH sentinel, VGA AL result and vendor signature checks, then tail-calls
geometry. Its capability WORDs increment; they are not idempotent assignments.
The buffer helper compares returned ES with the prior segment and commits the
native redirect flag/segment. The maintained owner clears capability fields
before each probe and rejects unsupported redirected segments.

[Provenance](../reconstruction/display_modes/capabilities-provenance.json) binds
complete REA byte reads to original SHA6401ccfd. The detector was not identified
as a function by the provider's function-boundary inventory; its static byte
reads and decoded branches establish the recovery, not an original runtime or
decompiled-source observation. Existing row/font/baseline/geometry/scanline/
cursor units bring the total to606 original bytes in nine units. A separate
original-file comparison checks every flat byte; ordinary builds use only
committed sources and digests.

## Maintained owner

`native_display_rows_probe()` and `native_display_rows_set()` are far-cdecl
entries with caller-owned near result storage, DS=SS, IF enabled and DF clear.
The caller must serialize access and own all screen/frame loans. Supported
requests are25/28/43/50 only, in80-column text modes2/3/7, page0. No heap is used.
The component's checked OMF imports contain only its own display services and
the existing small-code model marker; it needs no CRT BIOS thunk. The diagnostic
executable separately uses the CRT for its checks/output.

Unsupported requests return2 before a mode/font change. A supported request
uses the recovered BIOS path and reprobes actual geometry. A mismatch attempts
the original baseline reset once. Return3 means the request failed but80x25
fallback was verified. Return4 means fallback was not verified; it must not be
treated as a successful request or guaranteed25-row state. Invalid inputs
return1. Native mode/font changes are destructive operations, not screen-content
transactions. The original requested selector is not used as a success result.

## Actual DOS evidence

| DOSBox display profile | Successful row requests | Checks |
| --- | --- | --- |
| VGA color, mode3 |25/28/43/50 |97 |
| VGA monochrome, mode7 |25/28/43/50 |96 |
| EGA |25/43 |86 |
| CGA |25 |74 |
| Hercules, mode7 |25 |73 |

All426 checks pass. Actual BIOS mode/page/columns, BDA rows and BIOS font-height
reports independently check geometry. Repeated probes retain stable capability
values. Unsupported cases preserve two video sentinels and submit no observed
mode/font changes. Ten invalid row WORDs, NULL output, graphics and nonzero-page
admission are covered where the adapter implements those modes/pages.

An owned INT10 diagnostic observer refuses one8-pixel font load on each VGA
profile: the component reports3 and verifies25 rows. It then refuses both
baseline mode changes while50 rows are active: the component reports4 with
actual50 rows and no fallback-success flag. A subsequent normal request recovers
25 rows. The observer changes no product function, instruction or return address,
and its vector is restored before exit. It is diagnostic code, not a TSR or
physical-machine installation. An earlier run failed an observer-state readback;
the accepted observer uses explicit CS-owned getters/arming entries.

The [receipt](validation/display-rows-dos.json) binds the actual DOS matrix and
an exact source-only rebuild in a temporary tree with no ancestor Git or
original artifacts. Current diagnostic SHA is
`d226171b203564f7a445195c67c4f058efa7e1654fdcdd2ea1dbf06b9fadbf04`.

```sh
./tools/dev --command python standalone/build_display_rows.py \
  --output build/NEW-display-rows
./tools/dev --command python standalone/test_display_rows_dos.py \
  --component build/NEW-display-rows --output build/NEW-display-rows-dos
```

Bank/namespace integration, preferred-video-mode import, canonical terminal/
RIS/scroll geometry, larger shadow/frame/history loans, guarded key/menu entry,
online DOS/bridge size coordination and application/package acceptance remain
open. No BBS, UART, SIP, real Cirrus VGA or physical acceptance follows from this
display-component matrix. All13 unavailable commands and the full application
goal remain open; existing terminal/package/deployment identities are unchanged.
