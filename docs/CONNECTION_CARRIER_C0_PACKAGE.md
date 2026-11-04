# Carrier-loss and default C0 connection-test package

The [package receipt](validation/connection-carrier-c0-package.json) identifies
the original staged checkpoint below. At that checkpoint it had not replaced
an installed application or changed the deployment selection. Later installation
state and private configuration belong to the machine-management record.

- Folder: `build/connection-test-carrier-c0-final-20261104/PCPLUSSE`.
- Archive: `build/connection-test-carrier-c0-final-20261104.zip`.
- Application source checkpoint: `dc3b638`.
- Packaging source base: `dba968d`.
- Parent SHA256:
  `e2e1f7ec210da06c36be2f8129a622c70788179daf5ab10c4dac22981cc98059`.

An export of 2,142 public source/tooling files reproduces all five executables
and all ten package files exactly, including the authored help resource and
launchers. The export has no originals, private configuration, object files or
accessible ancestor Git. The parent's own isolated proof uses 570 application
inputs. The archive contains only the ten declared payload files; decompression
and every file hash are checked independently against the package manifest.

Actual DOS8086 checks exercise START, SETUP and standalone compilation followed
by a script that creates its expected result. The fixture omits the selected
COM3 entry from the emulated BIOS while retaining the dummy UART at IRQ5.
Hardware snapshots, private fixture PRM/DIR/XLT bytes, environment and packaged
binaries are preserved. Timed START/SETUP captures include the original-style
splash, `Version 2.01-LoC.3`, `LoC SPECIAL EDITION` and the sysop annotation.
This does not constitute physical visual acceptance.

The first package proof rejected its rebuilt terminal because the older flag
converter omitted seven newer display options. The initial script test also
rejected a startup failure: the old editor fixture left display words opaque,
which is invalid for the parent that now applies them. The converter now retains
those options; the fixture supplies admitted VGA25/status-visible values and
rejects an unsupported-function screen. Fresh package proofs and all three DOS
cases pass. Those earlier artifacts remain excluded.

The contained [carrier-loss correction](TRANSFER_LOSS_DRAIN.md) and
[default C0 services](C0_CONTROLS.md) pass current Enigma loss/redial/download/
logoff and local-cancellation workflows, with independent audits and damaged-copy
controls. Synchronet's editor/reference/NAWS regression also passes. These use
the staged serial-side proxy; they do not test analog audio, SIP, the adapter or
the Boca modem.

The package includes no PRM, dialing directory, key mapping, translation settings
or call history. Follow its README and the private machine-management deployment
workflow to preserve those files and retain verified backups. `PCPLUS.FON` is
call history. Keep the actual modem's working initialization settings; the lab's
escape-guard command is not a physical configuration recommendation. Compile
source scripts before starting the terminal to avoid nested compiler memory
pressure. Physical deployment, the reported BUSY behavior and full parity remain
open acceptance gates. Resident CS has only two bytes spare.

## Select the installation directory

`standalone/package_connection_test.py` now accepts `--dos-directory PCPLUS`
for an existing `C:\PCPLUS` installation. The default remains `PCPLUSSE`.
The choice is a single drive-C root directory name of one to eight ASCII letters,
digits or underscores; case is normalized and DOS device names or traversal
are rejected. It is not a drive or arbitrary nested-path option.

The packager records `dos_directory`, creates that payload folder, and uses it
in both launchers and the README. The source-only package proof and actual DOS
launcher/script/setup/splash tests use the same recorded folder. This prevents
installing a package into one directory while its launchers enter another.

The [directory validation receipt](validation/connection-package-directory.json)
binds a reproduced `PCPLUS` package and all three native workflows. All five
executables remain identical to the carrier/C0 checkpoint; the terminal SHA256
above is unchanged. A default-path control with the same source-base metadata
retains all ten original payload files byte-for-byte. The directory-specific
archive is `build/connection-test-pcplus-carrier-c0-20261104/PCPLUS-UPD.zip`.
No PRM, directory, key mapping, translation settings or call history is packaged.
Application installation checks and physical modem acceptance remain distinct.
