# Correction: Chat Alt-F6 requests Redisplay

Earlier Chat notes and the maintained internal CHAT_HELP flag misidentified
key6D00 as Help. It is the original Alt-F6 Redisplay/scrollback command. This
corrects the integration target; the current frontend still has no implemented
continuation for that result. It does not establish completed Redisplay inside
Chat or completed global Help.

## Static evidence

REA reopened the existing identified overlay15 analysis image,
SHA2564ae6ee164991ab772dcb0dba4974fe30d00ee97429719dbbe0b56d5756fbc868,
with its matching saved snapshot and Ghidra12.1.2 profile. No image was executed.
The recovered Chat branch at EA65 calls6B5A, D830,6B42 and6DCA, then returns
to the Chat loop. Existing controller assembly Evidence is
`ev_a1102a9ca1c8cd961517e2dcad8fe603db710c271e68720d8d8b574b349ebe0a`.

Fresh instruction Evidence
`ev_75e891dfc400c74ceab95549788b94abe6b93aff52e0ffb1228cf56e2144f731`
resolves the call target to procedure0x1d830. Its complete52-instruction view
`ev_bcc76b021eed706adc74b2fd7450379de1f7a32c4d711b922314572f337cca25`
reads4EBE,4EBA,4EC6 and4EC8. Independent recovered history provenance maps
these to history pointer/start/end/wrapped. The helper computes the prior
history position and enters D95C when history is available. It calls6BBE,
passes the returned words to4870, then calls6B42 and conditionally6DCA; those
state-preservation dependencies need individual verification. It temporarily
writes7A50=10000 and restores it from2068; that setting's meaning remains open.

D95C's complete pseudocode view
`ev_5cac34515179db6efb1997de9bb540a170b5193e7d2f4bba5e6a828a5e4059d3`
shows Escape exit, arrow/Home/End/Page navigation and letter commands C/F/W.
Those are static observations; the called command semantics still require
individual recovery. Its retained dossier is
`ev_48d4a2c32a7d9c67a9c139b5b256ec123f9c21fb1cff8ef9ba9182a9fc78ec18`.
The existing terminal dispatch and original-reference table already identify
6D00 as Alt-F6 Redisplay. Together these facts support the corrected command
identity, rather than a new generic Help page.

The generated analysis image has explicit loader/image-mapping limitations.
This pass did not newly match D830's complete underlying original-file slice
or run original PCPlus. The earlier Chat controller itself has the separate
original-byte match recorded in CHAT_NATIVE.md. No complete original runtime
behavior is inferred from the new pseudocode. The private saved snapshot is
`analysis/chat-pressure-redisplay-entry-20261106.rea.json`; REA closed normally
with15 retained Evidence records. It remains excluded from public Git.

## Integration requirements

The viewer needs a real suspend/resume boundary: Chat currently executes its
loadable module from frozen storage that ordinary Redisplay also owns. Calling
the viewer while the module retains that storage would overwrite live code.
Recover and verify the original entry/screen/cursor contract, preserve Chat's
session and normal underlay across the ownership handoff, then restore Chat
and receive/input service on return. Cover cancellation, carrier loss and
viewer/file operations without reentrant loading or leaking retained keys.

The legacy internal flag name may be kept as an ABI alias while its meaning
is corrected, or renamed during that integration. There is no justification
for substituting an unrelated Help view. Global Help behavior and Alt-Z are
separate remaining requirements, with their own original service evidence.
