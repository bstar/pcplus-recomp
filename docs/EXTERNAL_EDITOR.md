# External editor recovery

The opt-in `--external-editor` terminal build restores Alt-A, the original
Alt-Z Editor entry, and the command browser's File → Editor entry. It runs the
configured external program through the existing guarded PROGRAM/COMSPEC owner.
This recovers the terminal's editor launcher; it does not recreate or bundle
the separate proprietary PCEDIT application.

## Original evidence

REA/Ghidra identifies the original Alt-A scan1Eh trampoline at CS:BA7B,
selecting overlay3:DDC8. Its100-byte controller reads the command at DS:1F22,
uses the same overlay3:DE80 parameter helper as the external viewer, appends
a space and the parameter input, and calls the native process controller.
The helper allows48 parameter characters. The separately copied original PRM
field at039Eh is corroborated by actual unmodified-original DOS execution.

The retained private evidence is
`analysis/pcedit-launch-static-20261106.json`, with controller Evidence
`ev_b956c185a93758aaec6ab7c15e7ba99238c273d38bc1623ca407ce4ac665b1e4`
and parameter-helper Evidence
`ev_3160b3304ed30f8a5c28125da3d41ffb88b1a843a598edef29dc66284b73cc77`.
The static target is an analysis-only overlay image. Only the unmodified
original executable, SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`,
is executed in the isolated original runtime tests; analysis images never run.

Eight original workflows cover relative/absolute paths, configured options,
literal spaces, empty parameters, Escape,48 characters and no configured editor.
The owned COM helper records its actual PSP command tail and current directory.
Empty parameters launch the child with an empty DOS tail; Escape and an empty
configuration launch nothing. An empty original setting displays
`Editor not defined.`; the maintained implementation uses the existing external
dialog with `External editor unavailable`. That error presentation is an
explicit difference, rather than exact native UI parity.

## Maintained implementation

The editor reads its own65-byte field at PRM039Eh, independently of the viewer
at035Dh. It rereads and checks that field before execution. Only a transient
copy maps the editor setting into the existing checked literal-command builder;
neither the PRM file nor accepted session baseline is modified.

The modal editor and viewer are mutually exclusive and share the same frame,
input, cursor and child-process ownership. Foreground execution uses the existing
UART, display, mouse, handle and trap restoration gates. Two additional bytes
in the retained FILE_CODE state select the command field; this candidate retains
the same65488-byte DGROUP and65516-byte resident code footprint as the reviewed
viewer candidate. The optional feature remains disabled in the reviewed package
recipe, and rebuilding that recipe produces the exact previous executable.

The maintained builder accepts64 configured command bytes plus48 parameter
bytes with checked bounds, rather than the original controller's80-byte
temporary. Literal spaces and command options are preserved without adding
quotes or expanding input. An empty/malformed editor setting refuses execution;
it never falls back to the viewer or launches an internal editor.

## Validation and remaining work

The [acceptance receipt](validation/external-editor.json) records12 actual DOS8086
editor workflows and six external-viewer regressions. Each checks the complete
2000-cell return frame, cursor and shape, child command tail/current directory,
unchanged PRM, subsequent keyboard input, fresh ANSI position reply, and DOS
hardware restoration. Seven native parameter rectangles match all710 bytes.
The maximum-length test exercises a64-byte configured command and48 parameters.
An intentionally different viewer command guards against accidentally using
the wrong field. Five damaged linked-analysis controls are rejected without
execution. A public-source rebuild checks both feature states.

The initial candidate omitted Alt-A from the C screen controller's direct-modal
classification. Its failed first test is retained locally and excluded from
acceptance; the corrected candidate routes the dispatcher and screen controller
consistently. No installed package, private setting, call history or bridge
service is changed by these tests.

Physical modem acceptance, editor invocation inside live Enigma/Synchronet
workflows, editor-specific transfer/carrier-loss composition, arbitrary third
party editors, and separate PCEDIT functionality remain open. Prior viewer
receipts are evidence for their exact prior executable, not automatic acceptance
of this optional editor candidate.

## Enigma, transfer and recovery composition

The later [launch diagnostic](validation/program-admission.json) corrects the
initial startup interpretation below. DOS EXEC succeeds with no DOS error;
ASPECT terminates normally with exit1, `ASPECT_RUN_OPEN` (cannot open script).
The parent and PROGRAM result agree. Thus a failed DOS load is ruled out for
this observed session; memory exhaustion remains an inference, not a finding.
The owned-script DOS3D/6C observer records no matching `SYNC.ASX` request.
Actual normalized path/CRT error and any alternative open mechanism still
require investigation before attributing the error to heap allocation.

This diagnostic uses a read-only timer witness and an owned-script-only DOS
wrapper in the existing UMB observer. Sixteen executions of the assembled
wrapper verify success/error carry, filter, register, stack and IRET FLAGS
preservation. Its extra INT21/INT1C hooks are retired after the parent exits;
the final actual DOS run passes the complete before/after hardware comparison.
Earlier diagnostic versions omitted that retirement and are excluded from
restoration claims. The report's `passed` means the failure evidence was
validated; `application_accepted` is explicitly false. The failed BBS workflow
has not been converted into compatibility acceptance.

A subsequent menu-consolidation experiment kept all18 editor/viewer modal
routes working, but increased retention by16 bytes rather than saving memory.
It was rejected and reverted. Neither application code nor selected package
changes at this diagnostic checkpoint.

The later [composition receipt](validation/editor-composition.json) extends this
same93f08d0c executable with an actual Enigma editor session through the current
SynthModem source. Alt-A runs the owned mode13h child, then the post-child marker
gates an exact4000-byte editor/cursor/shape return. Subsequent ordinary editing
and draft abort pass. Independent pyte interpretation matches1920 final cells
with zero differences. The editor setting differs deliberately from the viewer
setting; the receipt checks that the child used the editor's field.

This accepted path uses250ms input-sequence framing and20ms serial input pacing.
An initial run with framing disabled and2ms pacing restores the editor but fails
later editing semantics and final-screen comparison. A paired reviewed-v6
control with those same disabled-framing settings fails those same checks.
That bounds the result as an existing compatibility limit rather than an
editor-specific regression. The workstation's private preload already selects
250ms framing; these tests do not change or restart its service. TCP write
boundaries alone are not a universal stream-parsing guarantee.

Six further DOS8086 workflows launch the graphics child through Alt-A before
X/Y/ZMODEM receive/send, including binary bytes, ZMODEM escaping and same-session
YMODEM cancel/retry. All pass exact protocol/file/frame/owner checks. Four
carrier-recovery workflows also pass: loss during bounded text and graphics
children, and loss during a partial YMODEM receive or ZMODEM upload after the
child. Independent peers require actual protocol progress before disconnecting;
the parent redials and accepts fresh keyboard input in the same DOS process.

Synchronet is **not accepted** for this editor candidate. Its ASPECT login never
starts in the current constrained lab. A fresh runner rebuild matches the
reviewed23caac93 interpreter exactly. A paired run with the reviewed2d626fb0
terminal, same interpreter/proxy/fixture and the same verified upper-memory
observer/key-helper placements successfully logs in, invokes the external
viewer, restores the editor and aborts the draft. The new terminal retains
482880 module bytes versus482400 in the reviewed parent:480 more bytes, while
DGROUP and resident-code extents stay unchanged. This is evidence of a tight
parent/child admission constraint; a specific DOS allocation error has not
been captured. Fixing and verifying memory admission is the next application
gate. Do not promote this optional candidate on the strength of Enigma alone.

The first Synchronet attempt was refused by the stale ASPECT source manifest
before DOS started. A rebuild with a relative output path also failed before
producing the runner; the accepted rebuilt runner uses an absolute output path.
Those attempts are not BBS or application acceptance evidence. All failed actual
DOS runs remain retained and excluded from accepted-path claims. No package
selector, installed file, private configuration or production service changed.
