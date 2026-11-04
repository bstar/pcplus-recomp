# Original Elapsed Time control

Alt-T (BIOS1400) selects resident thunk BA1B through the initialized overlay32
scan table at DS:44E0. The thunk selects overlay3:DB04. Fresh REA inspection
recovers its complete149-byte body through DB98. Flat assembly matches the
genuine2.01 file range F184..F218 exactly; the relocation-bearing OMF form also
assembles using declared external services. Original executables and synthetic
analysis images are absent from ordinary application build inputs.

The original window distinguishes **ELAPSED TIME THIS CALL:** while connected
from **ELAPSED TIME LAST CALL:** while disconnected. It does not start or reset
the call timer. The caption is selected once at entry. While waiting for a key,
it checks carrier before refreshing the existing elapsed value, refreshes wall
time, and prints the elapsed text. If carrier goes away, further elapsed
updates stop. It consumes one dismissal key, including Escape or Alt-X, and
closes its window using the exact saved two-word handle. The original body sets
the shared window-style word to10; that side effect is retained in the recovery.

## Evidence and boundary

- Resident-thunk bytes: REA `ev_0c36ae18bc599d0422bcecbd2580e59e2ec288d0e0c3cf02ea27753eda145242`.
- Overlay body listing: REA `ev_8162557c031b1b6b5dfb7d21e2fcadf0c2e9808010ef693a12cff0fa18e6ace5`.
- Complete149-byte function boundary: REA `ev_f2d0f28c7e0dfd06c7dde17583ed6c8d3a56408b307a3faddfaa0a9bc6de9d3d`.
- Body bytes: REA `ev_78185ae47ab4378e2df7d7d9d272817681a25d4c4622eae60e5b67b943f017fe`.

The overlay analysis MZ is synthetic and is never executed. Its selected body
is checked separately against the genuine original file. REA's resident read
includes loader relocation fixups; the optional comparison checks the genuine
unrelocated thunk. Complete REA bundles remain in ignored analysis storage.
Public provenance is in
[elapsed-provenance.json](../reconstruction/local_controls/elapsed-provenance.json).

The source-only CPU test executes this149-byte body with explicit modeled
window, print, date/time, carrier and key services.144 cases cover immediate and
repeated refreshes, zero/nonzero carrier values, carrier changes during refresh,
ordinary/extended dismissal keys, and zero/high-bit window handles. Checks
require exact service order and argument cleanup, conditionally updated elapsed
time, one consumed key, exact saved handle, DS=SS, BP/SI/stack preservation, and
the modeled window's restored screen. An optional second run verifies the
complete body and scan/thunk against the genuine original. The
[receipt](validation/elapsed-native.json) identifies both runs separately.

These are native-control recovery tests. They do not establish the behavior of
the external timer/window services, an enabled live Alt-T command, actual DOS
modal/UART coexistence, BBS behavior or physical acceptance. The149-byte body is
not linked into the current application and no installed file is changed.

## Required integration

The [original timer services](ELAPSED_TIME_TIMER.md) now rebuild exactly and
pass their boundary-model suite. Live binding must retain THIS CALL/LAST CALL
even when call-file logging is disabled.
The existing modem negotiation timeout counter must not be reused as call
elapsed time, because initialization, retries and hangup reset it independently.
Bind Alt-T and its original Alt-Z entry to the guarded foreground local-control
owner after menu restoration. Keep serial, parser, flow and qualified-carrier
service running while the view is open; defer connection notices until the
underlay is released, as with Screen Pause. Retain one local dismissal key and
exact view/cursor restoration. Check offline, connected, carrier-loss,
midnight, reconnect and partial-CSI cases before enabling it in a candidate.
Retain source/package identity and fresh Enigma/Synchronet regression gates.

```sh
./tools/dev --command python standalone/check_elapsed_native.py \
  --output build/NEW-elapsed-native
# Separate optional original comparison, outside ordinary builds:
./tools/dev --command python standalone/check_elapsed_native.py \
  --output build/NEW-elapsed-original \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```
