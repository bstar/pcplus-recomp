# Setup before connecting

`TERMINAL /S @PCPLUS.PRM` opens the maintained settings editor before acquiring
the UART. Put the source-built `TERMINAL.EXE` and `PRMEDIT.EXE` in the current
DOS directory with the existing, externally identified2.01 PRM. Build both with
`./tools/build terminal setup`; verify with `./tools/build test-setup-startup`.

`/S` requires an explicit8.3 leaf filename using letters, digits, `_` and `-`.
The normal terminal's longer/drive-qualified PRM paths remain supported when
`/S` is absent. No default file, working-directory change or implicit file
creation is introduced. The editor still rejects device and recovery names.

The option parser validates this dependency and leaf syntax before committing
any options. Normal directory-selector validation and optional entry selection
run first. Cancellation there skips setup and connection. Setup then calls the
existing checked DOS process owner directly with local `PRMEDIT.EXE` and a tail
consisting of a leading space plus the filename. This uses neither COMSPEC/PATH
search nor PCSETUP's legacy marker/shared parent pointer.

A failed DOS EXEC, nonzero child exit or abnormal child termination stops startup
with terminal exit7. Successful return runs the existing configuration and
optional directory import, keyboard/action loading, BIOS-port validation and
UART acquisition. Saved values therefore pass the normal decoder checks. CLI
serial-category overrides retain their existing precedence. Escape from the
editor discards unsaved changes and continues startup with the file on disk;
it is not a request to abort connecting. A malformed mapped value can be
repaired before the startup importer sees it. A malformed/truncated file that
cannot be opened by the editor fails without starting the terminal.

This completes an explicit setup-before-connect workflow. It does not provide
setup during an active connection, migrate paths, define all original fields
or defaults, or implement the missing original PCSETUP child. The editor's
staging/recovery policy is described in [SETUP_EDITOR.md](SETUP_EDITOR.md).
The complete application feature gates remain open.

The separate [Alt-F10 workflow](SETUP_LIVE.md) now invokes the maintained editor
after terminal startup. It now applies validated display/pacing/modem/BREAK
changes, with a separate confirmation for same-port baud/line/flow. COM
migration still requires restart; supported profiles4/6 have a separate confirmed
keyboard/view reset during the session.

## Evidence

`standalone/check_setup_startup.py` replays the linked8086 scheduler with only
its DOS EXEC boundary mocked. All interrupts and IN/OUT are forbidden during
this replay.47 inputs cover every process status, normal/abnormal child status,
exact cdecl arguments and bounded tail, caller cleanup, callee registers,
unterminated-path defense and disabled-option bypass.

`standalone/check_terminal_options.py` adds atomic `/S` dependency/path checks,
case/order, duplicate rejection, help bypass and reset to its existing linked
parser tests. Invalid options cannot leak staged settings.

`standalone/test_setup_startup_dos.py` executes the production editor and
terminal in DOSBox-X with synthetic PRMs and a loopback serial peer. An
independent INT1C TSR samples the active COM1 divisor; saved115200 and explicit
CLI19200 are observed at the UART, not inferred from a file round trip. It
briefly selects DLL/DLH with interrupts masked and restores LCR. Sampling is
periodic, not continuous coverage of every port operation. A separate source
child records the exact PSP command tail and UART/PIC/vector state at entry,
which matches the harness's pre-startup sample. Both directions of live serial
traffic and actual video/cursor replies are checked after successful startup.
Failures check expected DOS exit, no serial output and exact final hardware/file
state. Timer observations alone do not prove absence of all transient I/O.

Public `validation/setup-startup-{linked,dos}.json` bind these results to exact
source/binary hashes. Full terminal regressions and isolated source-only builds
remain separate evidence. These checks do not establish physical modem behavior.

The current checkpoint passes43 commands in the full terminal regression
(including the two build steps),47 linked setup inputs and12 actual DOS setup
workflows. Its isolated source checkout reproduces58 byte-identical outputs.
The first regression attempt exposed an overly broad expander-FLAGS comparison;
its retained failure and the corrected target-return observation are recorded
in `validation/setup-startup.json`. No runtime bridge change was needed.
