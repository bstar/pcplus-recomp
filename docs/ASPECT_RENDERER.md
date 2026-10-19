# Shared terminal renderer during ASPECT execution

The source-built DOS terminal now lends its actual terminal engine to the
ASPECT child. A directory login script can consume a CONNECT/banner burst with
WAITFOR while ANSI queries are answered by the same engine that owns the parent
screen. The parent retains the resulting cursor, screen, modes and history when
the child returns. This is an integrated, bounded renderer service; it does not
complete the application or the ASPECT language. Full-application gates F01–F16
remain open.

This checkpoint supersedes the **integration status** in
[ASPECT_RESIDENT_SERVICE.md](ASPECT_RESIDENT_SERVICE.md), which remains an
unchanged record of the earlier mechanical proof. The new checkpoint is bound
in [validation/aspect-renderer.json](validation/aspect-renderer.json).

## Frozen products and execution path

| Product | SHA-256 |
| --- | --- |
| TERMINAL.EXE | `dacbd777fbd5afaf441ad46ec559be2b95c53fd5ba9c1219ebfb865cd48e66ae` |
| ASPECT.EXE | `3369c3cb30c55153ad009be1c244af52efdb11117e5efd9d877fe50651d2ddbf` |

The parent and child are built from source; the checkpoint records no original
executable inputs. The linked parent uses 65,488 near bytes (48 spare), 65,024 resident code
bytes (512 spare), and 2,904 bytes in ASPECT_CODE. The child runtime remains a
trusted-source, partial 63-slot
ASPECT implementation. Recovered native instructions and the maintained lease,
rejection, cancellation and ownership policies are distinct parts of the build.

The native receive path is significant. Resident 4C3C selects display using
E37E; COMGETC/CD's 4C4F also considers E382. Native 4C74 translates a lead byte
once, performs the pattern/event-monitor step, and calls resident 0610 when
selected. E382 is the shared native gate/suppress-echo word. It is not a separate
independent child variable. The terminal parser synchronously consumes raw
continuation bytes: UART dequeue masking applies, but input translation and the
WAITFOR/WHEN matcher do not run a second time. Native DA/DSR reporting executes
during parsing, before the script proceeds to its next statement.

The service calls the existing native input, escape/CSI, text, cursor, erase,
scroll and reporting implementations. It does not recognize queries in a host
adapter or inject canned replies. Relevant sources are
[aspect_renderer.asm](../src/terminal/aspect_renderer.asm),
[receive_policy.asm](../src/aspect/receive_policy.asm),
[input dispatch](../reconstruction/input_dispatch/dispatch.asm),
[escape parser](../reconstruction/ansi/escape.asm) and
[reports](../reconstruction/reports/core.asm).

ASIOv4 extends the existing descriptor to 48 bytes with a versioned far entry
and nonzero lease token. BEGIN validates the actual current child PSP, its MCB,
client record and callback extent; EMIT invokes the parent engine; END retires
child callbacks. The parent executes on a reserved lower 4096-byte slice of its
existing 8192-byte stack. The child callback uses its own bounded stack. Both
contexts retain DS=SS; the mechanical bridge preserves caller registers and
FLAGS except for the typed AX result. Entry geometry, suspended-stack separation,
guards and single-depth reentry checks precede use. These checks do not prove a
maximum stack requirement for every possible parser stream.

The parent supplies the renderer; the child owns raw UART reads, unread, send,
poll and typed error callbacks during the lease. Each EMIT has a 4096-callback
and 72-BIOS-tick budget checked at callback boundaries. Native partial-sequence
reads retain their bounded timeout. Unsupported services, cancellation and
callback failures unwind locally into the child rather than invoking parent
application shutdown. Once adopted, the parent view is retained even on child
failure; stale pre-EXEC screen/cursor restoration is skipped. MESSAGE and child
diagnostics use the shared engine. Token/MCB validation and callback retirement
are described by [resident_render.h](../src/aspect/resident_render.h) and
[renderer_client.c](../src/aspect/renderer_client.c).

## Supported admission and rejection policy

Admission supports native profiles 4 and 6 with initialized renderer state,
BIOS mode 3, 80×25 text, page zero, coherent cursor/viewport metadata and bounded
far shadow/history storage. The parent foreground is suspended in PROGRAM kind
4. Capture, printer, transfer and other conflicting owners must be closed and
unambiguous; enabled or queued sink paths are rejected. These are checked owner
states, not pretend closes.

[renderer_policy.c](../src/aspect/renderer_policy.c) is a maintained pure policy,
not a recovered native admission function. Full admission scans metadata and
bounded key strings at preparation/BEGIN. Per-control checks repeat dynamic
owner, geometry, mode and pointer invariants in O(1); immutable content scans
are not repeated for every received byte. This depends on suspended foreground
ownership and guarded renderer mutations throughout the lease.

Every nested 0610 call increments parser depth and passes control preflight;
depth outside 1–16 is rejected. Complete CSI mode lists are checked before any
member mutates state. The current policy rejects standard mode 4, private mode
3, mode 12 SET (including private SET), standard mode 12 RESET, and private mode
2 RESET. Native report-prefix no-op lists remain no-ops. CSI media-copy entry is
unsupported. Unsafe CAN/SUB flag paths and the unsupported VT path are rejected;
legitimate VT raw-continuation and supported DEC linefeed paths remain available.
Normal admitted mode/control behavior uses the actual native implementation.

No arbitrary bytecode, parser-depth, unbounded-input or physical-device safety
claim follows from this policy. WHEN scheduling and broader script/UI services
remain outside this renderer checkpoint. Capture/printer integration, unsupported
profiles/geometries and the rejected native branches require further recovery or
owned implementations before admission can expand.

## Actual DOS evidence

`build/aspect-renderer-dos/final-history/checks.json` records **10 cases and 300
checks, all passing**, against the exact products above. Expectations were saved
before execution. A controlled modem sends CONNECT and the initial banner in one
write. A passive source-owned INT21/INT1C observer records actual ASPECT EXEC,
child exit, parent JFT, sink owners, mode state and far history; it neither
parses ANSI nor supplies query responses.

| Case | Observed behavior |
| --- | --- |
| Queries before login | Actual CPR/DA precede explicit script password transmission; a later parent query observes the retained cursor. |
| Edits/origin/scroll | Native cursor, erase, insert/delete character and line, margins, origin, scroll and SGR produce expected screen cells. |
| Nested CSI control | BEL inside CSI parsing executes the nested native control path. |
| RIS | Native reset clears prior content/attributes and query handling continues. |
| Nonidempotent XLT | Lead translation happens once; raw continuation bytes bypass XLT. |
| Seven-bit input | Dequeue masking and raw parser continuation remain coherent. |
| Media copy | Typed rejection returns from the child; parent owners/JFT and keyboard remain usable. |
| Mixed mode list | Unsupported later mode rejects the whole list before earlier origin mode changes. |
| Fragment timeout | Native parser timeout unwinds cleanly; WAITFOR later returns false and the script exits normally. |
| Fragment Escape | Cancellation returns a child error while parent view, device state and keyboard survive. |

All cases check unchanged sink-owner snapshots and JFT, bounded far-history
state, and exact retention from child exit through parent return. Successful
rendering updates history. Physical CTS/DCD timing is not represented. The
wire-level nested test reaches depth two; component depth-16/17 checks do not
establish an arbitrary hostile stream bound.

The pure-policy report `build/aspect-renderer-policy/checks.json` records
**29,206 actual 8086 DOS assertions plus 21 independent CPU probes**, including
324 executed instruction addresses. Its object contributes 1116 bytes of
ASPECT_CODE and zero DATA/CONST storage. Separate current reports prove 22 parent
MCB/client cases, 14 child linked groups (38 inputs), and five actual DOS child
lifecycle/callback cases. These component tests isolate mechanical/device
boundaries; the 10-case product suite supplies the actual engine composition.

## Strict Synchronet result

`build/bbs-lab/script-login/render-v4-dac-sync/checks.json` passes against the same
terminal and child. The actual local Synchronet server is reached through the
modeled Hayes/Telnet modem and DOSBox-X COM2 at 19200, 8N1, hardware flow setting.
The directory-bound script explicitly transmits the selected synthetic password
once; credentials are not keyboard-injected. Authentication, resumed stock
editor interaction, exercised Home/End/Insert/Delete/Page/Tab/Ctrl-Y wire output,
draft abort, exact directory accounting and hardware restoration all pass.
The one-line page-key exercise demonstrates boundary handling, not multiline
scrolling. CTS is held ready by the emulated nullmodem. No physical RS232/Wi-Fi
modem claim or ENiGMA success claim is made by this checkpoint.

## Retained failures and corrective evidence

Earlier PASS labels are not substituted for the final composition proof:

* `build/aspect-renderer-dos/attempt-history.json` indexes the preserved attempts.
  Early actual-product runs never EXECed ASPECT because policy admission failed.
* The original policy header put two arrays in one declaration with `__far` only
  binding to the first under Watcom. The history check consequently compared its
  actual far segment with DS and rejected the real parent. A fixture sharing the
  mistaken declaration had hidden this integration defect. The fixed header has
  separate explicit far declarations. The independent CPU regression derives
  history layout from the linker map, requires its segment to differ from DS,
  and checks successful admission. Old header/report evidence remains in
  `build/aspect-renderer-policy/dos-run-002/`, including `binding-defect.json`.
* `build/aspect-render-client-history/pre-CLI-transition/` retains the child
  interrupt-window defect: DS changed before CLI while SS still belonged to the
  parent. The final child disables interrupts before changing DS; instruction-
  boundary, IF-obeying ISR injection and DOS callback checks cover the correction.
* `build/aspect-renderer-dos/final-candidate/` retains a failed authored timeout
  expectation. Native timeout returned cleanly; the final case checks that actual
  contract and delays resumed keyboard input until after the script returns.
* `build/bbs-lab/script-login/render-v4-ef3-sync/` retains the pre-fix strict
  Synchronet failure. The later `render-v4-dac-sync` result is a separate run.

Local raw evidence remains ignored. Public validation contains source/report
hashes and bounded conclusions, not original executables, private directory
records, private credentials or captured proprietary data. Recreate the checkpoint with
`./tools/dev --command python standalone/record_aspect_renderer.py`; it verifies
current source/report/product identities and writes a new validation record.

A later metadata-only terminal rebuild retained the exact product hash. Linker
map timestamps changed; the recorder regenerates the passive observer in a
temporary directory from the current map and requires exact assembly-source
equality with the observer used by the DOS run. It records both map identities,
without rewriting that run or claiming another DOS execution.
