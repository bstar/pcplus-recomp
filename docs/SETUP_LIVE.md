# Settings during a terminal session

Place the source-built `TERMINAL.EXE`, `PRMEDIT.EXE` and an existing, externally
identified2.01 `PCPLUS.PRM` in the current DOS directory, then run:

```dos
TERMINAL @PCPLUS.PRM
```

Alt-F10 opens the maintained editor. Tab and PageUp/PageDown navigate fields
and pages; F10 validates and saves; Escape closes, confirming before discarding
unsaved edits. The parent then validates the file on disk and reports the result
at a key prompt before resuming the terminal.

## Applying settings

The foreground owner can now adopt these settings during the session:

- Five configured attributes, autowrap and scrolling.
- Key/command pause character and character pacing.
- Modem numeric settings, commands and response strings for future actions.
- BREAK duration for the next Alt-B operation.

Baud, parity/data/stop and software/hardware flow changes on the current port
now offer a separate confirmation: **Y** applies them, and any other key keeps
the current link. That choice also returns to the terminal; no extra key is
consumed. The peer must independently match the selected format. A busy
transmitter keeps the old serial settings and leaves a visible acknowledgment
prompt. Independent display/modem/BREAK changes can still be adopted.

A COM/base/IRQ change now offers a [confirmed idle-port move](PORT_HANDOFF.md).
The old port is restored before acquiring the new one; target DTR is preserved.
Declining or failing the move defers its serial/profile group together.
Both ports are rechecked just before commit, including incoming data and carrier.
Supported profiles4/6 now offer their own Y/N choice, with staged target keyboard
validation and a clean view/reset baseline; see [PROFILE_LIVE.md](PROFILE_LIVE.md). CLI category overrides retain precedence.
Negotiated autobaud is preserved on unrelated saves. Successfully applying a
new source rate advances the remembered source baseline, allowing a later edit
to revert the rate without mistaking it for an unrelated autobaud change.
Connected COM migration, physical validation and the broader emulation collection remain unfinished;
see [SERIAL_LIVE.md](SERIAL_LIVE.md).

Configured display defaults are separate from transient BBS state. Unedited
wrap/scroll fields preserve the peer's current modes. Palette changes preserve
active SGR; a currently plain normal attribute can adopt the new normal color,
while other attributes take effect at the next relevant SGR operation. Only
changed configured defaults are patched into RIS state: applying settings does
not capture the current cursor, margins, modes, SGR, tabs or keymap as defaults.
Unless a profile switch is explicitly confirmed, the existing screen is retained;
newly received characters use the active values.
No initialization, dialing or hang-up command is transmitted merely by saving.

Read, close, size, decoder or native-command-expansion errors leave active
settings unchanged and report failure. The child may have saved a file that
cannot be adopted; the parent does not undo or rewrite that file. The editor's
own checked replacement/recovery policy is in [SETUP_EDITOR.md](SETUP_EDITOR.md).

## Identity and ownership

The shortcut requires an explicit current-directory8.3 `@` leaf using letters,
digits, `_` or `-`. Normal startup still accepts supported drive-qualified and
longer PRM paths, but this editor workflow does not yet support those paths.
The editor rejects DOS devices and reserved recovery names before file I/O.

Startup binds the DOS canonical absolute PRM identity and original source baud.
Immediately before EXEC, the owner verifies the current lexical/canonical request
and retained directory context. A changed working directory cannot redirect the
editor to another same-named PRM. After child success the parent reads only the
bound absolute path, even if the child changed the current directory. Failed
canonicalization has no lexical fallback; unverifiable binding prevents setup
from starting while leaving the terminal usable. This is DOS namespace binding,
not a file-generation lock or protection against concurrent filesystem remapping.

Directory header/record selection stays frozen. It is never reread or replaced
while adopting PRM changes. Deferred accounting retains its separate live record
baseline; an accounting update does not create a spurious settings change.

The existing PROGRAM owner drains replies and physical TEMT, sends its owned
XOFF when configured, closes capture, preserves DTR, lowers RTS and releases the
UART IRQ before direct local EXEC. The child receives only the bounded filename;
COMSPEC/shell parsing is not involved. After validation/application, the owner
restores the screen/cursor/shape, UART format and ISR without discarding pending
RBR, then releases only its own software pause. NONE flow still cannot guarantee
incoming-data preservation while a child owns the machine. Competing local
owners and modem negotiation deny a second setup; Escape/Alt-X cancel a pending
launch. Unsupported-path/busy shortcut requests still need a complete visible
menu/error UI. Alt-S remains the upload shortcut.

## Evidence

`check_live_setup_owner.py` runs76 actual-terminal transaction cases with only
canonical/PRM file boundaries modeled. `check_live_setup_apply.py` runs27 actual
foreground application cases using kernel/BIOS/UART boundaries, plus the real
renderer/RIS code. `check_setup_live.py` retains32 invocation/handoff cases.
The production DOS editor test covers cancel, a declined baud save, live
normal color and accepted baud,7E2 line and software-flow saves. Four additional
profile cases check accepted/declined switches, explicit target F1 mapping and
missing-target-block preservation. After each return the peer receives typed bytes, sends
new display bytes and receives a fresh cursor reply. Exact screen attributes prove display adoption. An independent INT1C sampler
observes old/new divisor and LCR bitmaps; UART/vector/PIC samples prove final
restoration. The dedicated suites additionally exercise47 candidate-policy inputs,53 foreground
same-port serial handoff inputs and32 profile cases. COM coverage adds69 linked
resource-owner cases,33 complete foreground transaction cases and six actual
DOS production-editor scenarios with independent multiport sampling.

Run these through `./tools/build test-terminal`. The pure staging API is described
in [LIVE_CONFIGURATION_PLAN.md](LIVE_CONFIGURATION_PLAN.md); the full feature
inventory remains in [FEATURES.md](FEATURES.md). Hash-bound checkpoint evidence
is recorded in [validation/setup-live.json](validation/setup-live.json).
