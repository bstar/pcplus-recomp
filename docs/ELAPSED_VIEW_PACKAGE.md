# Elapsed Time candidate package

The [serviced Alt-T candidate](ELAPSED_VIEW_LIVE.md) now passes clean-source and
package/runtime checks. It is staged for hardware testing, not installed.
Application source commit is `f4191e3`; package/tooling source base is `ec4a4d1`.
The terminal remains SHA256
`340cb4bac4394d946f0bcbb52adacd922d7f8d8fec9665e117ff1f9cd8b95f6d`.
ASPECT remains84160498, ASPCOMP ae0fe208, PRMEDIT0a8452e7 and XLTEDIT c3cba662.
No application bytes changed during this packaging checkpoint.

Staged folder: `build/connection-elapsed-view-committed-20261103/PCPLUSSE`.
Verified archive: the sibling `pcplus-elapsed-view-test.zip`.
Its ten members match the package manifest exactly: five source-built programs,
authored help, START/SETUP, VERSION and README. No PRM, DIR, XLT, KEY/KBD or FON
payload is included. Preserve existing configuration/custom files and especially
PCPLUS.FON, which is evolving call history. The generated launchers target
C:\PCPLUSSE; installation at C:\PCPLUS must retain its actual launchers/path
and private configuration rather than copying these launchers blindly.

## Reproduction and runtime evidence

The terminal reproduces exactly from537 declared source files in an empty tree
with ancestor Git unavailable and no original executable inputs. Rebuild flag
selection now retains `--call-timer` and `--elapsed-view`.

The complete package reproduces from2044 committed public source files with
ancestor Git unavailable. All five executables and all ten package files match
exactly. The verifier uses explicit isolated terminal/ASPECT output paths, so
custom staging-directory names do not accidentally select an older/default
build. The manifest records both new feature flags and README describes Alt-T.
The source/tooling corrections are committed separately from this receipt.

Actual DOS8086 COM3/3E8h/IRQ5 package checks pass:

- START with DOS-precompiled ASX: standalone compiler produces exact bytecode,
  the packaged interpreter executes it and the script writes its expected result.
- SETUP/cancel/return: launcher returns and the synthetic private image remains
  unchanged.
- Splash-only START: an independent timer captures the magenta Special Edition
  screen; the original layout/edition/register check also passes separately
  against genuine2.01 data.
- START with BIOS COM3 entry omitted: actual UART remains present and configured;
  precompiled script/child return and restoration gates still pass.

All retain launcher exit, restored PCPLUS environment, UART/PIC/vector state,
unchanged synthetic PRM/DIR/XLT and packaged-binary checks. These are dummy-port
package tests, not modem/BBS calls or direct physical-call-history observations.
The precompile workflow is intentional: nested source compilation while the
terminal and interpreter remain resident still has the documented conventional
RAM limitation. It is not advertised as generally working by this receipt.

The [receipt](validation/elapsed-view-package.json) binds the exact package,
archive, clean reproductions, original-splash comparison and four DOS reports.
The prior Alt-T/window, sustained parser and Enigma/Synchronet results remain
bound to the same terminal image through their separate receipt. These checks
do not expand their scope to analog/SIP/DSP or physical acceptance.

## Remaining work

The active installed selection and private files have not changed. Updating
requires the DOS management profile to be available and verified read-back of
application files, while retaining the actual launchers, configuration and
PCPLUS.FON. Reboot out of IRQ5 Network management before Boca modem tests.
The physical BUSY/reboot outcome, same-process real calls, display/input, flow,
transfer/disconnect/reconnect and sound checks remain hardware acceptance work.
Other original controls, file/DOS, directory/key, Chat, ASPECT, emulations/
protocols and Host remain in the full-parity inventory.

```sh
./tools/dev --command python standalone/prove_terminal_manifest.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW-terminal-proof
./tools/dev --command python standalone/prove_connection_test_package.py \
  --package build/SELECTED-PACKAGE --output build/NEW-package-proof
./tools/dev --command python standalone/test_special_package_dos.py \
  --package build/SELECTED-PACKAGE --output build/NEW-runtime \
  --com 3 --irq 5 --precompile
```
