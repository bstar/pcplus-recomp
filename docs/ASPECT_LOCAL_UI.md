# Local interaction while ASPECT owns the session

## Confirmed query deadline gap

[Two frozen actual DOS runs](validation/aspect-window-query-failure.json) show
that the current blocking window delays an incoming CPR reply for3.449 and
3.448 seconds. Both fail the diagnostic's declared one-second deadline. The
reply is correct for the logical BBS cursor, the four query bytes are observed
in the child's ring while the window is visible, and both scripts subsequently
finish with normal sampled hardware restoration. This does not establish the
timeout used by any particular BBS; it establishes a concrete compatibility
risk that the existing pause-then-navigation stock BBS tests cannot detect.

`standalone/test_aspect_window_query_dos.py` returns nonzero for this defect.
The separate `standalone/audit_aspect_window_query.py` verifies frozen-file
hashes, reconstructs the complete peer stream and CPR completion timing, checks
both binary identities, and compares the DOS serial capture and before/after
hardware snapshots. Its successful exit means the failure evidence is sound,
not that the application passes. Reproduce with a fresh label and the exact
terminal/runner hashes required by the diagnostic CLI.

The production controller currently keeps UART flow/error servicing alive but
pauses the VM's actual receive/matcher/parser work until dismissal. Correcting
this requires cooperative window ownership across normal VM safe points:

- Retain actual native receive translation, WHEN matching and terminal parsing
  in their ordinary order. Cursor replies must use that real live state.
- Save the updated BBS frame and cursor while the window is visible; expose it
  before parser/status drawing and repaint at idle boundaries. Avoid a full
  frame copy for each received byte.
- Consume window dismissal before the ordinary Escape-to-cancel policy. Keep
  the original extended-key and repeated Alt-Z behavior explicitly tested.
- Close the window before child END, external PROGRAM, lease revocation and
  parent view adoption, including errors; cleanup cannot call a retired child.
- Version the parent/child contract and reject older mismatched pairs before
  UART access. Preserve DS=SS, interrupt service and existing parser budgets.

This intentionally changes production scheduling for modern BBS compatibility.
The recovered176-byte blocking body remains an original-behavior component;
its existing exact-byte comparisons cannot prove the cooperative controller.
Query deadlines, sustained traffic/flow, WHEN transitions, carrier/errors,
script completion, actual stock BBS workflows and affected SIP/audio routes
must all constrain the new implementation.


The [current live-window validation](validation/aspect-script-window-live.json)
accepts the native script-time Alt-Z reference/help window in the production
terminal. Alt-Z during a script wait opens the window; repeated Alt-Z switches
reference/help pages. Escape dismisses it without aborting the script. Extended
keys remain queued for subsequent dispatch. Full local command actions during
scripts remain an application gap. The earlier audio driver's startup-readiness
gate remains appropriate for its foreground recorder recipe.

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
That component regression alone does not prove an actual DOS window or serial
continuity; the selected production checks below provide separate evidence.

```sh
./tools/build test-aspect-local-window
./tools/dev --command python3 standalone/check_aspect_local_window.py --original
```

## Production window and interaction boundary

`runtime_when_dispatch_key()` in `src/aspect/when_runtime.c` sends keys through
the attached parent renderer. `aspect_render_key()` performs the checked
synchronous request. The parent's checked KEY handler now routes Alt-Z to the
recovered176-byte window on its captured foreground stack. Other keys continue
through `terminal_key_output`; local command services not yet connected still
return typed error3. This window does not launch transfers or nested programs.

`src/terminal/script_window.asm` supplies source-owned reference/help text,
full4000-byte video and BIOS cursor/shape save/restore, and a guarded borrow of
the inactive redisplay frame. Native resource arguments are unused by these
maintained services and bind to the already initialized context word, avoiding
new near-data placeholders. The initial placeholders caused an unrepresentable
10000 stack endpoint in the largest mouse diagnostic; its failed link/source
snapshots remain under `build/aspect-script-window-dos/data-limit-failure-01`.
The corrected variant links at65520 bytes. Ordinary keyboard/mouse builds retain
112/64 near-data bytes and350/202 resident-code bytes spare.

Frame copies keep DS=SS and interrupts enabled by switching ES per cell. The
window never touches parent device ports or the parent's TX ring. Its separate
transport-only child callback services pending flow control and errors while
leaving raw RX queued for WAITFOR/RGET; it does not peek or consume Escape.
Callback errors force native window retirement through the matching frame
restore before propagating a typed error. Repeated Alt-Z uses the owned debug
callback; the previous unowned-debug failure guard remains intact.

Each renderer callback checks a 4096-operation allowance and an elapsed limit
of 72 BIOS ticks, approximately four seconds. It is a bounded rendering/key-output scope,
not a modal UI lifetime. The child owns the active UART lease; ordinary parent
UI/transfer loops cannot assume their own serial queues own incoming data.
The reference window has its own synchronous keyboard lifetime and transport
polling, so it can wait beyond that parser budget without extending the parser
budget. The ASIO descriptor remains version4/48 bytes; capability8 requires the
new callback and capability9 also supports experimental external PROGRAM.
Use matching rebuilt terminal/ASPECT executables: older capabilities fail before
UART ownership rather than silently omitting window flow servicing.

The production window passes17 CPU cases in each keyboard/mouse build. Five
actual DOS cases exercise both supported profiles and BIOS modes, Escape,
queued F1, repeat help and a subsequent regular command menu. A passive timer
observes100 window ticks and six bytes retained in the actual child's receive
ring; the script later renders those bytes, sends exact expected output and
returns normally. The callback client passes18 cases including pending XOFF
without dequeue; five actual DOS callback lifecycle cases pass. Ordinary key
output837 and menu153 inputs pass. A fresh original-free tree reproduces26
normal, mouse, experimental and supporting products exactly. Separate selected
recorder/replay regressions pass four DOS sessions on Synchronet and ENiGMA;
those BBS runs are compatibility regressions, not script-window BBS acceptance.

The later [stock BBS window audit](validation/bbs-script-window.json) now accepts
the actual window path on both owned Synchronet and ENiGMA fixtures. Reference
and help remain visible for120/119 BIOS ticks while ASPECT pauses, then the
script performs a read-only Files/Main or Messages/Main round trip. A separate
BIOS helper waits for the script's own completion marker before opening the
regular menu. The passive observer counts that menu only after DOS EXEC has
actually returned. All typed bytes match the accepted login prefix plus only
script navigation; both relays have zero errors, the three-key helper retires
and restores its timer, and DOS/UART/configuration checks pass.

The first witness could count the launching menu as a return menu, and an
initial Synchronet relay reported a reset with forwarded shutdown commands.
The stricter observer then rejected ENiGMA's fixed-delay parent-menu attempt.
Those runs remain retained. The accepted tests use the existing lab's blank
hangup configuration because its Hayes/Telnet model does not implement modem
escape mode, and completion-gated BIOS keys replace the post-script delay.
No production executable or server was changed for these corrections.
The ASPECT script pauses before its BBS navigation, so this does not establish
sustained data or terminal-query servicing while a window is open.

```sh
./tools/build test-terminal-script-window
./tools/build test-aspect-script-window-dos
./tools/dev --command python3 lab/bbs/script_window_dos.py synchronet --label NEW
./tools/dev --command python3 lab/bbs/script_window_dos.py enigma --label NEW
./tools/dev --command python3 lab/bbs/audit_script_window_dos.py \
  --label NEW --cohort build/bbs-lab/window-accepted-NEW \
  --output docs/validation/window-accepted-NEW.json
```

## Implementation and acceptance still required

1. Extend the implemented reference-window lifetime to full command actions.
   Preserve child VM continuation, native WHEN safe points, checked DS=SS stack
   slices and cancellation while defining the additional owner transitions.
2. Extend actual DOS coverage to wider hook, mouse and fault combinations.
   Outer-script Escape confirmation/decline semantics remain separate
   unreconstructed services; current outer Escape still cancels immediately.
3. Connect the actual maintained menu/help/redisplay and all advertised actions.
   Define serial handoff or checked child-transport servicing for actions that
   need it, including transfers and external execution. Nested ownership must
   be validated before an action mutates files, vectors, queues or settings.
4. Expand the six-byte/100-tick DOS checks to sustained pressure, flow modes,
   carrier changes and wider WHEN/cancellation/fault combinations. Retain exact
   stream, screen/cursor, continuation and keyboard-return acceptance.
5. Expand the selected stock BBS paths to wider interaction and affected audio
   routes with the current production pair. Keep physical modem tests and the
   remaining F02/F05/F13 requirements separate and open.

This selected window integration closes no full application or physical gate.
