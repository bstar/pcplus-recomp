# Original ASPECT recorder behavior

The [native recorder probes](validation/aspect-recorder-native.json) pass28
original-instruction cases. REA/Ghidra identifies four buffering/formatting
routines in overlay12 and the mode controller in overlay16 of the verified2.01
image (`6401ccfd…`). Static analysis opens only the existing analysis carriers;
they are never executed. The separate probes execute selected original byte
ranges under Unicorn with synthetic memory, DS=SS and controlled CRT/wait
callbacks. This is native behavior recovery, not a source-built recorder or
an actual DOS/UI/file/UART test.

| Entry, relative to CS1000 | Role | Instruction bytes | REA evidence |
| --- | --- | --- | --- |
| Overlay12 DB28 | Retain the last16 received bytes | 53 | `ev_cdc10a9614446380a4b5ee9b67dfb0fab4b0759f93897f71fd6ecbf10a59c5ed` |
| Overlay12 DB5E | Capture a key, flush prompt/transmit groups | 80 | `ev_65c4af158df89f29fc47c8867ad021ecc82ad05468ccf84c08c7e436c2793d76` |
| Overlay12 DBAE | Format a transmit group | 91 | `ev_1ea1ae1accd530fc6d19e3a03684fbec3955a784cd85800315695b03c3ff17e2` |
| Overlay12 DC0A | Format a receive prompt | 147 | `ev_80c59c2666e6eaf42494c60f2e0b9d55eee35ccf2c88e0ddf3bf471b9cde55f8` |
| Overlay16 E1B4 | Recording start/stop UI and file owner | 421 | `ev_90f1a568008bbd188ea0d87f6c1a68087edee61ecaf61647b45fae6192214683` |

Only the stop branch of E1B4 is instruction-replayed here. Its startup/file
selection branches remain static observations. Resident thunks BACF/BADB reach
DB28/DB5E; BAF3 reaches E1B4. The existing keyboard dispatcher calls BADB when
recording is active. The exact receive-tap position and complete UI/file lifecycle
still need caller and runtime recovery.

## State and generated commands

| Original DS offset | Observed role |
| --- | --- |
| 373C | Recording mode word |
| 373E / CD3C | Receive count /16-byte sliding buffer |
| 3740 / CD4E | Transmit count /pending raw bytes |
| CFFA | Current key word |
| CE00 | Recording FILE pointer |
| 8E20 | UART receive queue count |

Before capturing a key, DB5E writes a pending receive prompt. DC0A drops NUL,
encodes retained controls as caret plus byte+40h, and suppresses leading controls
when a byte above space exists anywhere in the prompt. Space itself can end the
leading-control suppression. High CP437 bytes are copied directly. The command
is `waitfor` with a quoted literal and CRLF.

DB5E removes a pending byte for exact key word0E08. Otherwise it stores the key's
low byte, invokes the calibrated delay with argument100, and flushes when the
UART receive queue exceeds one byte or the complete key word equals000D. A BIOS
word1C0D does not meet that last condition. The first probe's mistaken expectation
is retained; the passing probe checks both forms separately.

Transmit count is flushed before a new key only when it already exceeds40, so
41 raw bytes can accumulate. DBAE expands controls, then emits a one-second
`pause` and a quoted `transmit` command. Literal quotes and carets are copied
without additional escaping by this formatter; a maintained implementation must
check compiler/replay semantics rather than assume every generated literal is
safe or byte-exact.

## Reproduced native defects

The transmit formatter allocates60 local bytes but performs no expansion bound
check.29 control bytes plus NUL fit;30 controls require61 bytes and overwrite
the saved BP byte.40 and41 controls overwrite farther into the caller frame.
All three cases are reproduced and stop at the formatting callback before a
damaged return can execute. This is an observed write outside the local buffer,
not a claim that a real DOS crash was reproduced.

The active stop branch writes `endproc`, closes its FILE and clears both counts
without flushing pending receive/transmit text. A three-byte pending transmit
tail is therefore discarded in the controlled probe. Both modeled formatted
write and close returnFFFF; native mode still clears. This proves unchecked
callback results in the selected instructions, not an actual disk-full event.

## Source replacement work

The separate [literal-generation constraints](validation/aspect-recorder-literal-limits.json)
now exercise16 cases through the maintained compiler's acceptance checks and
source-built native TRANSMIT/caret instructions with modeled device/delay
callbacks. No original executable is an input. This is not execution of a
generated script through the complete VM, or a source-owned recorder.

Applying the observed formatter rule exposes seven non-roundtrips: quotes
produce invalid source; unescaped caret sequences change bytes; the configured
pause character emits a delay rather than itself; rawFF emits serial NUL; and
adjacent controls1E/1F become the ambiguous sequence `^^^_`, which decodes to
literal caret/underscore. Using `^~^_` disambiguates that control pair; `^^^`
preserves one literal caret and `^@` sends NUL. Twenty-six escaped carets fit the
80-byte literal limit; twenty-seven do not. Chunking must therefore count the
encoded length, not only pending raw bytes. Quote construction, the FF/NUL
sentinel and pause-setting ownership still require deliberate source-owner
solutions. Copying the old formatter with a larger array cannot establish
byte-exact recorder replay. The first probe's mistaken expectation that all
adjacent control encodings round-trip is retained in its failure log; the
passing probe checks the observed collision explicitly.

Implement a bounded source-owned recorder with checked output/close ownership,
explicit prompt/key inputs and safe chunking of expanded literals. Preserve the
documented prompt and key behavior where appropriate; record deliberate fixes
for stack bounds, pending-tail preservation and ignored errors. Verify literal
quote/caret/control/CP437 round trips through the maintained compiler and runner.

Then bind the recorder to the foreground terminal, its source-owned command UI
and file-owner exclusion rules. Exercise start/cancel/stop, failed writes/close,
transfers and child handoffs, generated ASP compilation and actual DOS replay
against synthetic loopback peers. Full source-only production integration and
F13 remain open; these native probes cannot substitute for those requirements.

```sh
./tools/dev --command python3 standalone/check_aspect_recorder_native.py \
  --original --output build/aspect-recorder/native-original-new.json
```

The command explicitly requires the ignored original and overlay manifest.
It is an opt-in compatibility diagnostic, not an ordinary build dependency.

The separate source-only literal constraint probe uses cached source-built
component units, validates their manifest and performs no rebuild itself:

```sh
./tools/build aspect-serial-commands
./tools/dev --command python3 standalone/check_aspect_recorder_literal_limits.py \
  --output build/aspect-recorder/literal-limits-new.json
```
