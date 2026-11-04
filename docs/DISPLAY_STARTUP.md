# Applying imported display preferences during normal startup

The optional `--display-startup` build applies successfully imported display
preferences after the source-owned reset baseline is captured and before UART
enable, automatic dialing or ordinary parser input. It requires the composed
geometry, full-frame, ASPECT-row, notice and status-control owners. Competing
startup geometry diagnostics are rejected explicitly; they cannot silently
override the saved display choice. This enables startup application only;
normal Toggle Lines, live setup/HOOK adoption and tracked-online resize remain.

## Startup behavior

With no imported preferences, the new entry returns without changing BIOS,
canonical geometry or selector readiness. It does not invent saved defaults.
With an accepted capture, it delegates to the existing checked selector
transaction. That transaction retains native selector/font/fallback decisions
while reconciling BIOS, logical dimensions, status suppression, shadow, reset
defaults and mouse ownership. Raw preferences and the PRM remain unchanged.
Any nonzero saved hidden-status word selects hidden status.

The captured words remain `01C2` hidden status, `01C8` selector, `01CA` preferred
rows and `04EC` configured video mode. Selectors0..4 retain their established
meaning; accepted physical layout is independently verified. An ineligible mode
or verified graphics-mode failure can fall back to the known25-row baseline.
Fallback does not mean the requested mode succeeded.

A refused startup request follows the existing unsupported-display boundary
`2EAA`, exits with code2 and unwinds resources already acquired. It does not enable
transmission or dial after refusal. Existing UART/PIC/vector cleanup remains
responsible for restoration. The flag is off by default; disabling it retains
the preceding executable exactly. This is not a deployment/configuration migration.

## Evidence

The [receipt](validation/display-startup.json) binds exact images, public sources,
captures, checkers and source-only rebuilds.

-57 linked startup inputs cover absent import, selectors0..4, all four accepted
 heights and visible/nonzero-hidden captures, unchanged raw words, canonical
 shadow/RIS/query behavior, ineligible/graphics fallback, invalid captures and
 selectors, and busy-owner refusal. Product C/ASM executes; BIOS/UART/DOS
 boundaries are modeled.
-51 existing selector,181 preference-import and36 normal status-control inputs
 pass on the enabled parent:325 linked inputs in total. Four invalid build
 configurations reject competing initializers or missing owners before output.
-22 actual DOS8086 workflows cover20 accepted layouts and two refused startups.
 Owned PRM files drive25/28/43/50 rows, both status states, keep-mode, configured
 selectors, ineligible/graphics fallback, no import and disabled control. The
 no-import case explicitly selects COM3 with its normal IRQ4; imported cases
 retain their owned COM3/IRQ5 configuration. These are fixtures, not physical
 serial-setting changes.
-A DOS observer reads real BIOS mode/columns/page and BDA height/font after return
 without changing them. Complete8000-byte captures verify lower-body text/status.
 Actual UART/parser replies and a typed key use selected runtime dimensions.
 Invalid selectors return code2 without any transmitted byte. Every case retains
 the PRM and matches the42-byte sampled UART/PIC/vector baseline.
-Independent verification passes all22 cases, rebuilds the geometry observer and
 checks raw PRM words, BIOS records, full frame placement, exact wire order,
 failed-startup silence and restoration. This is not physical BIOS-fault evidence.
-Enabled and disabled parents each reproduce exactly from569 public source files
 in isolated trees without originals or ancestor Git. Disabled bytes match the
 preceding accepted image. The ASPECT child was separately refreshed from288
 current public sources in a fresh Git-free tree and retains its prior bytes;
 its previous manifest carried a shared menu source changed in an earlier
 checkpoint. The current manifest now matches that source too.

Enabled candidate SHA256:
`14358a87ca5a7f4429c87d10981eedbb0eeb1564d2e25b835d351c645f858ff0`.
Near data/stack remains65,120 bytes; resident CS is65,514 bytes with22 spare.
DISPLAY_CODE grows5,517→5,525 bytes. Disabled bytes remain
`baaff639d995f791ea8613e02544f2a14d316e281b96a57f9366086c52f72f1b`.
Budget further resident additions through code banks.

The direct-mode serial harness now honors its supplied banner instead of
silently substituting a fixed one. Initial probes also exposed an absent-import
fixture using the wrong port/IRQ and a duplicated DSR query. Fixtures were
corrected and the complete accepted matrix rerun; no application workaround or
arbitrary wire-prefix tolerance was added.

## Reproduction and remaining work

Add `--display-startup` to the receipt's composed parent flags. It excludes
`--session-rows-probe`, `--display-row-probe` and `--status-probe`, which are
competing startup geometry policies. Use the pinned toolchain and fresh outputs:

```sh
./tools/dev --command python standalone/check_display_startup_live.py \
  --terminal build/NEW/enabled/TERMINAL.EXE --output build/NEW-linked
./tools/dev --command python standalone/test_display_startup_dos.py \
  --build build/NEW --output build/NEW-DOS --jobs 2
./tools/dev --command python standalone/check_display_startup_artifacts.py \
  --run build/NEW-DOS --output build/NEW-independent
```

The DOS matrix also needs a matching `disabled` parent. Exact flags/paths are in
the receipt. The pre-session Linux collector can query accepted logical size via
CSI18t; startup application does not prove that collector's integration with
installed SynthModem or owned BBS layouts.

Normal Toggle Lines, live preference adoption, online NAWS, owned Enigma/
Synchronet and physical Cirrus/mouse/Boca/SPA2102/SIP/audio acceptance remain open.
No physical DOS/card files, selected connection-test payload, private settings/
call history, installed bridge/BBS/services or networking changed. The full
application-parity goal remains active.
