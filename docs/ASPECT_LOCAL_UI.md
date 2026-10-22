# Local interaction while ASPECT owns the session

The production script-time Alt-Z controller is cooperative. The VM, native
receive/matcher path and terminal parser continue while reference/help owns
local dismissal keys. Explicit attached-terminal PAUSE now also services this
pipeline. [PAUSE validation](validation/aspect-pause-live.json) and
[PAUSE load validation](validation/aspect-pause-pressure.json) bind normal
parent `0eff2348` and runner `2c80e45c`; capabilities remain10/11 and the ASIOv4
descriptor is unchanged. Earlier receipts retain their historical identities.
Real flow/carrier faults, affected software audio, full command actions and
physical modem integration remain open.

## Explicit terminal PAUSE

`runtime_serial_wait_second()` calls foreground-only `runtime_when_delay_poll()`
when the terminal renderer is attached. A full native WHEN/key/carrier service
precedes each burst of at most64 translated receive leads. The clock is checked
after each completed lead; one elapsed BIOS tick ends the burst. This amortizes
window/WHEN RPC overhead while keeping the command clock advancing. Parser
continuations retain their existing72-tick/4096-operation budgets: a lead that
needs continuation processing can exceed one tick. This is not a hard real-time
bound on arbitrary malformed input.

This intentionally changes script scheduling: ordinary text received during
terminal PAUSE is translated, matched by native WHEN and rendered. A later
WAITFOR or RGET sees subsequent input, rather than that already consumed text.
Arm WHEN beforehand or wait for a prompt directly when the script needs to act
on arriving text. Raw ASIO, transmit pacing, parser callbacks and generic delay
services retain transport-only polling and queued input. WHEN CALL workers
remain deferred until the foreground PAUSE finishes. No separate ANSI query
recognizer is introduced.

Seven actual DOS query/WHEN cases cover plain terminal and help, transmit
handlers, deferred/framed CALL, multiple-handler order and exclusion of stale
text from a future WAITFOR. Replies arrive within11.6ms and four-second PAUSE
markers arrive after4.13–4.22 seconds. A separate actual DOS Escape case returns
error13 without transmitting its unreachable tail. Ten linked CPU cases cover
ownership rejection, closed UART, frozen clock burst limits, midnight wrap,
cancellation and raw-delay queue retention. Fifteen raw DOS receive cases,
16 linked renderer groups,28 linked keyboard cases and five DOS callback cases
also pass. An isolated build reproduces26 products without original inputs.

The sustained PAUSE6 workload sends9,114 paced ANSI bytes, receives44 correct
CPRs within60ms and verifies all1,408 character/color cells. All replies precede
PAUSEDONE, independently measured at6.258 seconds after HOLD. The observer
samples91 window ticks and a26-byte RX peak; this is not an absolute ring
high-water measurement or CTS/RTS/XOFF/XON pressure acceptance. The first
per-byte service implementation failed with serial error14 and malformed
replies under this workload; its frozen source/captures remain retained. The
accepted implementation uses bounded receive bursts.

## Current stock BBS checks

[Fresh recorder/replay](validation/bbs-pause-live-compat.json) accepts four
production DOS sessions on the owned Synchronet/ENiGMA fixtures with runner
2c80e45c. [Fresh window sessions](validation/bbs-pause-live.json) accept two more:
reference/help is observed for137 BIOS ticks on each board, scripted read-only
navigation completes, and the ordinary command menu opens after actual child
return. Exact whole user streams, server routes, timer and hardware restoration
are independently checked.

The first ENiGMA window attempt completed its script and restored DOS/UART,
but the banner-gated keyboard driver stayed at phase0 until its watchdog. Its
post-exit menu gate failed and remains rejected. The corrected test driver reads
only the passive observer's magic, successful EXEC-return, child-exit and exit-code
fields through the installed INT21 vector. It injects ordinary BIOS keys after
actual completion; it writes no product, serial or success-file state. The auditor
reassembles the observer, offset probe and keyboard driver and retains both
attempts. These are selected loopback workflows, with no current software-audio
or physical acceptance and no closure of full application gates.

## Earlier WAITFOR load and stock BBS checkpoint

The owned pressure peer sends44 packets containing9,114 ANSI bytes. Each packet
paints a separate32-cell tile with alternating red/green text and requests CPR.
An independent audit reconstructs every packet, all44 reply positions/timings,
all1,408 final characters and attributes, the complete outbound wire, normal
child exit and42-byte hardware restoration. The slowest reply takes59.31ms.
The passive observer samples96 visible-window ticks and a maximum26 queued
bytes while the window is visible; these samples do not prove the absolute
ring high-water mark. This is a paced COM1/38400 emulated-UART workload during
WAITFOR. Transparent sockets do not represent real CTS/RTS stalls, and this
campaign does not force software XOFF/XON thresholds or prove other waits.

Fresh production runs on both existing owned stock BBS fixtures also pass:
File/C recording, DOS ASPCOMP compilation, unedited replay and manual navigation
in four sessions; reference/help, resumed scripted navigation and an ordinary
menu after actual child exit in two more. Each BBS window is observed for133
BIOS ticks. Independent audits check the actual server route, whole typed stream,
normal UART/DOS return, timer restoration, generated BIOS driver and frozen
source/binary captures. `lab/bbs/script_window_dos.py` and its auditor accept
`--baseline-label` so a new product pair uses its own recorder/login evidence;
the default historical label still requires identical parent/runner hashes.
These window sessions pause before BBS navigation, so the owned pressure test
provides separate evidence for incoming traffic during the open window.

## Historical PAUSE-context deadline gap

A separate actual DOS test first waits for HOLD with help open, executes PAUSE4,
then waits for END. The peer sends a CPR query one second after HOLD. The correct
reply is delayed3.188 seconds and misses the declared one-second deadline.
[Failure evidence](validation/aspect-window-pause-query-failure.json) preserves
exact wire/cursor behavior, normal child return and hardware restoration. This
is a retained failure on the earlier0eff2348/fa026aa8 pair, distinct from the
older blocking-window failure; it does not identify any stock BBS timeout.

Source inspection shows `runtime_serial_wait_second()` using
`runtime_serial_pause(18)`. Its loop invokes transport-only cancellation/service,
which leaves receive/parser work for a later ordinary wait. The queued query is
processed when WAITFOR resumes. The foreground PAUSE implementation and its separate evidence above address
this selected deadline. Broader carrier/error and real flow-control behavior
remain required; the earlier WAITFOR load receipt alone proves no PAUSE fix.

## Cooperative production interaction

The KEY request opens a frame owner and returns instead of entering the
recovered blocking loop. At ordinary WHEN safe points the child requests
WINDOW_SERVICE and receives one checked WINDOW_STATE callback. Native keyboard
service is suppressed for that poll so an Escape consumed by the window cannot
also cancel the script. A retained extended key becomes available on the next
normal poll. Deferred parser/WHEN callbacks keep serial servicing active and
leave window-owned keys for that safe point, without re-entering the parent.

Before parser, status, script-label or break-notice drawing, the parent exposes
the saved BBS frame and cursor. The actual parser processes ordinary received
bytes, continuations and queries in their existing order. An idle service may
save the updated frame and repaint help; service with queued RX does not
repaint. Repeated idle requests for an already visible window do not copy the
frame again. No replacement query recognizer or replay queue is introduced.

Escape and ordinary dismissal, extended-key retention, signed hook comparison,
and repeated Alt-Z follow the recovered key-consumption contract. Scheduling
intentionally changes: script waits and execution can advance under the open
window. END, experimental external PROGRAM acquisition and lease revocation
close the owner and restore the latest frame/context; revocation never calls
the retired child. This requires matched capability10 normal or11 external
parent/child products; the48-byte ASIOv4 descriptor remains unchanged and older
capabilities fail before UART access.

The retained176-byte blocking component remains linked for original-behavior
regression. Its CPU proof does not establish the new scheduling behavior.
Separate cooperative checks exercise updated frame/cursor restoration, hidden
page changes, idle copy counts, key classification and parent retirement. Actual
DOS tests separately cover incoming bytes, query timing and script completion
without a dismissal key. Existing F01–F16 whole-application gates remain open.

## Historical blocking-window query deadline gap

[Two frozen actual DOS runs](validation/aspect-window-query-failure.json) show
that the earlier capability8 blocking window delayed an incoming CPR reply for3.449 and
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

That earlier production controller kept UART flow/error servicing alive but
paused the VM's actual receive/matcher/parser work until dismissal. The cooperative controller addresses that scheduling defect. Its ownership
requirements remain:

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

## Capability8/9 production window checkpoint

`runtime_when_dispatch_key()` in `src/aspect/when_runtime.c` sends keys through
the attached parent renderer. `aspect_render_key()` performs the checked
synchronous request. That parent's checked KEY handler routed Alt-Z to the
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
./tools/dev --command python3 lab/bbs/recording_dos.py synchronet --label COMPAT_NEW
./tools/dev --command python3 lab/bbs/recording_dos.py enigma --label COMPAT_NEW
./tools/dev --command python3 lab/bbs/script_window_dos.py synchronet \
  --label WINDOW_NEW --baseline-label COMPAT_NEW
./tools/dev --command python3 lab/bbs/script_window_dos.py enigma \
  --label WINDOW_NEW --baseline-label COMPAT_NEW
./tools/dev --command python3 lab/bbs/audit_script_window_dos.py \
  --label WINDOW_NEW --baseline-label COMPAT_NEW \
  --cohort build/bbs-lab/window-accepted-NEW \
  --output docs/validation/window-accepted-NEW.json
```

The independent stock-window auditor also requires the retained historical
failure cohorts named in its source. These local evidence archives are separate
from the source-only application build and are not distributed in Git.

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
