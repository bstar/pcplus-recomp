# Original ALARM controller

The next ASPECT recovery now has120 exact native instruction bytes:
overlay18 E660's27-byte ALARM wrapper and resident3616's93-byte shared alert.
It remains a component baseline, separate from the source interpreter table
and existing maintained connection alert. No installed build changes.

The wrapper saves the configured duration at original DS1D42. If an optional
operand is present, it uses the existing pause-operand reader, temporarily
replaces that duration, invokes the alert, then restores the previous word on
normal return. This is not a new definition of malformed-operand error unwinding.

The shared controller counts observed DOS-second changes. With sound enabled
at original DS1D40 it requests two880Hz tones of duration15, separated/followed
by1/6-tick waits through the original helpers. Quiet mode still waits for the
duration or a key. A pending key ends the loop; a final availability check can
consume a key that arrives just as the duration ends. A frozen seconds source
does not expire a nonzero duration by itself. These are native compatibility
facts, rather than recommended scheduling policy for a live UART.

```sh
./tools/dev --command python standalone/check_aspect_alarm.py \
  --output build/my-alarm-check
```

The source-only check verifies original-range hashes and348 CPU scenarios.
Cases cover duration overrides/restoration, quiet/nonzero enable words,
second wrap/freeze, cancellation and late-key consumption, paired tone/wait
arguments, DS=SS, caller stack and BP/SI/DI preservation. Clock, operand,
keyboard and sound services are explicit models. It does not execute BIOS,
PIT, UART or an acoustic waveform. The generated OMF object is unbound.
The [receipt](validation/aspect-alarm-native.json) records exact sources/units.

REA Evidence IDs:
`ev_4144446925f09733abe9f13d106778a1ddb3691f0c2cbbada79fc70fef6e90e9`
and`ev_14e5906eba85617d1389180edd33b51b3c7b8fae22574d6e89474837d3a735a8`.
The retained private bundle is`analysis/aspect-alarm-next-20261106.rea.json`.
The synthetic overlay was analyzed only; normal builds need no original code
or REA database input. Existing [native sound helpers](PROGRAM_SOUND.md) are
separate evidence for PIT and calibrated delay behavior.

Integration still requires compiler grammar/bytecode evidence, current-parent
duration/sound policy access, a bounded speaker owner, UART-serviced timing,
keyboard cancellation and tested cleanup. The existing synchronous native
controller cannot simply be inserted into the live interpreter and declared
compatible under sustained receive traffic. All application/physical gates
for this command remain open.

The [cooperative adapter](ASPECT_ALARM_COOPERATIVE.md) now exercises the native
shared alert through bounded callback services in actual DOS. It remains a
separate component; real parent policy, serial/speaker backends and opcode
integration are still required.
