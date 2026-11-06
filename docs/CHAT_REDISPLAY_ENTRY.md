# Correction: Chat Alt-F6 requests Redisplay

Earlier Chat notes and the maintained internal CHAT_HELP flag misidentified
key6D00 as Help. It is the original Alt-F6 Redisplay/scrollback command. This
corrects the integration target. At this initial recovery checkpoint the
frontend had no continuation for that result. The later opt-in
[Chat Redisplay integration](CHAT_REDISPLAY.md) supplies a maintained storage
lease and return; global Help remains separate.

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

The initial investigation did not match D830's underlying original-file slice.
The subsequent native-source checkpoint below closes that mapping gap; neither
pass runs the synthetic image or original whole application. The earlier Chat
controller has its separate original-byte match in CHAT_NATIVE.md. No complete
original runtime behavior is inferred from pseudocode. The initial private snapshot is
`analysis/chat-pressure-redisplay-entry-20261106.rea.json`; REA closed normally
with15 retained Evidence records. It remains excluded from public Git.

## Native entry and return recovery

`reconstruction/redisplay_entry/` now contains190 exact original bytes:
D830–D8BC entry141 bytes,4870–488E restore wrapper31 bytes and488F–48A0
fallback18 bytes. Each compiles to its original flat slice and relocatable OMF.
The source-only builder reads public assembly/provenance only. The optional
analyst audit separately matches identified original-file slices at offsets
104336,23152 and23183 through the loader source ranges. It checks that none
overlap replaced trampolines and that the static carrier contains identical
bytes. No analysis image is executable input.

Fresh REA assembly views `ev_c181d6a9f8a1abdc7f3343bf840f2802a1b010c4e570e47984dd278ff61d952d`
and `ev_5784e27c7be825d8b1df12ade511351b67be8cd0ed7d77cf6632f6e792d9b5d6`
complete the wrapper/fallback contract. Existing exact6BBE/7558 screen services
in `reconstruction/program_display/` and6B5A/6B42 cursor services in
`reconstruction/notice_window/` supply the dependencies, without duplicating
their recovered source. Combined with the entry, the CPU check composes470
bytes of native instructions. Heap, viewer, BIOS/CRT and alert endpoints remain
declared models.

The contract has several consequential details:

- `6BBE` allocates `display_bytes`, saves the frame and returns DX:AX. The
 entry retains both words across the viewer.
- `4870` tests both pointer words. A nonzero far pointer reaches7558, which
 restores the frame and frees it. NULL invokes488F; it never copies/frees NULL.
- Allocation failure does **not** prevent the original entry from calling the
 viewer or empty-history notice. Its fallback calls376D, then7722 with stack
 arguments100/440, then376D again. Static7722 evidence confirms the two-argument
 RET4 ABI (`ev_bff68d9907a2228106ed3622c3c421616dcac41b421990b0010ee52747526339`).
 No acoustic output is claimed. The maintained Chat owner should refuse before
 the handoff when it cannot fund safe preservation, rather than adopting this
 unrecoverable-screen behavior.
- `6B5A/6B42` nest cursor positions. Chat's outer save/restore surrounds the
 entry's own save/restore; one saved cursor word cannot replace both levels.
- `7A50` is the mouse X scale, independently mapped by the existing mouse
 reconstruction and PRM reader. The entry restores it from configured2068,
 **not** from its previous runtime value.397A=0x25 is the Redisplay help context,
 consistent with other recovered local-window help-context use.

[The checked receipt](validation/redisplay-entry.json) binds3460 source CPU
cases,3460 paired original-slice comparisons and a separate3460-case cold
source-only rebuild. The matrix covers25/28/43/50-row frames, direct CRT/BIOS
cursor paths, both conditional cursor-policy branches, zero/seven existing
cursor frames, a diagnostic caller matching Chat's nested call sequence,
empty/nonempty/wrapped history, arithmetic wrap, allocation failure, and all
four zero/nonzero far-pointer offset/segment classes. These are instruction
replays with explicit service models, not live DOS, serial or physical tests.

Reproduce under the pinned toolchain with fresh output directories:

```sh
./tools/dev --command python standalone/build_redisplay_entry.py --output build/redisplay-entry-check
./tools/dev --command python standalone/check_redisplay_entry.py --output build/redisplay-entry-check
# Optional identified local originals, outside the source build:
./tools/dev --command python standalone/check_redisplay_entry.py --output build/redisplay-entry-check --original
./tools/dev --command python standalone/test_redisplay_entry_cold.py --build build/redisplay-entry-check --output /tmp/pcplus-redisplay-cold-check
```

REA closed normally to ignored
`analysis/chat-redisplay-contract-20261106.rea.json`, retaining40 records.
This checkpoint changes no live application code, module ABI, selected package
or deployment. The controller's blocking D95C implementation is not integrated;
global Help, Alt-Z and the broader original-feature inventory remain separate.

## Integration requirements

The viewer needs a real suspend/resume boundary: Chat currently executes its
loadable module from frozen storage that ordinary Redisplay also owns. Calling
the viewer while the module retains that storage would overwrite live code.
The entry/screen/cursor contract above is now byte-checked in isolation.
Preserve Chat's session and normal underlay across the ownership handoff, then restore Chat
and receive/input service on return. Cover cancellation, carrier loss and
viewer/file operations without reentrant loading or leaking retained keys.

The legacy internal flag name may be kept as an ABI alias while its meaning
is corrected, or renamed during that integration. There is no justification
for substituting an unrelated Help view. Global Help behavior and Alt-Z are
separate remaining requirements, with their own original service evidence.
