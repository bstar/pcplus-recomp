# ASPECT PROGRAM notice input

The [current receipt](validation/program-notice-input.json) accepts selected
native mouse/BIOS input inside the ordinary ASPECT child. Previously these
notices used BIOS input alone while the parent mouse stayed suspended. The new
child owns a separate mouse callback and driver snapshot for the notice, then
retires that ownership before DOS frees the child. Unresolved ownership keeps
the image allocated through the existing DOS31 exit policy.

## Matching build

```sh
./tools/build program-notice-input
./tools/build test-program-notice-input
./tools/build test-program-notice-input-source
./tools/build test-notice-input-exit
./tools/build test-notice-input-exit-source
```

| Role | Product |
| --- | --- |
| Terminal parent | `build/terminal-mouse-notice-input/TERMINAL.EXE` |
| Ordinary sibling ASPECT | `build/aspect-notice-input-parent/ASPECT.EXE` |
| Separate fault diagnostic | `build/aspect-notice-input-fault/ASPECT.EXE` |
| Matching 51-field editor | `build/setup-mouse-notice-sound/PRMEDIT.EXE` |

Keep the ordinary child beside this matching terminal as `ASPECT.EXE`. These
are explicit experimental products. The four published mouse/sound baseline
executables retain their earlier hashes; ordinary 105-slot publication remains
unchanged.

## Configuration and input ownership

Capability16 adds read-only operation14: selector0/1 returns `F000h | scale`
for configured X/Y values1..999. Typed errors remain outside that tagged range.
The parent reads its accepted settings, including when no driver was acquired;
uninitialized native driver state cannot supply this policy. The query is
permitted during the existing PROGRAM lease without entering the parser, local
windows or transport callbacks. Capability15 sound policy remains operation13.

Native mouse, queue/default tables, guarded owner, DOS allocation backend and
input bridges live in `NOTICEINPUT_CODE`. Keyboard names are isolated from the
interpreter's BIOS-only reader; the bank aliases its BIOS selector to the actual
`runtime_keyboard_mode` word. The parent callback stays suspended throughout
ASPECT. The child validates scales, captures the current opaque driver state,
installs its own native callback, and restores its snapshot after notice cleanup.
Raw CLI input uses explicit8/8 defaults when no parent policy exists.

The native reader preserves mouse priority and distinct Enter/Escape peek/read
words. Input failures now use `NOTICE_INPUT` with the underlying status retained
in `service_status`, so they are not reported as serial failures. A missing or
unsupported storage API with no acquired mouse owner admits BIOS-only input.
The fallback checks its context/output extent and consumes no mouse queue.

Window/speaker quarantine keeps input ownership and private streams alive.
Outer recovery closes the notice first, then the input owner. Repair permits
retry; unrepaired ownership does not advertise a reusable VM or reach DOS4C.

## Exit lifetime

The CLI prepares the existing PSP/static-floor guard at startup, before its
application callback acquisitions. Input open repeats that preparation
idempotently. This specialization does not install a Ctrl-Break owner. Final
exit checks input/window and process, serial, handle and external-scope leases.
If a lease remains, it validates the current MCB and retains the complete current
PSP allocation and other DOS-owned blocks via DOS31, returning raw030Ah (778).
An invalid ownership/allocation boundary stops instead of falling into DOS4C.
The product neither invokes nor overwrites the changed driver vector.

Three actual EXEC tests cover ordinary close, deliberately held native input,
and the ordinary ASPECT executable after a controlled INT33 replacement. The
retained cases allocate/fill the largest free DOS block, verify retained code
and allocation boundaries, and invoke the known native callback afterward with
foreign DS/SS. Its queue remains functional. The actual CLI also retains its
typed input cause and busy PROGRAM owner. Test cleanup restores the known driver
snapshot and INT0; retained allocations stay until the private VM ends. This is
not a general retained-process unload mechanism.

The first retention fixture timed out before its witness. Its manual PSP shrink
could truncate the CRT near heap, and it used default code-bank packing. The
corrected fixture keeps the startup allocation and disables packing. The failed
files remain preserved and excluded; no single isolated root cause is claimed.

## Validation

| Check | Accepted scope |
| --- | --- |
| 3 ordinary input sessions | Native Enter/Escape, standard/enhanced BIOS, scales8/4,9/5,999/1 and sound0/1/FFFFh |
| 3 no-driver sessions | INT33 absent before startup through child exit; BIOS Enter at the rendered popup; original vector restored by the test afterward |
| 14 fault/retry sessions | DIV, foreign-DS DIV, typed abort, damaged/replaced windows and foreign speaker; 508 text bytes, private streams and subsequent DOS child preserved |
| Before-exit observation | Child callback matches the prior suspended registration before DOS4C; parent resume, menu events and full576-byte driver restoration follow |
| 3 exit tests | 305 checks total, including actual ordinary CLI quarantine and retained callback execution after memory pressure |
| Component fallback | 78 DOS checks, including distinct native peek/read, typeahead, invalid/foreign ownership and vector repair |
| Existing exit policy | 12 default exit-owner regressions |
| BBS sessions | 4 current-build ENiGMA/Synchronet record, DOS compile, derived PROGRAM replay and manual-navigation sessions |

The [BBS receipt](validation/bbs-native-notice-input.json) retains its independent
wire, server-route and executable audit. Original recordings remain unchanged;
a separately compiled wrapper performs the missing-target and successful-child
checks. These use owned loopback servers and the modeled Hayes/Telnet peer.

Fresh source-only trees reproduce the four matching products from641 files,
three exit-fixture products from270, and three BIOS/quiet products from87.
A separate632-source proof reproduces the four unchanged published products.
The raw-capture audit checks actual callback targets, queue/result words,
before-exit registration, exact42-byte UART/PIC/vector snapshots and parent
resource bytes. The no-driver variant claims vector restoration, not an opaque
driver-state comparison. Probes that query/exchange registration or inject
events/vectors/BIOS keys are explicitly active test instruments.

## Remaining work

The contextual Alt-Z diagnostic/shared UI remains disabled; direct KEY macro
playback is a separate application path. Full mouse-motion/repetition routing
outside notice lifetimes, broader views and arbitrary asynchronous faults remain
open. Retained input-driver failure through the complete terminal parent, real
DOS-kernel comparisons, and broader live Setup/editor/transfer workflows on this
exact build also remain open. DOSBox-X 8086 tests, injected events and muted
speaker-gate samples do not establish physical mouse, modem or acoustic output.
Full PROGRAM, F01–F16 and Boca/SPA2102/SynthModem acceptance remain unproven.
