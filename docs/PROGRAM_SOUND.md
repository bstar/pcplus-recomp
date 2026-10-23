# Native PROGRAM notice sound

The configured error and information sounds now have source-built native
implementations. Four units reproduce108 original PCPlus2.01 bytes; the existing
38-byte calibrated delay is reused unchanged. The linked `SOUND.EXE` contains no
CRT sound replacement and builds without an original executable or REA database.
This is the native foundation for the remaining application sound integration;
the production and experimental PROGRAM notice bindings still select quiet mode.

The [receipt](validation/program-sound.json) binds100 instruction-level original
comparisons, an actual8086 DOS diagnostic and a ten-source-only rebuild of six
products. Static provenance comes from REA/Ghidra12.1.2 inspection of the genuine
PCPlus2.01 image with SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Read and source-mapping Evidence IDs are retained in
[provenance.json](../reconstruction/program_sound/provenance.json). The full
REA bundle remains in ignored analyst storage. It is never an ordinary build input.

| Original CS range, end exclusive | Meaning | Bytes |
| --- | --- | ---: |
| 376d–378b | Error/information enable checks | 30 |
| 7722–774d | Tone/PIT/delay composition | 43 |
| 774e–775a | Error sound arguments | 12 |
| 7fa0–7fb7 | Speaker gate and PIT divisor writes | 23 |

Both configured wrappers check original DS:1d40 as a word: zero is quiet; any
nonzero value enables sound. The error path requests220Hz and duration15; the
information path requests440Hz and duration20. The tone routine reads duration
and frequency from near stack arguments, removes four argument bytes, and uses
DS:BX stack access. DS must equal SS. It writes PIT control B6h, computes
1193182/frequency, writes the divisor low/high bytes to42h, enables port61h bits0/1,
runs the actual calibrated delay for the low16 bits of duration*10, then clears
port61h bits0/1. Other bits are preserved from each immediate input read.

The generic native tone does not consult the enable flag. It checks neither zero
frequency nor quotient overflow. Tests preserve12 real DIV fault cases for
frequencies0/1/18, including the PIT control write that precedes the fault. Wrapped
16-bit duration multiplication is also retained. A caller with an already-active
speaker loses its two gate bits at completion: the original does not restore a
preexisting speaker owner. These are counterexamples to safe maintained admission,
not behavior to expose through a new application API without ownership checks.

The exact delay is a calibrated busy loop over the original floor/count words.
It does not use an interrupt-driven timer, poll UART, dispatch keyboard input or
accept cancellation. The DOS diagnostic supplies explicit floor0/count100 and
therefore does not establish a calibrated150/200ms duration. Its linked native
switches, direct tone, callee-pop stack, gate control and writable port61h bits2/3
pass under DOSBox-X's8086 CPU. Status bits4/5 are live hardware values and are not
incorrectly compared as stable outputs. The mixer is muted; no acoustic waveform
or physical speaker result is claimed.

Before enabling application sound, add maintained admission for valid frequency,
exclusive inactive-speaker ownership and finite duration; replace the blocking
wait with bounded UART-serviced polling; ensure every notice/outer-fault cleanup
silences the owned speaker; and connect the actual configuration setting through
an explicit far-bank ABI. Keep these maintained policies separate from the exact
native baseline. Macro keyboard, mouse/shared UI, wider video modes, BBS workflow
regressions, physical hardware and full F01–F16 gates remain open.

```sh
./tools/build test-program-sound
./tools/build test-program-sound-original  # Analyst comparison needs ignored original.
./tools/build test-program-sound-source
```

## Serviced speaker ownership and optional notice composition

The maintained [speaker owner](../src/ui/speaker.c) now supplies separate
start/poll/stop APIs in `SPEAKERCODE`. These do not replace the exact native
baseline above. They require foreground DS=SS and interrupts enabled, reject
frequencies below19Hz before any PIT write, admit only1–182 BIOS ticks with a
nonzero32-bit poll limit, and refuse an already-active speaker (either port61h
bit0 or bit1). Polling stops on elapsed time, invalid BIOS time or exhausted poll
budget, including BIOS midnight wrap. It neither dequeues UART bytes nor owns an
ISR. The caller must continue bounded polling or explicitly stop; this is not
an autonomous watchdog if a callback hangs forever.

The backend checks and publishes the generation/cleanup owner under a short
interrupt-disabled interval before its first PIT write. Generation skips zero.
Stop clears only the owned gate bits, preserving other bits from the immediate
input read, and publishes release after the hardware write. It never stops an
unowned active speaker. Invalid DS=SS/IF context retains ownership for repaired
retry. Inactive-speaker admission means the gate baseline is quiet; the PIT2
counter/mode is left programmed in mode3 with its gate disabled. Arbitrary prior
PIT modes/counts, noncooperating direct port writers and physical hardware are
outside this ownership contract.

All public owner operations cross an explicit far bank boundary. The builder
checks that the four near platform helpers share the owner's CS, that main has a
different CS, and that the C object imports no unexpected near CRT helper.
The optional notice diagnostic adds a third bank, `NOTICECODE`; no near sound
callback is incorrectly invoked from another CS.

`NOTICE_SPEAKER` enables the optional composition. Its private
[configuration API](../src/ui/notice_speaker.h) defaults to quiet and rejects
changes during a live notice/window/speaker lease. Explicit enable lets a NULL
legacy sound callback select the built-in220/440Hz tone. A supplied legacy
callback takes precedence. The ABI and quiet behavior of builds without
`NOTICE_SPEAKER` remain unchanged. The built-in error/information durations are
3/4 BIOS ticks, a maintained coarse timing policy rather than a claim of exact
native150/200ms calibration.

Notice service polls the tone while its existing callback can service UART.
Normal completion, service errors, deadlines and explicit outer unwind stop only
the notice's speaker generation. The notice reserves the expected claim generation
before entering start, so an abandoned claim remains identifiable. A foreign
stop/reopen is retained; configuration and a new notice reject until that owner
is closed. Retried cleanup preserves the original cause. An unwind attempted
with IF clear rejects without releasing either speaker or window; repair permits
retirement.

The [serviced receipt](validation/speaker-serviced.json) covers:

- 68 host checks of arguments, state/context, clock wrap/stall, budget and generation.
- 513 linked8086 checks, including196 instruction-boundary abandonment/cleanup cases.
  These cuts model a caller that already repaired DS=SS/IF; they are not actual
  asynchronous hardware/CPU faults.
- Sixteen actual8086 DOS COM1/COM2 N/S/H/B cases, with normal completion or an
  explicit early stop after508 queued bytes. All8,760 DOS checks pass; both tones
  retain exact peer input and continue the READY! exchange with exact flow bytes
  and restored UART/vector/PIC state.
- 49 actual DOS notice checks covering serviced tone completion, service-error
  cleanup, a real outer C longjmp, IF-disabled retention/repair, foreign-owner
  quarantine/retry, quiet mode and legacy callback precedence. All windows,
  screen/cursor and owned speaker gates retire correctly.
- A74-source-only rebuild reproduces both new diagnostics and both quiet notice
  components. The quiet component's583-check DOS regression passes. The separate
  237-source proof reproduces all35 existing PROGRAM notice products, including
  the unchanged ordinary and focused ASPECT executables.

The mixer is muted in DOS tests; acoustic waveform and physical speaker timing
remain unverified. The UART and notice lifecycle diagnostics are separate tests;
this is not yet a single attached PROGRAM/BBS sound workflow. Actual application
sound configuration, PROGRAM/outer recovery binding, original macro keyboard and
mouse/shared UI policies still require integration before normal publication.

```sh
./tools/build test-speaker
./tools/build test-speaker-notice
./tools/build test-speaker-source
```

## PRM-configured PROGRAM sound through the attached terminal

A separate experimental application build now connects that speaker owner to
PROGRAM error notices and the actual parent setting. Original DS1d40 lies within
the proved PRM memory image DS1b84..2073, giving file offset01BCh. The original
switch's REA Evidence `ev_b4bedd3b0c9c20f39dd5f250b025d498eb3c492b0c2861034eb3a518a67ecc41`
checks this word for zero. Startup normalizes0 to quiet and every nonzero word,
including FFFFh, to enabled. The existing44-byte settings ABI stays unchanged.

`--notice-sound` builds the matching49-field `PRMEDIT.EXE`; **Program sound** is
on the TERMINAL page. Viewing a noncanonical nonzero word preserves it. An explicit
edit changes only the two selected bytes; all other PRM bytes remain intact.
The standard48-field and mouse50-field editors remain separate products. The
combined mouse/sound editor and mouse-enabled sound parent are not yet published.
No default PRM or private configuration is supplied.

The sound-enabled terminal commits its private setting only after the full
startup import succeeds. Directory-startup failures also leave it unchanged.
Live Setup stages the image; only acknowledgement of a successful foreground
offer updates the setting. Cancelled, invalid and consumed offers cannot commit
it. Sound adoption does not change the existing serial/directory plan layouts or
force adoption of a deferred baud edit.

Renderer capability15 adds read-only scalar operation13. It returns FF00h/FF01h
or a typed error, preserving a distinct success range. The parent validates the
attached child PSP/DS and unreturned handoff before answering. This one query is
allowed during the PROGRAM lease; it draws nothing, consumes no receive bytes,
and enters no child callback. A12-byte far adapter in the child's near code
returns into NOTICECODE. The child checks the reply and configures the serviced
notice before drawing it. A raw CLI without an attached parent remains quiet.
Capability12/13 products retain their existing behavior and bytes.

The [application sound receipt](validation/program-notice-sound.json) accepts20
actual8086 DOS attached fault/recovery sessions plus three ordinary-product DOS
smoke sessions. The fault cases cover before/during/after-popup DIV, foreign-DS
DIV and typed abort, sound off/on, FFFFh normalization, guard damage, foreign
window replacement and foreign speaker replacement. Speaker-on faults observe
active gate bits before recovery; the original owned tone stops afterward.
A replacement speaker stays active while PROGRAM/file/view leases remain held.
Live retry and new VM entry reject; its owner can stop it and then retry cleanup.
Subsequent normal popups, source-built DOS execution, exact508-byte queued text,
parent resources, selected sound value and resumed serial input all pass.

The sound diagnostic adds a bounded, transport-only receive gate before the tone.
It uses the real UART poll and does not dequeue bytes, run WAITFOR, or inject
success into product services. This arranges the failure while the short tone
and508 queued bytes coexist. The before-popup fault retains its original scope.
An earlier script-level WAITFOR gate consumed three payload bytes and was rejected;
that failed local capture is not accepted evidence. The focused report appends
sound observations to the existing62-word schema; quiet diagnostics retain their
original124-byte report and executable bytes.

The ordinary-product smoke uses the actual ordinary child main, without the
fault driver or product patches. A passive INT1C observer reads speaker gate bits
while ASPECT EXEC is live. It sees activity only for nonzero settings, then verifies
successful DOS-child execution and continued terminal input. These are three
observed gate-state sessions, not recorded acoustic waveforms. All DOS tests use
a muted mixer; physical speaker/modem behavior and BBS audio remain unverified.

Forty-five linked settings cases cover atomic startup/directory import and live
offer commit/reject/abort. Twenty-one ordinary-editor field cases verify lossless
view, range rejection and whole-image preservation. A fresh tree of615 declared
sources reproduces the editor, parent, ordinary ASPECT and focused diagnostic;
it contains no original executable, install, private PRM, REA database or previous
objects. The standard237-source proof still reproduces35 quiet PROGRAM notice
products. Six cached quiet products retain their hashes; the cached mouse-enabled
attached parent was stale, and a fresh400-source rebuild from pre-change commit
8d555a4 independently matches its current executable exactly.

Build and test this matching set explicitly:

```sh
./tools/build program-notice-sound
./tools/build test-program-notice-sound
./tools/build test-program-notice-sound-source
```

| Product | Source-built executable |
| --- | --- |
| Editor | `build/setup-notice-sound/PRMEDIT.EXE` |
| Terminal parent | `build/terminal-notice-sound/TERMINAL.EXE` |
| Ordinary ASPECT child | `build/aspect-notice-sound-parent/ASPECT.EXE` |
| Diagnostic child | `build/aspect-notice-sound-fault/ASPECT.EXE` |

Use the ordinary child as the parent's sibling `ASPECT.EXE`; the diagnostic is a
separate test product. This accepts selected PROGRAM sound/configuration/recovery
integration, not all PROGRAM policy. Macro keyboard, shared mouse/UI, wider views,
current live BBS regressions, physical audio/modem acceptance and full F01–F16
application requirements remain open. Normal105-slot publication is unchanged.
