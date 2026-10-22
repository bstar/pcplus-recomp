# Recorder input versus transmitted bytes

The [source-owned recorder follow-up](ASPECT_RECORDER_SOURCE.md) now accepts
explicit transmitted bytes and proves byte-exact DOS compilation/UART replay
through its maintained raw-output extension. These native tap observations
remain the boundary evidence; terminal tap/UI integration and F13 stay open.

The [454 original-instruction cases](validation/aspect-recorder-native-tap.json)
resolve an important boundary for the source-owned recorder: the original
keyboard tap does not observe every transmitted byte. These are opt-in Unicorn
probes of the verified PCPlus2.01 resident dispatcher and binding emitter.
Recorder, serial, delay, status and display callees are modeled boundaries.
They are not BIOS input, actual UART output or full DOS application tests.

REA/Ghidra observes the dispatcher at CS1604, with calls to recorder thunk
BADB at CS1707 and CS171E. The latter call is admitted only when the saved
original key word is below0080h and recording mode is nonzero. The emitter at
CS0A62 sends a binding's bytes through serial service AB0B, converting stored
FF to NUL. The resident recorder thunk jumps to overlay12 DB5E. Full retained
Evidence stays in ignored analysis storage; evidence identities and artifact
digests are recorded in the public validation receipt. The analysis carrier
was opened for static inspection only and never executed.

| Normalized input | Serial-service observation | Recorder-tap observation |
| --- | --- | --- |
| Literal0041, recording active | 0041 | Key0041, after serial call |
| Literal007F, recording active | 007F | Key007F, after serial call |
| Literal0080 through00FF, recording active | Corresponding literal byte | No call |
| Enter000D, binding `X FF Y` | `58 00 59` | One key000D, after all binding bytes |
| Enter000D, binding `^M~` | Literal `5E 4D 7E` | One key000D |
| Recording disabled | Same serial observations | No call |

All224 literal words0020..00FF are tested with recording both enabled and
disabled. Three Enter bindings are tested in both modes. Each case checks
normal return, stack balance, BP preservation and DS=SS. The binding emitter
and dispatcher instructions execute unchanged; callbacks only replace the
declared external services. Extended/function-key coverage remains open.

The earlier [formatter constraints](validation/aspect-recorder-literal-limits.json)
feed synthetic byte strings directly to the formatter and formatted TRANSMIT
component. RawFF becoming serial NUL there is a formatter API limitation.
It does not establish that the original keyboard recorder captured literalFF:
this dispatcher path instead omits that key. Nor does recording a binding's
FF sentinel as NUL inherently change its intended serial byte.

For the maintained implementation, explicit transmitted-byte input is required
to preserve literal CP437 bytes and expanded bindings. A separate editing/key
input can retain deliberate backspace and grouping behavior. Treat this as an
intentional correction of the native tap boundary, alongside bounded encoding,
checked file ownership and pending-tail preservation. Source recorder ownership,
complete compiler/VM replay, terminal integration and F13 remain unfinished.

```sh
./tools/dev --command python3 standalone/check_aspect_recorder_tap_native.py \
  --original --output build/aspect-recorder/native-tap-new.json
```

This compatibility diagnostic requires the ignored verified original and
overlay manifest. It is not an ordinary source-build dependency.
