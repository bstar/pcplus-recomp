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
low-byte keys, 1C/1D/1F and a matching enabled hook character for later handling.
It then restores the rectangle and returns. This is a local window/keyboard
contract; it does not establish that all application menu actions work during
a script. The complete BIOS/DOS/UART/window interaction has not been executed
by this static investigation.

The private evidence bundle and reusable snapshot are retained under
`analysis/aspect-when/local-ui-20261022.*`; originals and REA payloads stay out
of public builds and Git. The REA session was closed after export.

## Executable native regression

`reconstruction/script_menu/window.asm` now reconstructs all176 bytes exactly
and assembles both flat code and relocatable OMF. Its analyst-only `recover.py`
requires the verified original; ordinary checks build entirely from source.
The [validation record](validation/aspect-local-window.json) binds2,064 CPU
cases and2,064 comparisons with corresponding genuine-original instruction
bytes under the same declared modeled services. The231 recovered keyboard
bytes execute directly, including the normalizers, queue/read/peek/poll paths
and repeated Alt-Z debug interception. Eight additional composed cases enter
through native WHEN4DE9 and the real1604 dispatcher with the original scan2C
table word, rather than calling the window directly.

The cases cover every low-byte value, enabled/disabled hooks, both BIOS modes,
3,000 empty polls before input, ordinary dismissal, extended keys left queued
and a second Alt-Z followed by dismissal. Native sign extension means hook
characters80..FF do not match the window's zero-extended low-byte comparison;
the regression characterizes this original behavior. Escape inside the window
is consumed as dismissal and does not invoke the script-abort service in the
composed cases. This is distinct from Escape at the outer WHEN wait.

Window, status, BIOS and debug callbacks remain modeled. The fixture checks
their arguments, saved-frame identity and restoration, remaining input queue,
stack cleanup and BP/SI/DI/DS/SS/ES preservation. REA confirms callee cleanup
RET6 at4056, RET2 at780E and RET6 at6BF0 in dossiers
`ev_9c5680c42a12034c026d4170883285f4ebd1b7b437b5279e30dec958893605b8`,
`ev_7f9e33fba53e582afe714539a420c24db117215acd4f03d96eaad33326e6d42b`
and `ev_da4d22527ec92140290dfc0bf6ed25718cfd1f69b992c196a4ebfdfc81b8dc13`.
The later private `local-ui-contracts-20261022.*` exports retain those dossiers.
No actual DOS window, UART continuity or production menu integration is proved.

```sh
./tools/build test-aspect-local-window
./tools/dev --command python3 standalone/check_aspect_local_window.py --original
```

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
2. Extend the established native window/key-consumption regression through an
   actual DOS view and the new interaction lifetime. Preserve ordinary dismiss,
   queued extended keys, repeated Alt-Z and hook behavior. Outer-script Escape
   confirmation/decline semantics remain separate unreconstructed services.
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

The maintained production terminal/ASPECT binaries have not changed. This
component recovery and controlled replay close no full application gate.
