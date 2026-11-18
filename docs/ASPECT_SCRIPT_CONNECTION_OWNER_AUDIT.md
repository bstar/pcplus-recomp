# Script connection owner audit

This is a read-only source audit of the capability27 checkpoint qualified at
`e619ed0`, using parent `build/screen-parent-v6-20261119`. It defines proposed
integration boundaries, not an implemented connection service or runtime proof.
No application, compiler, builder or checker was changed for this audit.
Original command semantics are recorded separately in
[ASPECT_SCRIPT_CONNECTION_RECOVERY.md](ASPECT_SCRIPT_CONNECTION_RECOVERY.md).

The existing PROGRAM release/reclaim machinery is useful, but it is not a
reusable child-to-parent connection lease. Calling the foreground dial path
unchanged would retire the running script's owner identity. Closing and reopening
the child's ordinary ASIO handle also ends the invocation's return contract.

## Existing ABI and ownership boundaries

| Interface | Actual contract and relevant limit |
|---|---|
| `aspect_render_request(operation,value)` | Near child cdecl, two caller-cleaned WORD arguments; invokes the descriptor's FAR entry with AX/BX. Parent returns AX and preserves all other registers and original FLAGS. Each side uses its own DS=SS stack. `src/aspect/resident_render_client.asm:83`; `src/aspect/resident_bridge.asm:1`. |
| Parent `render_body` | Requires actual DOS PSP, child DS, attached client, token/callback identity, active parent PROGRAM kind4, and no compiler memory loan. Existing field/window/snapshot guards remain relevant. `src/terminal/aspect_renderer.asm:357`. |
| `aspect_render_program_begin(save_screen)` / `end(view_reset)` | Near child cdecl. BEGIN checks child UART active1, owners and client, closes the parent's script window and records external render ownership. It does not acquire the parent's UART. END retires the render owner and checks the actual view; accepted result0, unsupported3 or serial14 retires the child-side owner. Other failures retain it for retry. `src/aspect/resident_render.c:46`; `src/terminal/aspect_renderer.asm:1019`. |
| Snapshot operations17/18/19 | Only while PROGRAM SAVE owner2; borrow the retained8000-byte parent frame, return its address as four tagged bytes, and release it explicitly. Not a connection state snapshot or UART handoff. `src/aspect/resident_render.c:89`; `src/terminal/aspect_renderer.asm:925`. |
| `aspect_process_serial_pause()` | Near child cdecl, requires IF1/IRQ0 clock and coherent live driver, drains flow/TEMT, snapshots actual child UART/vector, masks IRQ/IER and lowers RTS. Success sets `aspect_serial_active=2`; child queue/unread state stays owned, ASIO `returned` remains0. `src/aspect/process_serial.c:9`; `src/aspect/process_serial.asm:33`. |
| `aspect_process_serial_resume()` | Near child cdecl, bounded36-tick restore then force; restores the original child divisor/LCR/vector/MCR/IER and only its PIC bit. It intentionally rejects changed DTR and unsupported FIFO state. Thus it cannot adopt a new port, baud or framing unchanged. `src/aspect/process_serial.c:20`; `src/aspect/process_serial.asm:148`. |
| `terminal_connection_*` | Resident NEAR wrappers call exported `*_far` wrappers, which call NEAR `*_impl` in MODEM_CODE. No ordinary C argument frame; DS=SS/DF0, preserve BP/SI/DI/ES, other volatile registers/FLAGS follow each operation. `prepare` returns CF/error; `receive` AL byte returns CF1 consumed / CF0 data; `cancel` AX0 abort / AX1 online hangup. Start/poll outcomes are shared state, not an AX success API. `src/terminal/modem_abi.inc:1`; `src/terminal/modem_bridge.asm:1`; `src/terminal/connection.asm:1`. |
| Modem sender / response kernels | Existing bounded command expansion, response classification, paced sender, UART write/clock and notices are reusable lower services. Sender start takes SI, poll returns AX0 busy / AX1 done and attempts at most one physical write per poll. C callbacks explicitly copy1..4 caller-cleaned WORDs. `src/terminal/modem_sender.asm:1`; `src/terminal/far_bridge.inc:1`; `src/terminal/modem_abi.inc:23`. |

The bridge is synchronous and refuses reentry. A borrowed-parent operation must
not callback into the ordinary child serial/renderer path while the child is
active2 or the PROGRAM render owner is set. The existing callback dispatcher
rejects ordinary callbacks while `program_owned`; the normal child ready/owner
checks require UART active1 (`src/aspect/resident_render.c:125,317,489`). A new
connection request needs a distinct authenticated, owner-aware route rather than
passing through ordinary EMIT, STATUS or screen admission during dialing.

## Foreground paths that cannot be reused unchanged

1. Start and cancel call `connection_program_cancel_service`, mapped directly
   to `terminal_program_cancel`. Even if no PROGRAM is pending, that function
   clears `terminal_program_kind` to0 and resumes flow. The active child would
   then fail every parent renderer authentication requiring kind4.
   `src/terminal/connection.asm:196,770`;
   `src/terminal/modem_abi.inc:22`;
   `src/terminal/program_actions.asm:1104,1149`.
2. Start/abort deliberately clear queues and reset matcher/session state.
   Successful connect calls `connection_note_connected_service`, which calls
   `terminal_directory_script_connected` before deferred accounting. The current
   active PROGRAM guard happens to suppress another script, but the scripted
   connection contract must explicitly exclude automatic-script bit1 while
   adopting the original terminal/protocol/META/KEY behavior.
   `src/terminal/connection.asm:210,229,566`;
   `src/terminal/directory_accounting.asm:37`;
   `src/terminal/script_launch.asm:27`.
3. `terminal_directory_adopt` admits only foreground resource PROGRAM kind8,
   idle connection, empty rings and private resource transaction state. It is
   not a script-kind4 adoption API. It also stages the foreground compiled-script
   binding and a wider resource transaction. Reuse validation/lower kernels,
   not that entry's context assumptions.
   `src/terminal/directory_adopt.c:185`.
4. Ordinary renderer policy accepts only idle state0 or online state6 and an
   unscoped parser. A modal script dial must not weaken this policy globally.
   It needs its own short-lived display/parser authority, or defer all post-
   CONNECT raw bytes for the child to render after reacquisition.
   `src/aspect/renderer_policy.c:36`.
5. Foreground Escape/Alt-H/Alt-D go through ordinary command cancellation.
   Script Escape is a normal FAILURE1 result with continued execution, not
   `ASPECT_RUN_CANCELLED=13`. Do not use the child's ordinary cancellation poll
   as the connection dialog's Escape implementation.
   `src/terminal/transport.asm:592`; `src/aspect/runtime.h:7`.

Existing connection states are0 idle,1 initializing,2 sending dial,5 waiting
response,6 online,7 sending abort,8 DTR wait,9 online hangup and10 strict modem
initialization. Status0 idle /1 online /2 response failure /3 timeout /4 cancel /
5 hangup /6 carrier lost /7 internal /8 hangup failed are controller results,
not ASPECT FAILURE flags or runtime error codes.
`src/terminal/connection.asm:452,752,984`.

A hangup timeout can leave state6/status8 while DCD remains high. Start refuses
to blindly initialize such a live modem. Script result adaptation must respect
that real outcome rather than claiming ownership release from a command being
sent. `src/terminal/connection.asm:177,696`.

## Return publication and cache refresh

Ordinary `aspect_serial_close()` is a final invocation handback. It publishes
registers, copies the raw ring to parent storage, publishes status/count/flow,
sets ASIO `returned=1` last, and drops its private handoff pointer. Backend close
also retires the unread token. Ordinary `open()` refuses an attached renderer.
Consequently close/open is not a mid-script connection transaction.
`src/aspect/serial.c:235,273`; `src/aspect/serial_backend.asm:602`.

The parent validates more than the ASIO descriptor's magic. Final script return
compares live selected entry/record/projection against `_script_directory_*`,
the renderer descriptor, translation state, original ring state and immutable
carrier-policy bit. The register-enabled descriptor has its own copy and guard,
and register extraction compares its immutable bytes to the base descriptor.
Changing the live directory context alone makes final return fail.
`src/terminal/script_launch.asm:392,443`;
`src/terminal/register_owner.c:49`.

A mid-script connection commit must atomically rebase the relevant retained
base/v7 descriptors, guard inputs and directory/accounting snapshot while keeping
the same live client/register invocation. Do not call `terminal_register_prepare`
or detach/attach the register exchange: preparation clears integer registers and
string starts, while final publish consumes the exchange.
`src/terminal/register_owner.c:20`;
`src/aspect/register_handoff.c:24,29,40`.

There are two child directory copies:

- ASIO's private `directory_record[114]` / `directory_entry` populated on open,
  with `aspect_serial_directory_record()` currently returning NULL for index0.
  `src/aspect/serial.c:44,61,245`.
- Interpreter `runtime_directory_record[114]` / `runtime_directory_entry`,
  copied by `runtime_directory_reset()` at interpreter initialization.
  Every recovered D_* getter reads this interpreter record.
  `src/aspect/directory_runtime.c:18`; `src/aspect/runtime.c:162`;
  `src/aspect/runtime_bridge.asm:933`.

Refresh both copies after a successful selection/adoption, including terminal,
protocol, baud/line and accounting fields proved by the native family. Do not
call general `runtime_reset_native()`: it resets files, stack, WHEN and globals.
The working record's validity must be separated from selected index0: native
MDIAL changes the working record without an explicit E482 assignment in its
recovered body; DIAL selection0 also reads working fields. The existing
index0-means-no-record rule cannot represent that distinction. The exact MDIAL
selected-index behavior remains a native investigation limit.

FROMDDIR is a separate launch-origin WORD, not the latest dial selection. Leave
it unchanged across DIAL/MDIAL/REDIAL/HANGUP. Its child getter already refreshes
through the authenticated parent WORD query, unlike the D_* record cache.
`src/terminal/script_launch.asm:94,517`;
`src/aspect/terminal_builtins.c:13`.

The child transport also caches translation, software-pause and carrier policy;
its driver stores actual port/IRQ/divisor/LCR. Reacquisition must adopt accepted
new values while preserving the original process-shutdown hardware/vector
baseline and unrelated PIC bits. Plain PROGRAM resume restores the old values,
and intentional DTR changes currently become serial line error8.
`src/aspect/serial.c:43,67,241,306`;
`src/aspect/process_serial.asm:166,217`.

## Proposed bounded service

Keep the native command wrappers in a far child bank. Add an explicit capability
and connection transaction with one outstanding owner, authenticated at every
entry. A scalar staged request can avoid parent dereferencing arbitrary child
pointers; alternatively a bounded copied descriptor needs normal MCB/extent and
immutability checks. Connection results and runtime errors must be separate.

Suggested phases:

1. Validate operands/destination and the full parent/client/child owner context
   before changing UART or committed selection. Refuse field/confirmation,
   compiler loan, snapshot, existing connection transaction, parser continuation
   and competing file/display/hardware owners. Establish external render
   exclusion and child UART pause without publishing ASIO final return.
2. Explicitly acquire the parent UART and its raw ring on the checked parent
   stack. `terminal_program_restore_uart` is a useful no-RBR-discard restoration
   kernel, not a standalone complete lease. It assumes the saved PROGRAM MCR,
   selected parent port and ownership baseline; new transaction admission and
   release must provide those invariants. `src/terminal/program_actions.asm:939`.
3. Run a script-specific mode of the modem controller, preserving the live
   PROGRAM kind4/client. Suppress automatic scripts and ordinary PROGRAM cancel;
   retain the required notices, logging, carrier and native adoption/accounting.
   Bound pumping and cancellation; ordinary Escape completes local failure and
   cleanup, whereas invalid ownership/IO remains a typed runtime error.
4. Preserve the first post-CONNECT data and partial CSI exactly. The foreground
   path already stops reading once a match is present during state2; copy that
   invariant into the script pump. Do not drain an immediate CONNECT+banner
   burst through the modem matcher or emit/parser-process it twice.
   `src/terminal/main.asm:446`; `src/terminal/connection.asm:859`.
5. Quiet parent IRQ/IER; transfer accepted new raw tail and flow state in a
   defined order, including the child unread token. Existing pre-dial bytes may
   be intentionally discarded by native dial/reset semantics; establish that
   exact boundary from native evidence rather than silently preserving or
   dropping them. Enforce4096 capacity and explicit overflow failure. Rebind the
   child driver and both directory caches, rebase final-return guards, then
   retire parent connection/render ownership. Do not call `uart_enable`, which
   discards RBR; the existing PROGRAM return explicitly avoids it.
   `src/terminal/program_actions.asm:978`.
6. Publish the native selected-index output/FAILURE result only after coherent
   reacquisition. Preserve the script's variables, open streams, file position,
   WHEN state, launch origin and call stack. If hardware/client restoration is
   uncertain, retain/quarantine the owner for an explicit safe retry instead of
   resuming a mixed parent/child state.

The real handoff still needs tests for CONNECT+banner+CPR in one burst; failure
and Escape followed by script continuation; successful autobaud/port changes;
XOFF/CTS, DCD loss and hangup timeout; GET/WHEN after reacquisition; register and
held-file preservation; final guarded return after entry changes; manual0 working
record; and repeated commands without a second automatic script.

## Capacity and scope

The qualified parent has `_TEXT=65224` bytes (312 spare), DGROUP65520 bytes
(16 spare), CONFIG_CODE65439 bytes (97 spare), ASPECT_CODE15931 bytes and
MODEM_CODE4196 bytes. These are map/manifest observations, not budgets available
after the next feature. Keep transaction state CS-relative or in an explicitly
retained far data owner; put substantial new code outside _TEXT/CONFIG_CODE.
Existing MODEM_CODE and a new named far bank are practical places for the
controller. Use existing register/no-argument modem FAR entries instead of
duplicating resident wrappers, and account for every necessary new near gate.
`build/screen-parent-v6-20261119/terminal.map:51`;
`build/screen-parent-v6-20261119/manifest.json:21,318`.

This audit establishes source contracts and concrete integration gaps only.
It does not qualify any new DIAL/MDIAL/REDIAL/HANGUP implementation, original
runtime behavior beyond the separately retained native evidence, physical
modem/BBS operation, or full ASPECT parity.

## Follow-up: DOS PSP, handles and reset services

The synchronous renderer bridge switches SS/SP/DS, not DOS CurrentPDB. Its
`render_psp` deliberately reads the actual current PSP with AH62 and checks the
child identity. Running on the parent's stack does not make newly opened DOS
handles parent-owned. `src/aspect/resident_bridge.asm:133`;
`src/terminal/aspect_renderer.asm:350`.

There is an exact precedent for preserving this distinction. The compiler
lease DOS boundary performs file IO under the child PSP. Only SETBLOCK is
temporarily scoped to the parent because DOS can assign the resized arena to
CurrentPDB. That small AH50 bracket saves and restores the suspended parent's
PSP:2E/30 stack words, restores the original child PSP on success and failure,
and preserves the operation result. The overlay initializer uses the same
pattern. A broad switch around an entire dial dialog would need all those
guarantees, plus protection against callbacks, nonlocal exits and outstanding
handles crossing the switch. It is unnecessary for the current bounded readers.
`src/process/compiler_lease_dos.asm:154`;
`src/process/compiler_overlay_front.asm:389`.

The useful filesystem boundaries have these concrete properties:

| Service | Actual IO/ownership consequence |
|---|---|
| `directory_dos_read/page` | Direct `_dos_open/read/close`, local numeric handle, complete exact-size23050-byte stream plus suffix probe, commit only on success. Opens use the current child JFT if called from the bridge. `src/directory/directory_dos.c:72`. |
| Incremental `directory_reader_*` | Keeps a numeric handle in its owner across steps; open uses O_NOINHERIT. Close uncertainty enters RECOVERY and is not blindly retried. This owner has no PSP field, so a future bridge transaction must pin the same PSP/JFT until retirement or add explicit owner identity. `src/directory/directory_reader.c:52,65`; `src/directory/directory_reader_fs.c:4`. |
| KEY / KBD readers | Direct DOS local handles, full staged read and validation, close before destination commit. KBD seek uses AH42. O_NOINHERIT prevents nested inheritance; it does not move the handle to the parent JFT. Both result structures retain close errors. `src/key_mapping/key_actions_dos.c:42`; `src/key_mapping/keymap_dos.c:42`; `src/key_mapping/keymap_dos_fs.c:4`. |
| Binding existence probe | AH3D/AH3E on a local handle, same current PSP. `src/terminal/directory_keys_io.asm:7`. |
| Path/environment lookup | `resource_program_path` and `resource_pcplus_path` read an explicitly supplied PSP/environment image, not CurrentPDB. Continue supplying checked parent `process_psp` for parent configuration fallback; that does not require AH50. Canonicalization uses DOS AH60. `src/config/resource_path.c:49`; `src/capture/capture_fs.c:4`. |
| Directory replacement/accounting | Direct DOS handles, create/write/close/rename and recovery state. Open and cleanup must remain on one JFT. The existing deferred accounting hook is RAM plus AH2A until explicit flush; it is not native E20A's immediate partial-write implementation. `src/directory/directory_replace.c:97,126`; `src/terminal/directory_accounting.asm:37,72`. |
| Phone-log file owner | Retains one numeric handle and uncertain/recovery flags. It must not retain a handle opened on the child JFT for later parent-PSP polling. Connection notices/log-event callbacks therefore need an audited queue-only or fully closed IO boundary during the borrow. `src/directory/phone_log_file.c:17,83`. |

Keeping CurrentPDB as the child permits complete direct-DOS reads while its
held FILE streams remain open: DOS allocates a free child JFT slot and the
bounded reader closes only that returned slot. Parent C pointers and stack still
use parent DS=SS; no child CRT FILE operation is performed by these readers.
There is no reason to hide the child's existing handles merely to read a KBD.

`process_handles_begin/end` is an inheritance bracket for an actual nested DOS
EXEC. It masks chosen entries with FF and restores their exact SFT bytes, checks
the saved current PSP/JFT/capacity, and can expose temporarily vacant numeric
slots to another open. It is not a PSP switch or a general file-owner transfer.
Do not add it around a no-EXEC dial pump. Likewise, the child's
`runtime_script_files_external_begin/end` flushes and snapshots its own FILE
state for PROGRAM; it does not identify parent resource paths or authorize
another process's CRT to use those descriptors.
`src/process/process_handles.c:58,90`;
`src/aspect/script_file_runtime.c:103,154`.

A failed close can leave a parent-side owner containing a child-JFT handle.
Returning to the child is safe only if that uncertainty is retained and later
cleanup is either performed under the same checked child identity or is
quarantined. After the child exits, its numeric handle may denote an unrelated
parent file; never retry such a close under the parent's PSP. Synchronous
strict readers do not retry, but an incremental or phone-log owner needs an
explicit cross-invocation policy. The existing owner structs do not supply it.

Separate from JFT isolation, canonical file conflicts need a decision. Parent
capture reservations inspect parent owners; current child script FILE owners
store streams/descriptors/buffers but no canonical path. Thus neither existing
reservation system proves that an open script FILE cannot alias the directory
being updated. This audit does not invent a new restriction or assume DOS
sharing will reject every alias. Prove the required original sharing semantics
and add a concrete test for a held directory/resource FILE before claiming
arbitrary held-FILE/accounting compatibility.
`src/capture/capture_reservation.c:10`;
`src/aspect/script_file_runtime.c:26`.

The current RIS/reset path performs no file opening, heap allocation or PSP
switch. Its native width bank uses preallocated source-owned code/data and a
private stack. However, maintained `csi_reset_terminal` is explicitly distinct
from original20A4: it restores captured terminal ID and948-byte keyboard state.
Calling it after assigning a newly selected terminal would undo adoption.
The current setup profile transaction demonstrates staging old RIS, applying
the new profile, installing the staged keyboard, clearing tabs/view and
capturing a new RIS baseline. Script adoption needs the native E20A ordering
without adopting setup's confirmation/UI semantics.
`src/terminal/terminal_reset.asm:1,216`;
`src/terminal/setup_profile.asm:99`;
`src/ui/reset_bank_context.asm:49`.

## Follow-up: guarded continuation and hardware rebind order

The present input guard can be written exactly as:

```
G6 = parentPSP XOR parentDS XOR ringOffset XOR A510h
   XOR tableOffset XOR translationMode
   XOR preloadCount XOR preloadRead
   XOR selectedEntry XOR recordOffset
   XOR year XOR month XOR day XOR delta
   XOR renderOffset XOR renderSegment XOR renderToken XOR renderCapability
   XOR initialFlowFlags
G7 = G6 XOR registerOffset XOR registerSegment XOR registerBytes XOR registerToken
```

All terms are WORDs. `initialFlowFlags` contains peer-XOFF bit0 and tracked-
MODEM bit1 (numeric2). Final child close changes output count/status/flow but
does not replace this input guard. Parent `terminal_script_complete` reconstructs
G6 from its retained original ring metadata, current `uart_tx_paused`, saved
directory/projection fields and saved carrier bit; only after validation does it
install the child's output queue. Register extraction checks G7 relative to G6,
matching immutable descriptor bytes and matching carrier bit.
`src/aspect/serial.c:158`;
`src/terminal/script_launch.asm:412`;
`src/terminal/register_owner.c:42`.

Consequently a successful mid-script handoff must leave a new, internally
consistent retained input baseline. A proposed ordering is:

1. While the old child UART and client remain valid, preflight operands, FILE
   and VM ownership, current PSP/JFT, parent context and old guarded descriptor.
   Record a separate connection transaction token. Do not increment the renderer
   or register token or publish either returned flag. Quiesce the child with
   explicit cleanup ownership; parent authentication continues to see the child
   PSP and PROGRAM kind4.
2. Borrow parent UART and pump only the script connection controller. Keep raw
   post-match bytes in the parent ring until release. Resolve accounting for the
   old directory identity before replacing path/entry/record: current deferred
   accounting has one global count/date and flushes against the *current*
   identity, not a per-entry queue. Do not apply a pending delta to a new entry.
   If native E20A immediately persists the increment, publish the resulting new
   record as the baseline and do not project that same increment a second time.
   `src/terminal/directory_accounting.asm:37,84`.
3. Stage accepted parent configuration, raw-tail extent, ring offsets, software
   pause, carrier policy and the exact working114-byte record separately from
   the selected index. Complete fallible reads/close/adoption/reset work before
   releasing that staged result. A failed dial may still leave an intentionally
   disconnected modem; do not automatically restore a pre-dial online state.
4. Quiet the parent hardware. Validate accepted COM/base/IRQ/divisor/LCR/flow
   and the new child release/rebind capability before any final commit. Adopt
   the actual returned autobaud result (`connection_baud_index` and live
   `terminal_baud_low/high`), not just the selected record's requested rate.
   `src/terminal/connection.asm:535`.
5. Rebase the retained parent's ring metadata to the new preload baseline
   (normalizing read0 is possible), peer-XOFF input state and `_script_flow_flags`;
   update base v6 entry/record/projection/translation fields and G6, then its
   register-enabled v7 copy and G7. Keep parentPSP/DS, ring allocation, renderer
   identity and the current register exchange/token/phase unchanged. Keep
   both serial and register `returned=0`. Perform the correlated stores under
   transaction exclusion before ordinary requests or final-return checks may
   observe them. Do not call generic script prepare or register prepare.
6. Refresh both child directory caches, transport masks/table and carrier/flow
   state from the same accepted snapshot; copy the raw tail once with explicit
   capacity checks. Restore the child's IRQ/vector using the accepted settings,
   preserving the correct per-port exit baseline. Acknowledge this successful
   rebind before retiring the parent transaction/render exclusion or publishing
   native command results. Unknown rebind/ack outcomes retain a recoverable
   owner rather than enabling both drivers or silently continuing.

Those are new services to implement and prove, not current APIs. Scalar staged
read/ack operations can keep the parent from dereferencing arbitrary child
buffers. A commit or ACK must be idempotent for the same transaction and refuse
stale/foreign clients; parent staged data must survive a failed child read.

For intentional HANGUP, idle connection state0 is admissible on return; ordinary
renderer policy already accepts0 or6. The child can continue at UART active1
without being logically online. Do not map carrier loss or local Escape to a
sticky runtime cancellation solely to regain ownership.
`src/aspect/renderer_policy.c:36`.

Do not clear tracked-MODEM carrier bit2 merely because state becomes0. With that
bit retained, `serial_carrier_policy` plus physical DCDlow suppresses queued
XON/XOFF into the modem command interpreter. Policy0 instead means untracked /
DIRECT and allows flow. Existing parent final-return checks permit the tracked
bit to remain set while disconnected; keeping it unchanged avoids a needless
guard rebase for HANGUP alone. If the effective policy really changes, update
the base/v7 guard inputs, child `preload_carrier_policy` and live
`serial_carrier_policy` together. Old peer-XOFF and introduced pause state still
need explicit retirement after the session ends.
`src/aspect/serial_backend.asm:443,462`;
`src/terminal/connection.asm:395,717`.

Ordinary child open requires an asserted DTR baseline and clears its queue;
ordinary PROGRAM restore flags changed DTR as LINE8. A disconnected continuation
therefore needs an explicit rebind that admits the *expected* DTR state while
retaining real overrun/line/ownership errors. Do not clear a genuine sticky
serial error as part of successful command-result adaptation.
`src/aspect/serial_backend.asm:101,115`;
`src/aspect/process_serial.asm:166`.

For a port move there are two different shutdown baselines: the parent retains
the real pre-application hardware/vector baseline, while the child retains the
parent's quiet-port baseline captured when the child acquired its lease. The
child must retire the old port against its old baseline before the parent moves
that port to its pre-application state. Otherwise final child close can restore
old-port settings into the new port or resurrect the old parent ISR.

The existing foreground port handoff supplies a useful hardware sequence but
rejects script kind4: validate both ports/IRQ/BIOS entries and late arrivals;
restore old IRQ vector before old hardware; retain the original UART snapshot
for an IRQ-only move; capture the new port baseline for an actual port move;
seed the saved vector from the **new IRQ**; leave target masked/IER0/RTS-low for
format installation. Its same-UART IRQ-only path restores only the previous
owned PIC bit. Native `uart_restore_hardware_state` itself restores an entire
saved PIC byte, so a new long-lived multi-owner transition must preserve
unrelated current PIC bits explicitly rather than assuming that call does so.
`src/terminal/port_handoff.asm:19,192,249,268`;
`reconstruction/uart/core.asm:558`.

After acquiring the target, the parent must retain its target's original exit
baseline, the new child must capture that parent's target-quiet baseline, and
the parent PROGRAM return MCR/port/vector must refer to the accepted target.
Plain `aspect_process_serial_resume()` uses its saved old port-independent
register values and cannot perform that move. Same-port autobaud/framing needs
an accepted-format rebind without replacing the original hardware snapshot or
previous IRQ baseline. IRQ-only and cross-port changes require separate tests,
including shared IRQs, absent/conflicting BIOS slots and late RBR/DCD changes.

The admitted parent RPC stack is4096 bytes carved from its existing8192-byte
stack, with16-byte redzones; it is not the parent's whole ordinary foreground
stack. Strict readers alone have bounded locals, but composing resource staging,
profile change and replacement can nest multiple large C frames. Keep large
records/proposals in an explicit retained far owner and measure/check the real
linked call depth rather than enlarging the bridge slice or dropping redzones.
`src/terminal/aspect_renderer.asm:211`;
`src/aspect/resident_bridge.inc:9`.

## Capacity follow-up: PCCONN in an expanded exclusive snapshot extent

**The initial8192-byte PCCONN proposal is superseded by a measured10880-byte
compact allocation.** The controlled compact OMF probe passes40 cases/657
checks with3890 code bytes,16 initialized DATA bytes,2824 BSS bytes, a full4096-
byte private stack,32 guard bytes and22 alignment bytes. Its62 MZ relocations
occupy248 bytes within a288-byte header; retaining that whole header would give
11168 bytes. Observed stack high-water is214 bytes, not a worst-case bound or
permission to shrink the4096-byte stack. All71 data aliases and856 controlled
FAR calls were exercised. This proves a16KB candidate extent is sufficient for
the measured component, and8KB is not. Real parent resource/UI services may
need more space.

Receipt: `build/aspect-connection-compact-omf-final-20261119/result.json`, SHA256
`b6b7c031f986fd000c63fa0c921be7d804cbcd4682ba6d25055291278140ea88`.
The gateway switches private DS=SS to a guarded **synthetic** parent stack and
back. No DOS loader, actual parent service, UART/ASIO/IRQ/filesystem integration
or persistent state across module replacement is qualified by that probe.

A future connection owner may borrow at least16KB, or a separately bounded32KB
extent, within the existing63000-byte inactive snapshot without adding another
allocation or reducing its normal capacity. For example, offset16384 plus16KB
ends at32768, and plus32KB ends at49152, both below the61000-byte snapshot-image
alias. These are layout proposals, not granted lifetimes or established
application fits. PCCONN cannot coexist with PCCOMP/Line/Meta in an overlapping
extent; its exact range, all other content owners and retained state must be
checked before entry. The current compiler loader remains an8192-byte owner.

The qualified PCCOMP payload is3408 bytes plus73 two-byte fixups,3554 file bytes
total. Its target is `redisplay_snapshot+16384`, within a statically retained
8192-byte window. An inactive compiler module has no live state that needs to
survive the next load; the existing frontend reloads it before each new loan.
That fact does not make the compiler's8192-byte limit large enough for PCCONN.
`build/screen-parent-v6-20261119/manifest.json:1881`;
`src/process/compiler_overlay_front.asm:383`.

The full63000-byte redisplay snapshot is separate from the live63000-byte
history ring. Normal redisplay rebuilds the snapshot from the live ring on
opening. Thus previous inactive snapshot bytes do not need saving merely to
load a separately admitted PCCONN extent; no history capacity is reduced.
The existing compiler window16384..24575 does not overlap the compiler's saved
frame0..8005 or Alt-G's61000..62999 image. The larger proposed connection extent
must declare its own exact end and all occupied subranges. Chat,
directory and resource owners also borrow snapshot memory, so exclusivity must
cover them even where their immediate state lies below16384. PCLINE and PCMETA
begin at the same16384 offset and do overlap the proposed module directly.
`src/terminal/state.asm:319`;
`src/terminal/redisplay.asm:408`;
`src/redisplay/redisplay.c:458`;
`src/chat/frontend.c:64,108`;
`src/terminal/directory_resource_owner.c:28`.

### Existing machinery that can be shared

The shared Line/Meta loader already stores `owner_kind`,16 active descriptor
bytes and32 state bytes in CONFIG_CODE, not DGROUP. Compiler kind4 copies six
descriptor WORDs into this state and drives the same loader. It reads at most
512 bytes per poll, verifies exact EOF and successful close, compares CRC32,
applies at most32 ordered/nonoverlapping segment fixups per poll and publishes
phase2 only after completion. Partial failures stay non-ready. For compiler
kind4 READY does not call a UI entry.
`src/line_port/overlay_shared.asm:17,32,683,715,764,789,820`;
`src/process/compiler_overlay_front.asm:211`.

Module opening already resolves an exact sibling leaf from checked parent
`process_psp`, uses an80-byte private stack path buffer and DOS3DA0
(read-only/deny-write/no-inherit) under the caller's current child JFT. The
handle remains in the shared state until it is closed. A failed close sets
sticky `fatal`, marks the numeric handle FFFF and prevents a fresh ordinary
load; it is not blindly closed again. PCCONN must inherit that refusal rather
than clear `fatal` on retry.
`src/line_port/overlay_shared.asm:59,99,225`.

A common loader factor can accept a retained expected descriptor and an
authenticated owner kind, select the corresponding sibling leaf, initialize
the existing state, run the existing bounded polls, and release only an idle,
nonfatal, resource-retired owner. This avoids duplicating the compiler
frontend's start/copy/load/release implementation. Compiler-specific init,
parent-tail lending, screen capture and END verification must remain separate;
PCCONN must not call compiler init, BEGIN, resize, backup or FINALIZE merely to
obtain arena storage.

Current special cases need explicit extension, not an unguarded extra leaf:

- The loader bypasses UI admission only for authenticated compiler owner4 and
  suppresses UI initialization only for owner4. A connection kind needs the
  same non-UI distinction after its own admission. Otherwise it reaches Meta
  UI behavior or waits on foreground admission that is false during ASPECT.
  `src/line_port/overlay_shared.asm:715,823`.
- Compiler `load_module` bounds itself to64 polls. With an entire image/fixup
  table bounded to8192 and at most512 fixups,16 data polls plus EOF and16
  fixup polls fit that existing count. These are existing compiler bounds;
  derive a separate bounded count for the selected16KB/32KB connection format,
  including BSS/stack initialization and relocation work, instead of treating
  the compiler loop as an implicit new capacity grant.
  `src/process/compiler_overlay_front.asm:132`.
- Bounds must cover **payload +2*fixup_count + any EOF scratch byte**, not only
  payload. Existing extraction checks the full file fits8192, while the shared
  EOF probe writes at the first byte past the file into the arena. For a file
  exactly8192 bytes, use a separate private probe byte or require space for it;
  do not write into24576 for the existing compiler claim. Apply the analogous
  exact-end check to the larger connection extent. The compact MZ probe's248-
  byte four-byte-entry table is not the existing loader's two-byte-offset
  companion format; conversion/layout must be explicit. Likewise declare
  staging/data/stack extents explicitly.
  `standalone/compiler_lease_module.py:63`;
  `src/line_port/overlay_shared.asm:764`.
- Compiler `_compiler_overlay_loaned` reports only `bridge_active`, not every
  shared arena claim. New connection ownership must block compiler loading,
  ordinary rendering, field/GET, Help/PROGRAM/snapshot, Chat and other arena
  consumers through the authoritative shared owner/phase. Existing renderer
  dispatch checks only the compiler loan before ordinary requests; it needs a
  bounded new owner gate, with connection read/ack/recovery routed before it.
  `src/process/compiler_overlay_front.asm:295`;
  `src/terminal/aspect_renderer.asm:389`.

At connection BEGIN, require shared phase0/busy0/fatal0 plus authenticated child,
actual retained parent MCB/full extent, no compiler loan, no field/window/
confirmation/PROGRAM snapshot, no active frozen snapshot/viewer/index/export/
search or resource/Chat owner. Claim before loading or writing the arena. During
LOAD/READY/BORROW/REBIND retain the same owner. Ordinary calls must not poll the
module or reuse its storage. After its UART/FILE/transaction state retires and
no callback/return frame points into the module, save persistent connection
state outside the replaceable extent before releasing to phase0. The next
PCCOMP/Line/Meta/redisplay use may overwrite the module completely.

Connection restoration uncertainty requires a resident-visible quarantine
marker/phase; it must survive a nonlocal VM abort without executing discarded
module state. Loader close uncertainty already has resident `fatal`. Hardware
borrow/ACK uncertainty needs equivalent persistent exclusion, using otherwise
idle shared state words if their lifecycle is explicit. Revoke/typed-abort and
unexpected child termination may not simply clear the owner while its UART is
borrowed, nor invoke compiler `_lease_info` against PCCONN bytes. Existing
compiler revoke deliberately fail-stops on an active invalid loan; that is
precedent for containment, not a connection cleanup implementation.
`src/process/compiler_overlay_front.asm:298,553`.

### Extraction, native DS and permanent footprint

The current whole-PCCOMP extractor asserts that every segment relocation inside
the module refers only to its own extracted span. PCCONN needs parent UART,
filesystem and display callbacks, so that extractor cannot be used unchanged.
Line/Meta extraction already handles source-linked, matched-parent-relative
segment imports, removes only declared MZ relocation words and rebases the
remaining parent/modules consistently. Generalize that machinery with an
explicit measured connection extent of at least16KB and a new metadata anchor;
retain checks that resident
code/data do not share an extracted segment base, fixups do not overlap and
other transient modules do not import this module's replaceable code.
`standalone/compiler_lease_module.py:20,58`;
`standalone/line_port_overlay.py:29`;
`standalone/meta_overlay.py:23,42`.

CRC32 is corruption detection, not cryptographic authentication. The application
must still use the matched parent's source-built expected length/CRC/relocation
descriptor and the authenticated client/arena owner. Do not let the child choose
an arbitrary module path or descriptor. The new18th companion also needs package,
archive, module-forgery and cold-source binding; current17-file contracts do not
implicitly cover it.

Recovered connection source has1527 native bytes plus the reused576-byte dial
attempt, before adapters and data. Its71 imported data symbols have native
near-DS semantics and cannot be allocated in the parent's16-byte DGROUP spare.
The exact layout constraints include the114-byte working record, fifteen
seven-byte selection slots (105 bytes), a201-byte indexed selection marker area,
and record aliases. Two81-byte staged string buffers add162 bytes. Together
these named pieces account for2685 bytes before other native state/constants,
callback adapters, fixups and private stack. This preliminary sum is superseded
by the10880-byte compact allocation above; it never established an8KB fit.
`src/aspect/connection_commands.asm:3,275`;
`reconstruction/aspect_connection_commands/provenance.json:data_layout_constraints`.

A viable module must therefore either use a compact private DS=SS context
inside the separately admitted larger extent or provide explicitly maintained OMF CS-state
bindings checked against the unchanged flat native component. A private
context can contain code/data/stack without another DOS allocation, while the
resident UART ISR retains its own saved parent DS. Its local near wrappers
must call existing parent FAR services through an explicit DS=SS/stack adapter;
they cannot recursively call the busy outer `resident_bridge_entry`. Any new
per-service near resident thunk consumes the scarce permanent budget, so use
the existing exported modem FAR services and a small shared callback dispatcher
where the exact callee ABI permits it. The compact probe measures that mechanism
with controlled callbacks; actual parent argument/return semantics and full
resource stack usage remain required evidence.

Persistent additions include module identity/entry metadata, the sibling leaf,
authentication/dispatch/retirement glue **and the full native REDIAL selection
state**. A six-WORD loader
descriptor is12 bytes; adding magic/version and an entry offset makes18 bytes,
and `PCCONN.OVL` including NUL is11. Those29 bytes are a data accounting example,
not an assembled frontend size. Existing active descriptor/state/owner storage
can be reused rather than duplicated; the162-byte staged strings and genuinely
per-attempt engine state can belong in the replaceable image. Source-level factoring can replace
existing compiler-only start/release code instead of adding another full front.

The fifteen seven-byte slots are105 bytes, including their consumed flags,
not merely the selected strings. Native REDIAL and DIAL with empty input reuse
that state across commands and foreground dials. The compact same-allocation
probe retains a consumed slot after DIAL200 then REDIAL; it does not preserve
the list across an overwritten/reloaded arena. Before release, the entire105
bytes must be retained outside all overlapping transient extents and restored
before the next native call. Foreground and script users must share one
authoritative list or use an explicit coherent transfer; independent reset
copies change semantics. Do not borrow the live N/S register payload for this
storage or assume unused record buffers are safe. A concrete retained location
and its cost remain unresolved at this checkpoint. The201-byte marker area's
per-attempt versus cross-command lifecycle also remains unresolved and must not
be silently classified as disposable. Other persistent engine fields require
the same explicit lifetime decision.

There is no source-only proof that this glue and retained connection state fit the observed142-byte total
co-residency margin, especially after the proposed child near-gate additions
and paragraph rounding. A2KiB *resident* implementation demonstrably does not;
the transient design removes that specific cost. Acceptance still requires
the new linked retained extent plus child/environment/actual heap growth to fit
the unchanged8086 full observer, along with exact load/refusal/reload/recovery
and same-parent PCCOMP→PCCONN→PCCOMP/GET/Help regressions. No arena, history,
snapshot, stack, variable capacity or observer assertion may be reduced to
obtain that result.

The later optional ASIO change saves5040 exact bytes in an unqualified build.
Its full software suite is pending; that measurement is not production memory
headroom or permission to relax any acceptance gate. The measured compact
component and larger-extent proposals do not establish a new parent profile.
At this pause checkpoint the remaining questions are the authoritative retained
selection/marker state, full resource-service size, loader/exclusion/recovery
integration, guarded UART/ASIO rebind and unchanged full8086 capacity acceptance.
