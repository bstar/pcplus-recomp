# Startup capture of saved display preferences

`--display-preferences` adds a typed eight-byte capture to the current internal
row-owner component. Both public startup readers capture the four
[recovered saved words](DISPLAY_CONFIGURATION.md) from their existing single
PRM read: status-hidden01C2, selector01C8, rows01CA and video-mode04EC. The raw
words remain separate from accepted BIOS, parser and runtime selector state.
This option requires `--row-geometry-owner` and does not enable any command.

The capture publishes only after serial, optional modem, transfer, directory,
mouse and baseline checks succeed. It uses no extra file read, heap or BIOS
call. Failed reads or validation retain the previous capture and readiness.
Every input/output object must be disjoint from the capture and readiness stores;
aliases are rejected before file IO. The existing public calling conventions
and serial/directory plan layouts remain unchanged.

`terminal_display_preferences_ready` is explicitly cleared at actual MZ entry,
before mouse/bootstrap owners, independently of BSS contents. A successful
import stores all four raw words, then sets readiness1. No PRM/default import
means no ready capture. This is startup metadata: live setup/HOOK adoption does
not refresh it yet. Neither zero-filled capture bytes nor a saved selector are
evidence of accepted hardware geometry.

## Verification

[Receipt](validation/display-preferences-startup.json) binds the ordinary0915e079
and separate diagnostic862eacd9 images, manifests, source hashes and reports.
Ordinary resident CS is65398 bytes (138 spare); DGROUP stays65072 (464 spare).
Its CONFIG_CODE is larger, so this is not a claim of zero additional retained
memory. The eight-byte capture and two-byte readiness occupy existing alignment
capacity. The diagnostic's local report storage makes its DGROUP65104.

The linked CPU suite passes181 inputs:132 raw-field combinations over serial,
modem and directory startup;12 read/decode/mouse/late-baseline failures;36
capture/readiness aliases; and actual MZ readiness initialization. The real C/ASM
startup readers, validators, mouse staging and baseline owner execute. A boundary
observer verifies the old capture is still present on entry to baseline publish.
DOS/file effects are modeled; the late failure clears IF at the real publish
boundary. No product function or instruction is replaced. The raw captures retain
all bits, including values not currently admissible as video requests. Existing
screen/shadow/history planes remain unchanged during these import checks.

Actual8086 DOS parent startup reads a synthetic PRM and writes a diagnostic-only
DPREF.BIN containing readiness1 and raw words FFFF,4,43,12h. The ordinary live
layout still starts80x25 with24 content rows: capture does not apply those saved
preferences. Both normal and exclusive GROWS.BIN refusal workflows verify the
capture, unchanged PRM/image, zero serial output and42-byte vector/UART/PIC
restoration. The existing BIOS/canonical row sequence and full-shadow/video
captures also pass. This startup diagnostic runs before UART enable and cannot
be packaged as the application.

The ordinary image passes102 row-transaction,76 status and250 captured-default
regression inputs. Ordinary, diagnostic and disabled-control images each rebuild
exactly from declared public sources in fresh trees without ancestor Git or
original artifacts. With this option disabled the executable stays exactly
7e61a128, the accepted preceding row component.

```sh
# Add to the current internal row-owner build flags:
--display-preferences

./tools/dev --command python standalone/check_display_preferences_live.py \
  --terminal build/ORDINARY/TERMINAL.EXE --output build/NEW-display-import
```

## Remaining integration

Saved words now reach a checked startup capture; they are not applied to BIOS,
canonical status visibility or runtime selector. The [canonical selector transaction](DISPLAY_SELECTOR_TRANSACTION.md) now
reconciles saved selector with accepted BIOS/canonical state and implements
explicit saved application/cycling APIs. Normal startup application remains guarded;
and define live setup/HOOK updates. Larger-screen modal loans, normal command
bindings and online DOS/bridge size agreement remain open. Do not silently apply
an unsupported preference or advertise extra rows while the bridge remains24.

No application package, deployment selection, physical machine, private PRM,
bridge or BBS instance changes here. Thirteen reference commands remain
unavailable. The ignored display-preferences pointer selects an internal
component only. Physical hardware and full application acceptance remain open.
