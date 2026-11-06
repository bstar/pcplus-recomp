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
