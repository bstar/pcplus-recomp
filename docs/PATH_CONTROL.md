# Serviced change-directory command

The newer [original path-editor follow-up](PATH_EDITOR_PARITY.md) corrects a
one-cell error in the original capture decoder, restores fixed-width editing
and modal acknowledgement, and adds application-level DOS failure tests. Its
receipt supersedes this checkpoint's UI coordinates and interaction claims.
The lifecycle/storage checkpoint below remains historical evidence.

The optional `--path-control` parent implements original Alt-F7 through the
shared foreground viewer. It also enables the startup resource identities and
original command reference. The command is available directly, from Alt-Z,
and as Change directory in the File command browser. Escape and empty input
return without a change. The entry is initially blank, accepts 62 characters,
and supports cursor movement, insertion, overwrite, Backspace and Delete.

The recovered 58-byte path/drive helper remains exact in the linked image.
Its raw invalid-drive false-success behavior is guarded by the existing path
owner's independent DOS queries and rollback verification. The dialog follows
the observed original five-row cyan frame and magenta input field, with the
current directory in its header. It adds explicit busy/recovery notices.
This is a maintained serviced UI, rather than an assertion that the original
155-byte blocking dialog has been linked unchanged. Original observations and
REA anchors remain in [CWD identities](CWD_IDENTITIES.md).

The lifecycle captures the startup drive and absolute directory before `/S`.
Subsequent changes cannot replace that snapshot. Orderly shutdown restores it
after file/accounting cleanup and before final trap/exit cleanup. Restoration
is independently verified; failure retains a nonzero exit status. A failed
change rollback quarantines the path session and requests orderly exit rather
than permitting further terminal file operations. The standalone lifecycle
also permits explicit restoration retry; the application does not prompt for
a retry during shutdown.

The dialog admits changes only when the existing foreground readiness and
recorder-file guards allow them. UART receive, ANSI parsing, history and query
replies remain serviced while it is open. A small popup must redraw over the
updated BBS frame: the ordinary command browser intentionally retains a frozen
whole-screen view, which cannot simply be reused for this composition.
All DOS calls remain synchronous foreground work. This does not establish
lossless reception during arbitrarily slow physical DOS filesystem calls.

## Storage and identity

The candidate is `build/path-control-serviced-final-20261104/TERMINAL.EXE`, SHA256
`7da48f9c6fd0f1c6611f211cb823a5218068358d3fa23133b24edae64cffa569`.
Its FILE_CODE bank contains 3,560 bytes, including 76 bytes of lifecycle state
and 144 bytes of dialog state. Each of the three C objects contributes zero
DGROUP bytes. Near data/stack remains 65,488 bytes with 48 spare; resident code
is 65,332 bytes with 204 spare. The map/image inspector checks initialized
state sentinels, nonoverlapping extents, segment separation and retained bounds.

Disabling the feature reproduces the previous `d8e8b72` executable exactly.
The enabled parent reproduces byte-for-byte from 583 declared public inputs in
a fresh tree without Git metadata or original executables. The existing
deployment selector is unchanged; this is a development candidate.

## Evidence and remaining gates

The evidence receipt is [path-control.json](validation/path-control.json).
Component lifecycle coverage includes six DOS8086 workflows and 143 assertions:
snapshot reentry, cross-drive restoration, 65-byte startup paths, bounded
queries, injected verification failures, failed rollback quarantine and
restoration retry. Those injected failures are explicit diagnostic wrappers,
not claimed physical DOS errors.

Nine application workflows pass 219 checks using DOSBox-X built-in DOS,
an 8086 CPU, COM3/IRQ5, a
synthetic serial modem and a passive video observer. They cover dialog
geometry/attributes, direct/reference/browser entry, cancel, empty input,
relative and cross-drive changes, failed-path retry, editing, startup-drive
and directory restoration, live UART queries and final hardware restoration.
The live-popup case captures updated UART text outside the frame while the
dialog remains visible and checks its cursor-position reply. An unchanged
earlier frozen-popup image fails that simultaneous-capture test while its
ordinary serial/query checks still pass.
The production resource-identity and stock Enigma/Synchronet editor checks are
separate evidence, rather than substitutes for the dialog tests.
Three startup/live-setup/accounting workflows pass 90 checks; production
PRMEDIT open/cancel passes 31 checks in each enabled/disabled parent with their
different final-CWD expectations. Each stock BBS editor audit matches all 1,920
logical screen cells and the independently checked cursor position.

Microsoft DOS 6.22, physical Boca/SPA2102/SynthModem acceptance, application-level
fault injection and complete file-owner combinations remain required. Immediate
menu-to-popup background composition and the full input/cursor contract still
need original-UI parity review; the live-traffic composition has its own check.
Gateway, File Directory, View a File and editor integration remain separate unfinished
file/DOS commands. This checkpoint does not establish complete original parity
or change the selected physical package.
