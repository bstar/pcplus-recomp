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
