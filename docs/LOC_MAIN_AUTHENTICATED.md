# Authenticated LoC main-menu rendering and input

The current source-built PCPlus parent now has a real authenticated test of the
copied LoSs oF CoNtRoL main module, command form and source artwork. The fixture
uses the pinned stock Enigma core with synthetic accounts/database snapshots and
separate writable paths. Only the selected main-menu objects and three explicit
module/layout files are copied from the source board; no private board database
or complete board configuration is imported. Main M/F/G actions retain their
source mappings while other unstaged routes are omitted. This is selected-menu
acceptance, not a whole live-board clone.

## Interaction and independent references

For each admitted physical height25/28/43/50 with status visible/hidden, actual
DOS startup applies an owned selector2/video0 PRM before dial. The staged proxy
owns one CSI18t query and advertises the real logical dimensions through Telnet
NAWS. The synthetic user logs in through actual DOS BIOS keyboard/UART input.
Then the workflow:

1. Opens native PCPlus Alt-Z. A passive INT1C observer captures the actual reference
   screen and all39 original command labels; it neither injects keys nor reads UART.
2. Dismisses the local menu, enters the BBS message menu with M/Enter, and returns
   with Q/Enter. Real authenticated server menu events verify the round trip.
3. Types LOCSNAP into the restored LoC command field without submitting it.
4. Uses a real final CPR to bound the complete delivered output prefix before
   DOS exits. Later output is held and retained separately by the fixture.

The independent ANSI/cell oracle compares every logical character/attribute cell
and cursor. A second model derives glyphs and nearest16-color attributes directly
from classic-pillars.json, independently of the emitted ANSI. It verifies every
non-field cell, including blank extensions below the25-row artwork. The14 live
field cells are checked separately: LOCSNAP followed by seven spaces, bright-white
entered text, and cursor column53. The25-row visible-status case uses the source
module's explicit24-row separator reduction and field row24; every other case uses
field row25. The declared CP437 fallback maps only unsupported Ð to D. Font pixels
are not accepted by a character/attribute-plane comparison.

Each run also checks raw PRM, actual BIOS/BDA height/font/mode/columns/page,
full8000-byte physical capture, normal DOS return, unchanged image/configuration,
and42-byte UART/PIC/vector restoration. A real TCP capture and server NAWS event
independently establish the advertised size; terminal metadata never becomes
BBS command-field input. The native-menu witness establishes actual display,
while the final complete frame and subsequent BBS input verify restoration.
All39 labels do not imply that every original command is implemented.

## Adapter and fixture changes

The owned proxy adapter now accepts the already-declared loopback fixture port
23239 and an explicit bounded uppercase freeze trigger. Its default remains
UNSAVED. LoC uses LOCSNAP so a real focused input field can trigger capture without
entering the message editor or publishing content. Fresh stock Enigma/Synchronet
editor workflows exercise the unchanged default behavior and retain independent
NAWS/cell/cursor checks. The installed SynthModem source/configuration/service is
not modified by the adapter's in-memory test overrides.

The fixture stager copies a clean pinned stock source tree, shares installed
Node dependencies by the existing read-only convention, and snapshots only the
two synthetic stock users. It verifies the source board's selected file hashes
before/after staging and every session. Current source client.js, standard_menu.js
and view_controller.js also match the corresponding pinned stock core files;
this observation does not establish all live-board code/configuration equivalence.

A component control compares browser25 output from the current copied module to
the historical pre-classic-ANSI-fix module: wire bytes remain identical. It also
checks the24/25 DOS prompt positions and classic SGR fallback. This is not a
browser pixel or authenticated browser-session assertion. The earlier
[menu/color recovery](validation/loc-menu-and-carrier.json) retains its separate
historical component scope.

## Accepted evidence

The [receipt](validation/loc-main-authenticated.json) binds all eight workflows,
23,040 matching reference cells and cursors,22,928 matching non-field source-model
cells (including blank extensions),112 independently checked live field cells,
eight native39-label menu witnesses and eight authenticated message-menu round
trips. The complete matrix checker verifies every linked producer/source/capture.
Eighteen copied-capture controls at visible25 and hidden50 rows pass: two unchanged
captures accepted,16 first/bottom glyph/attribute/cursor/prefix/font/proxy-input
mutations rejected. Bridge error logs are empty. Both fresh default-trigger stock
editor regressions retain zero differing cells. Browser25 wire invariance passes.
The explicitly owned fixture was stopped afterward; pre-existing services remain.

Application bytes remain
`a2fd6a3fcdcc30138426d747d8cde400d9fc6eb9ca5fca84d1656aeaf17caa77`,
resident CS65,514/22 spare and near data/stack65,120. Its exact569-public-source
rebuild still matches current application inputs. This checkpoint changes owned
test tooling/evidence, not application code or the selected deployment package.

## Reproduction

Use a fresh fixture/output and the pinned toolchains. Existing stock source and
synthetic databases must already be prepared. Staging/startup uses the BBS shell:

```sh
./tools/bbs-dev --command python lab/bbs/enigma_loc_menu_fixture.py setup \
  --candidate build/NEW-fixture --server-root /path/to/source-board
./tools/bbs-dev --command python lab/bbs/enigma_loc_menu_fixture.py start \
  --candidate build/NEW-fixture
./tools/dev --command python lab/bbs/test_loc_main_matrix.py \
  --candidate build/NEW-fixture --runtime build/STAGE/candidate \
  --terminal build/PARENT/TERMINAL.EXE --output build/NEW-matrix
./tools/dev --command python lab/bbs/check_loc_main_matrix.py \
  --run build/NEW-matrix --output build/NEW-independent
./tools/bbs-dev --command python lab/bbs/enigma_loc_menu_fixture.py stop \
  --candidate build/NEW-fixture
```

The source module/layout/form copies and generated captures stay in ignored build
storage. No source-board module, live listener, private settings/call history,
physical DOS/card files, selected deployment package, host networking or package
is replaced by this validation.

## Remaining scope

The route remains paced250ms key-framing/20ms serial input and synthetic Hayes
through the staged pre-session proxy. It does not establish actual SIP/DSP/audio,
physical CTS/DCD timing, unframed transport, every intermediate frame, full-route
binary transfers/cancellation/reconnect or other custom board menus/doors. Broader
original commands/emulations/ASPECT/Host parity, live setup/HOOK adoption, online
local resize and physical Cirrus/mouse/Boca/SPA2102 acceptance remain open. The
full application goal stays active.
