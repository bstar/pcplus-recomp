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
