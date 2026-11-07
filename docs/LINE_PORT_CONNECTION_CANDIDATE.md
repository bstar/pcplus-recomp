# Matched native Alt-P connection package

The reviewed connection-test package now includes the transient native Line/Port
popup and its compulsory `PCLINE.OVL` companion. The package has 14 public files,
including five executables. It preserves the existing special-edition splash,
Chat/Help, ASPECT EMULATE and the separately versioned compiler. This software
milestone does not select a release or update the physical machine.

The [package receipt](validation/line-port-connection-candidate.json) binds the
recipe, products, archive, actual DOS workflows and isolated source rebuild.
The [native Alt-P receipt](LINE_PORT_OVERLAY.md) retains the exact same products'
popup, capacity, ABI, source, Enigma/Synchronet and carrier-recovery evidence.
Its historical source snapshot is not rewritten by packaging changes.

## Exact payload

- Parent: `ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399`
- Alt-P module: `0c92e898622576ed27cfc0d146da09c199a126f10b37567ca5bc9c1ca9cf18e0`
- Interpreter: `5c641ac458494d8d6d7cb048d13dc531830689a4e401df7011092057c37ef066`
- Compiler: `ac58a8a1ee07f6253b4dfb4d531eb1d456da3b6f7ea15afca8814db626e997e2`
- ZIP: `faecb4dee79a941e3937d520f9c548599cf40635930cf917eda6ef4396fbbd71`

The native implementation's source base is `d875ea0`. The isolated export of
package-build sources is commit `a64ac72`; both full identities are recorded in
the receipt. These distinguish the application change from its packaging work.

```sh
./tools/dev --command python standalone/build_connection_candidate.py \
  --recipe standalone/line_port_connection_candidate_recipe.json \
  --output-dir build/NEW-line-port-connection
```

The result is `build/NEW-line-port-connection/archive/PCPLUSSE.ZIP`, containing
`PCPLUS/` application files. It includes no private PRM/DIR/KEY/KBD/XLT or FON
call history. Preserve those files from the active installation; do not replace
them with another installation's configuration. Always keep the matched parent
and module together. Startup help also uses the module's read-only text span.

## Observed package gates

Fourteen admission cases cover the real matched companion, a plain-build policy
control, missing/corrupt modules, inconsistent declarations and unverified bank
layouts. Invalid archive manifests and incomplete build recipes fail before
creating an archive or starting an application build. The valid archive checks
all extracted bytes, uses fixed timestamps and sorted DOS paths, and excludes
undeclared files.

Five actual DOS8086 workflows run the packaged START/SETUP launchers: standalone
compilation and ASPECT EMULATE/ALARM/DATE/TIME, setup, original magenta splash
with the LoC note, Chat/context Help, and native Alt-P. Alt-P is passively observed
after loading its packaged sibling module, then returns normally. Every mode
preserves six synthetic private-file sentinels and all packaged application
bytes, restores the PCPLUS environment and restores COM3/PIC/vector state.

An isolated 2,552-file public-source export, without originals, private settings,
prior objects or ancestor Git, rebuilds all five executables and reproduces all
14 payload files and the deterministic ZIP. The outer checkout supplies the
pinned Nix environment. A fresh build of the preceding EMULATE recipe also
reproduces its original 13 files and ZIP exactly.

Release selection, verified deployment and physical Boca/SPA2102/SynthModem
acceptance remain separate. These named software gates do not close broader
fault/flow coverage or the full original ASPECT/emulation/protocol/Host inventory.
