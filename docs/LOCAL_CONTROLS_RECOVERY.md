# Original local terminal control entries

Fresh REA inspection confirms resident CS:1604 dispatches zero-character BIOS
scan codes through DS:44E0. Verified original2.01 data maps Alt-C(scan2E) to
CS:24E2, Alt-U(scan16) to CS:1368 and Alt-E(scan12) to CS:3316. The initialized
data lives in the appended overlay32; the bare resident MZ does not supply it
to Ghidra automatically. Undefined procedures were not inferred absent merely
because Ghidra had not marked their entrypoints.

Clear Screen directly uses the already recovered clear/home routine. The new
local_controls reset entry passes cdecl argument1 to native20A4, cleans it and
returns(11bytes). The duplex entry maps zero to1 and every other word to0 at
DS:1D1A(13bytes). Its original SBB direction-bit encoding is retained explicitly.
Both flat assemblies match the verified original bytes exactly.

The source-only CPU check passes261 cases; the optional original comparison
passes the same cases. It verifies entry stack/data ownership and the reset
argument, modeling the reset callee as an explicit service boundary. It does
not establish complete reset behavior or UI integration. Provenance is recorded
in reconstruction/local_controls/provenance.json; complete REA records stay in
ignored analysis/local-controls-20261103-rea.json.

```sh
./tools/dev --command python standalone/check_local_control_entries.py \
  --output build/NEW-control-proof
```

Next integration must route both direct keys and Alt-Z actions to a common
foreground owner after view restoration. Defer controls during parser, macro,
child or transfer ownership; verify saved reset-state behavior, status updates,
continued serial input and no transmitted local-key bytes. Account for resident
segment pressure through checked bank interfaces before enabling the commands.
These components are not linked into the deployed application yet.
