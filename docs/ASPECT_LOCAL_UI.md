# Local interaction while ASPECT owns the session

The normal recorder software-audio workflow now passes, but local commands
during an active script remain an application gap. The audio driver's startup
readiness gate avoids interrupting a script; it does not implement this feature.

## Original behavior established by static evidence

The selected PCPlus 2.01 executable has SHA-256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
REA/Ghidra verified its initialized DOS load image in
`ev_e64adede842cb5581a5caa88c7267b5fe09e200a2aa6cbcc31d7beee9f04e6ab`.
These are analysis coordinates at load segment 1000, not a running DOS address.

The recovered WHEN service at CS:4DE9 reads enabled keyboard input and calls
CS:1604 for non-Escape keys. Existing controlled replay and native-source
boundaries are documented in [service timing](ASPECT_WHEN_SERVICE_TIMING.md).
The fresh CS:1604 dossier
`ev_7753758e6ef19f812067b801bd30a7ebb318af6547000bd2cfbd3e84236826fa`
confirms that an extended key with AL=0 uses AH to select an indirect near call
through DS:44E0, for scans up to 8C. The original table's scan 2C word is 56FE.
Its original file offset is 29E88; its containing table hash matches
`reconstruction/keyboard_mapping/provenance.json`. The table is in appended
overlay data, so the verified initialized-image mapping alone does not prove
its runtime contents.

The CS:56FE dossier
`ev_8c6397f7450acd0fef77d580471c22c3d1d6365d1693861c4ba15c016a200e06`
contains a contiguous 176-byte body. It writes DS:397A=29, saves a screen
rectangle, draws a window/text and polls CS:6530 until a key is available.
It consumes an ordinary low-byte key through CS:64FE, but leaves zero/E0
low-byte keys, 1C/1D/1F and the enabled hook character for later handling.
It then restores the rectangle and returns. This is a local window/keyboard
contract; it does not establish that all application menu actions work during
a script. The complete BIOS/DOS/UART/window interaction has not been executed
by this static investigation.

The private evidence bundle and reusable snapshot are retained under
`analysis/aspect-when/local-ui-20261022.*`; originals and REA payloads stay out
of public builds and Git. The REA session was closed after export.

## Current implementation boundary

`runtime_when_dispatch_key()` in `src/aspect/when_runtime.c` sends keys through
the attached parent renderer. `aspect_render_key()` performs the checked
synchronous request, and `src/terminal/aspect_renderer.asm` calls the shared
`terminal_key_output` service on the parent stack. The classifier deliberately
marks local services FFFE; `src/terminal/key_dispatch.asm` returns typed error 3
for them. This is why an early Alt-Z stops an active WAITQUIET instead of
opening the maintained command menu.

Each renderer callback checks a 4096-operation allowance and an elapsed limit
of 72 BIOS ticks, approximately four seconds. It is a bounded rendering/key-output scope,
not a modal UI lifetime. The child owns the active UART lease; ordinary parent
UI/transfer loops cannot assume their own serial queues own incoming data.
Removing the classifier rejection or extending the renderer timeout would
leave those ownership and servicing requirements unresolved.

## Implementation and acceptance still required

1. Add a dedicated checked foreground interaction lifetime, distinct from the
   bounded parser/render request. Preserve the child VM continuation, native
   WHEN safe points, parent/child DS=SS stack slices and script cancellation.
2. Reconstruct local window/key-consumption behavior against original-native
   replay, including an ordinary dismiss key, an extended key left queued,
   repeated Alt-Z, hook handling and Escape confirmation/decline semantics.
3. Connect the actual maintained menu/help/redisplay and all advertised actions.
   Define serial handoff or checked child-transport servicing for actions that
   need it, including transfers and external execution. Nested ownership must
   be validated before an action mutates files, vectors, queues or settings.
4. Test incoming traffic during a modal wait exceeding the existing 72-tick
   rendering budget. Verify exact bytes, no duplicate WHEN actions, no local
   scan bytes on the wire, restored screen/cursor, resumed script and normal
   keyboard operation afterward. Include cancellation and callback failures.
5. Repeat actual DOS/BBS workflows on ENiGMA and Synchronet and affected audio
   routes with the resulting production binaries. Keep physical modem tests
   and the remaining F02/F05/F13 requirements separate and open.

No production source changed in this investigation, and no full feature gate
is accepted by the static evidence.
