# Experimental ASPECT standard overlays

The expanded GET/Help/notice overlay build passes the previously failing
six-file/graphics PROGRAM workload, source compiler lending and GET recovery.
The full Help composition gate now passes with mouse and BIOS-only input;
missing and malformed Help resources also return safely to the live terminal.
Packaging remains pending broader overlay lifetime/failure coverage and
BBS/package regression gates. Earlier failures below are historical receipts.
No installed package, selector, private configuration or call history changes.

This is maintained memory-layout work, not recovered vendor overlay code.
It follows the [disk snapshot experiment](DISK_SNAPSHOT_EXPERIMENT.md).
The [validation record](validation/aspect-standard-overlays.json) binds the
exact experimental binary and its passing and failing receipts.

## Layout and lifetime rules

`overlay_ready=True` in the process builder prepares separate GET root and bank
adapters and a separate Help code bank. It does not itself enable disk overlays.
`standalone/build_aspect_standard_overlay.py` relinks that prepared build with
Watcom's standard far overlay manager, sharing a code area between GET and Help.
All input objects are source-built; original executable inputs remain absent.

GET's six mutable checkpoint words move from replaceable CS into resident
DGROUP, using SS-relative access so an owned-stack native fault with foreign DS
can recover. Entry checks require the resident data stack. This is not a claim
of safe handling of arbitrary foreign SS. Keyboard, mouse callbacks, UART,
process and ordinary runtime code remain resident. Help's near allocator calls
use explicit far adapters to the resident allocation owner.

The overlay file has a root MZ image and a separate trailer. The experimental
builder measures and hashes both without applying ordinary no-trailer header
padding. It checks root manager/table/vector bounds and shared CS, resident
checkpoint bounds, far editor storage before DGROUP, `_NULL` first in DGROUP,
BSS before the final unchanged8192-byte stack, and a206-byte editor state.
These are checks of trusted linker output, not a general overlay-file parser.

## Two startup failures diagnosed

The first application layout exited255 before C main. A separate DOS CRT-spawn
witness captured stderr as `incompatible overlay manager` from both C: and D:.
The manual class order placed tables/vectors after a different resident bank,
outside the manager's CS. Putting the manager last fixed that first failure.

That intermediate build passed CLI help/usage but a simple script returned
runtime-state error10 at opcode00/step0. Its preloaded data section had `_NULL`
after the stack and far editor storage mixed into DGROUP's range. Removing the
manual ORDER lets overlay-aware DOSSEG order both code and preloaded data.
The final build passes help, invalid arguments and an actual simple script with
exact redirected stdout/stderr, expected exit status and preserved INT0 vector,
from both drives. These are standalone bootstrap checks, not ASIO acceptance.

The upstream loader's version check and DOSSEG rules are documented in
[Open Watcom loader source](https://github.com/open-watcom/open-watcom-v2/blob/master/bld/wl/ovlldr/c/ovlldr.c)
and the [Linker Guide](https://open-watcom.github.io/open-watcom-v2-wikidocs/lguide.html).

## Initial GET/Help checkpoint

The earlier GET/Help-only experimental ASPECT SHA256 was:
`b57eeb6b9f731a3c261de5ef50b186e88d7721323f71d8cb8931e591d7b34da9`.
Near code64340, GET4079, editor1544, Help6529, DGROUP40448, stack8192;
exact MZ minimum including PSP132816 bytes (page minimum133088).
The disk-snapshot control is byte-identical to its previous135040-byte minimum
build, giving2224 bytes of measured minimum-allocation saving. This does not
measure free runtime heap or prove nested-child capacity.

- Actual8086 standalone bootstrap: six launches,30 checks, exact outputs.
- Full parent386/UMB: GET editing with a retained open stream passes; framed WHEN
  divide and confirmed cancellation also pass with normal parent return.
- A separate8086 near64K-root probe passes600 callbacks, including reentry into
  sibling B before returning to A. This is a narrow ABI prerequisite.
- Heavy unobserved8086 workload reaches all six held files (`ACK6`) but returns
  runtime-state error10 at PROGRAM opcode9B/step20. It fails the required three
  graphics children, viewport, stream and same-process recovery acceptance.
  The origin of that state refusal is still unresolved; do not call it a proven
  memory failure or successful PROGRAM integration.

## Expanded notice overlay: PROGRAM capacity passes

The optional `--notice` relink also shares the6466-byte notice bank with GET
and Help. Its three mutable recovery words move to resident DGROUP with
SS-relative access and an entry stack check. A Help call must not erase its
caller's notice recovery frame when loading another bank. The root allocator,
mouse callback, UART, active PROGRAM controller and their return paths remain
resident. Normal non-overlay output remains byte-identical.

Expanded experimental ASPECT SHA256:
`59dba04d2fbde87a92bc5755384aed07103227d7ff9dacdaf04e58d4df65db2e`.
Exact minimum including PSP126432 bytes, page minimum126576, DGROUP40448 and
stack8192. This saves8608 minimum bytes relative to the disk-snapshot control,
including6384 beyond the GET/Help-only overlay. No stack, file-slot or512-byte
buffer capacity was reduced.

A passive386/UMB diagnostic of the earlier failure records process status4,
CRT errno12 and DOS error8 with no child started. The subsequent error notice
returns status7 (notice failure), causing outer runtime-state error10. This
establishes process memory pressure beneath that error; stream masking and
teardown completed and their owners retired. Diagnostic memory footprints are
separate from the unobserved8086 acceptance run.

The expanded build passes:

- The original unobserved8086 workload: six held files, all six ordinary file
  slots, three actual graphics children, actual WAIT Space, exact restored
  viewport cells, VT220/ANSI switching, missing-file recovery and four script
  calls within one parent. All30 final checks pass. The generic harness's
  intermediate banner check is replaced by explicit pre-reset CPR and exact
  post-reset viewport checks because EMULATE deliberately clears that banner.
- Six standalone8086 bootstrap launches and30 checks with exact output.
- Two full-parent386/UMB source compiler loans (startup and EXECUTE), exact
  compiled ASX, GET editing and continued writes through an owned open stream.
- Two full-parent386/UMB framed WHEN divide and confirmed cancellation cases.
- Independent cold source rebuild of1048 files with no originals, old objects
  or ancestor Git; exact parent, child, compiler and helper artifacts, plus
  exact replay of both source-lending cases.

The source test now requires the allocation/EXEC observer for lease acceptance.
Its stream expectation distinguishes a refusal's flushed prefix from the
successful stream's prefix plus edited GET value; it does not discard the
contents check. Early unobserved attempts and that stale expectation remain in
ignored receipts and do not count as accepted tests.

The [expanded validation record](validation/aspect-notice-overlays.json) binds
these receipts, including the failed Help run.

The earlier full-parent Help receipt reports notice input cause11, service4
(`MOUSE_MEMORY`), before a captured Help frame. That mapped code also covers
Help model and screen allocation failures; it did not establish a saved-mouse-
state failure. This is retained as a failed integration receipt. Consequently
actual Notice→Help bank eviction and
notice recovery are not accepted merely because their state is now resident.
Broader GET lifetime/WHEN tests, nonlocal recovery across real bank eviction,
overlay handle inheritance/failure paths, remaining Help memory pressure and
BBS/package regression gates remain open. Physical Boca/SPA2102/SynthModem/
Enigma acceptance is separate. Host remains last; no package is promoted.

## Help admission follow-up: allocations pass, service gate remains open

The later [Help-admission record](validation/aspect-help-admission.json) narrows
the earlier cause11/service4 failure. Service4 is a mapped `MOUSE_MEMORY` value,
also returned for Help model or saved-screen allocation refusal. The mouse
callback was already active and the notice was visible. It was incorrect to
identify the earlier receipt as failure to allocate saved mouse state.

An optional passive INT21 observer records requests after Help-key admission,
their actual carry/AX/BX results, PSP, DS, caller and near-heap boundary. In the
original notice-overlay child, the model allocation requests AH4A/BX8142,
but DOS returns error8 and largest extent7933 paragraphs, with curbrk40960 and
nheapbeg40448. This is a contiguous PSP growth refusal; no Help screen request
has occurred. Separate DOS allocations pin the near heap's ceiling.

`early_help_model=True` reserves the unchanged model before notice input takes
its separate mouse/window DOS blocks. A failed reservation still permits the
error notice, and its later Help request reports failure explicitly. Failed
mouse admission releases an unused reservation; a retained mouse owner retains
its backing until normal close/recovery. Missing-file fallback releases the
model before using authored static pages. Existing view/model release guards
still retain backing until both file and borrowed view have retired.

This resolves model admission: curbrk reaches44298. The next observed refusal is
then the actual4032-byte saved screen (AH48/BX252, largest free165 paragraphs).
The experimental `--program` relink also shares the synchronous PROGRAM
controller's1463 code bytes. Its mutable state already resides in DGROUP;
platform, keyboard/UART interrupt code and native external checkpoint remain
resident. This releases another1392 minimum bytes. All stack and buffer
capacities remain intact.

The resulting production-layout prototype is
`822897f0b67dfbfbe98bed8711cb1071417705ad9a75fdcd5138c88679fc7c05`,
minimum125120/page125200, DGROUP40464, stack8192:9920 minimum bytes below the
disk-snapshot control. Its saved-screen request succeeds. The same unobserved
8086 six-file/three-graphics/WAIT workload remains green. The reservation
component passes91 DOS checks, including admission failure, idempotence,
active-owner refusal, exact screen/JFT restoration, release retry and repeated
resource search/lifetimes. Disabled production bytes remain exactly the prior
disk-snapshot control.
Two full-parent source compiler loan/GET/open-stream cases and six standalone
bootstrap launches also pass. A clean1048-file export reproduces the exact
parent/child/compiler/helpers and replays both compiler cases. These passing
checks do not override the failed Help integration.

The initial full Help result was rejected. The diagnostic `program_result_probe` profile
records the notice service failure's source and execution context. With BIOS
input fallback, after successful4032-byte screen allocation, speaker polling
returns STATE4 with DS=SS37608, FLAGS7006h (IF clear), and UART status0. This is
NOTICE_SERVICE6, subsequently presented by the existing PROGRAM adapter as
serial error14/status4. It does not establish a UART failure. The later observer
audit below identifies an instrumentation-induced IF leak, so this receipt is
not evidence of an application interrupt-state defect. The diagnosis uses a larger marked diagnostic
child and BIOS fallback, not mouse-enabled capacity acceptance.

No application STI or weakened context guard was introduced. Packaging,
BBS/physical tests and full feature parity remain open.

## Observer correction and verified Help sub-gate

The allocation observer called the original DOS handler using its own
interrupt-entry FLAGS and forwarded that returned IF0 into the caller's frame.
It now forwards DOS's returned status/carry while retaining the caller's IF.
An actual8086 DOS control verifies successful AH48, failed AH48 and successful
AH4A: all three callers retain IF1 and carry remains0/1/0. A separate negative
control omits only that preservation and reproduces IF0 for all three calls.
An unobserved DOS baseline gives the same caller IF/carry values as the fixed
observer:512/513/512 when masked to IF and carry. The negative control gives
0/1/0. The older outer/nested EXEC observers use the same corrected forwarding rule.
The earlier speaker STATE4/IF0 observation was induced by the diagnostic.

INT10 function6F00 messages also do not establish corruption: the maintained
display detector deliberately issues that optional vendor probe in
`reconstruction/display_modes/detect.asm`. Unsupported replies are expected
when the adapter does not identify itself. Neither observation justifies an
application interrupt-state repair.

The Help fixture now allows a longer final-key delay, selects the current
browser key when Alt-Z belongs to the original reference, and stages the
parent's exact PCMETA/PCLINE/PCCOMP/PCCHAT modules using manifest hashes. These
fixture corrections do not turn the entire test green: it still times out on
parent keyboard/menu/hangup. Missing modules and old bindings were fixture
omissions; staging them did not resolve the remaining timeout.

An optional entry-only INT10 witness records bounded register/FLAGS rows and
two parent screen rows. On timeout, the parent Python process captures only
its owned emulator's observer allocation before cleanup. Exact resident code,
an allocated DOS MCB/PSP and the expected observer sample anchor that capture;
UMB backing may be separate from conventional RAM. The tool never reads the
physical PC. Failed snapshot attempts remain explicitly unverified.

`extract_notice_timeout.py` reassembles the exact observer, requires its bytes
to match the captured fixture, and uses the assembler's data-label offsets to
decode the verified image. Its10 Help sub-gate checks pass for the unchanged
production-layout child822897f0:

- Both actual Help topics and resource-search captures are present.
- The Help timer holds90 ticks; all five search/F3/no-match/cancel witnesses
  fire exactly once, without BIOS seed failures.
- The original popup and cursor restore exactly; the notice receives its own
  Enter, with status/key1/13 and service0.
- A real subsequent DOS child writes SUCCESS.OK; ASPECT exits0 and emits the
  password exactly once without BAD output.

This is evidence of child Help behavior and return from its modal frame, not
complete parent acceptance. The parent has not emitted the scheduled `ready`
or hangup, and its mouse-menu/action checks have not completed. A BIOS-fallback
capture additionally reports unsupported service3 at PAUSE opcode88/step17;
that path needs separate investigation. Both remain open rather than being
removed from the gates. The [correction record](validation/aspect-help-observer-correction.json)
binds these partial results, the negative control and a fresh1048-file exact
source rebuild with two compiler-loan/GET replays. No application bytes,
installed package, private settings or call history changed in this correction.

## Parent return gate: event-driven input (2026-11-08)

The later parent timeout was also a fixture problem. A bounded, entry-only
INT16 witness records the queued BIOS key, read function, caller, BIOS time and
child EXEC-return state without intercepting the BIOS result. The old timed
schedule delivered `ready` and Alt-X while `exec_done` was still zero, to the
child's actual BIOS reader. Parent state subsequently showed connected6, no
PROGRAM/menu/macro/redisplay owner, no paused transmitter and an empty keyboard
queue. Those observations do not establish a broken parent input path.

The fixture now sends one early Space to dismiss the startup splash. Its owned
timer then waits for actual child return and release of PROGRAM ownership before
seeding the browser key through BIOS AH05. With a mouse driver, it waits for the
existing independent mouse probe to select Snapshot; without a driver, it waits
for the actual menu and seeds Escape. Only after menu/redisplay ownership clears
does it seed `ready`, followed by Alt-X. It neither calls an application command
directly nor overwrites queued keys. Automatic LOGIN needs no extra return Space;
a new exact-wire check prevents accidentally sending one to the BBS. The old
wall-clock schedule remains available as `--timed-parent-keys` for diagnosis.

The unchanged parent a0e1b082 and application-layout child822897f0 now pass the
complete Help composition case, including real next EXEC, exact popup/cursor
restore, five resource-search witnesses,90 held timer ticks, retained receive
text, resumed parent typing and actual modem hangup. The mouse case also checks
callback suspension/resumption, foreign-DS invocation, menu mouse events,
Snapshot output and exact driver-state restoration. The BIOS-only case retains
INT33 removal/restoration checks and completes PAUSE without the earlier
unsupported-opcode report. No application code was changed to obtain these
results; the prior BIOS report does not reproduce with corrected input delivery.

See [the return validation record](validation/aspect-help-parent-return.json)
for exact receipts and limits. The INT10/INT16 diagnostic remains optional;
the complete mouse case is repeated without it. Earlier timeout captures stay
historical failures, not passing tests. Their first INT16 diagnostic lost its
function value to MUL's DX clobber; only its key/caller/EXEC-state evidence is
used. The corrected witness reloads the saved function after MUL. Empty-input
startup experiments did not pass observer admission and prove no application
behavior. All results are emulator evidence; no package, installed selector,
private settings, hardware or call history changed. Full original Help/ASPECT
parity, broader overlay acceptance and physical testing remain open; Host last.

## Cold source replay and resource failures (2026-11-08)

Missing LOCHELP.HLP exercises the built-in topic fallback; malformed data
exercises the explicit Help-resource error page. Both complete the held timer,
exact notice/cursor restoration, real next EXEC, resumed mouse/menu/Snapshot,
queued receive, exact parent typing and hangup checks. These are47 and48 checks
respectively, without the optional video/allocation observers. They establish
these two resource-failure paths, not arbitrary overlay I/O failure recovery.

`prove_compiler_bridge_source.py` accepts repeated `--help-checks RESULT.JSON`
arguments. It validates each passing report's binary/source bindings, exports
only allowed public source files, rebuilds the parent, compiler, prepared child
and final overlay child, and requires exact product identities. Help maps,
manifests and generated HLP are classified as product evidence rather than
copied into the source export; the resource is regenerated and compared exactly.
It then replays each supplied Help case, requiring identical check results,
Help/resource witnesses, observer bytes, companion bindings and serial bytes.

The1061-file Git-free export reproduces all eight bound products, including
LOCHELP.HLP, and repeats four full Help cases (188 checks: normal mouse,
BIOS-only, missing resource and malformed resource), plus two actual source
compiler-loan/GET/open-stream cases. See
[the cold replay record](validation/aspect-help-source-replay.json). This closes
the source reproduction gate for these workflows; it does not close the broader
overlay lifetime/handle-failure, BBS/package or physical gates.

A packaging review also found a concrete next gap: the current compiler-bridge
lab packager includes parent PCPLUS.HLP but omits the child's LOCHELP.HLP.
The Help fixtures explicitly stage the latter, so their success cannot prove
that an existing lab/release package has it. Preserve and bind that companion
before using this new child for the complete packaged BBS regression. No payload
or installed selector was changed in this checkpoint. Host remains last.
