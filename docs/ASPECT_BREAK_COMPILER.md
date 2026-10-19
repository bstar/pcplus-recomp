# BREAK duration compiler grammar

The maintained host compiler accepts no-argument `BREAK`, `SET BREAK` and `FETCH BREAK` using frozen ASPCOMP 1.01 bytecode evidence. **GET is not the setting query command.** It is an unrelated interactive field-input command. `BREAKLEN` is not the proved setting keyword.

```
./tools/dev --command python3 standalone/test_aspect_break_compiler.py
```

The public corpus freezes 63 authored original compiler attempts: 15 accepted sources in the maintained scope, 47 rejections, and one accepted `FETCH DISPLAY` source retained as explicitly unsupported. The checker verifies all supported bytes, symbol/case/whitespace variants, original rejection boundaries, the unsupported boundary and seven novel emissions. Compilation does not establish working UART BREAK ownership, electrical duration, parent inheritance, or complete FETCH support.

## Source syntax and exact bytes

```
integer saved_delay
proc main
    fetch break saved_delay
    set break 350
    break
    set break saved_delay
endproc
```

BREAK accepts no operands, comma or other punctuation. It emits `0D`; a complete empty-main example is `00 CF 0D 94`.

SET BREAK takes an atomic integer source. Integer globals, locals, parameters and signed word constants are accepted. Long/float/string sources, expressions, parentheses and unsigned positive literals32768 or65535 are rejected by the compiler. A comma between the setting and operand is accepted; a trailing comma is rejected. Negative word constants compile, including−32768, but their native runtime bounds are a separate matter.

SET emission is `9E 09 <integer-source>`. Examples inside an ordinary main procedure:

| Statement | Whole ASX |
| --- | --- |
| `set break 350` | `00 CF 9E09 AB5E01 94` |
| `set break 0` | `00 CF 9E09 B500 94` |
| `set break 32767` | `00 CF 9E09 ABFF7F 94` |
| `set break -1` | `00 CF 9E09 ABFFFF 94` |

FETCH BREAK takes an atomic **integer destination**: global, local or integer parameter. Constants, readonly builtins, other variable types, expressions and parentheses are rejected. A comma before the destination is accepted; a trailing comma is rejected. It emits `37 09 <integer-destination>`. For global integer0: `00 CF 37 09 8D00 94`. The query's native owner does not refresh the status row; the successful native setter does.

Only FETCH BREAK is added here. The original compiler also accepted `FETCH DISPLAY duration`, emitting `37 12 8D00`, but the maintained compiler deliberately rejects it until that family is separately integrated. No getter is implemented as a constant or no-op.

## Native storage, bounds and defaults

Native setting slot09 dispatches overlay19:E8A7. In SET mode it calls DD9C, which invokes the integer reader with signed bounds **0..32767**, then stores AX into DS:1D28. In FETCH mode it passes the raw DS:1D28 word to DE3A, the real typed integer destination writer. Source syntax therefore does not supply an ordinary0..65535 SET range.

The original installed executable initializes DS:1D28 to015E, decimal350. Its proved PRM image offset is01A4. This establishes an original program initializer, not the value of the user's configuration or every profile. The word stores native calibrated delay units consumed by6B72. Their nominal millisecond-style intent depends on startup calibration; it is not an unconditional conversion to350 milliseconds or350 BIOS ticks. See [BREAK_NATIVE.md](BREAK_NATIVE.md) and [ASPECT_TXPACE.md](ASPECT_TXPACE.md).

Private controlled native replay executed actual FETCH E660, setting E8A7, DD9C/DD68/DC48, DE3A/DE4D and the original byte reader for12 cases. FETCH returned raw0,350,32767,32768 and65535 exactly into a real global integer destination, with no status refresh. Bounds-enabled SET accepted0,350 and32767; negative word patterns32768/65535 reached native error1 before storage under the tested stop-on-error boundary. Disabling native E37C bounds checking allowed those raw high words to be stored. This investigation does not enable such a bounds-disabled setting in the maintained compiler/runtime.

A raw imported word may therefore exceed32767 and FETCH may return its signed-negative integer interpretation; setting that fetched value again under normal bounds can fail. Preserve the raw configuration word separately rather than silently clamping or claiming lossless scripted restoration for every imported value. The consumer BREAK routine itself reads the raw word, so its imported range and the setter's accepted range are distinct.

Parent/child inheritance needs an explicit lifetime and ABI decision. The maintained parent's live BREAK uses a deliberately chosen BIOS-tick policy; it cannot be substituted for a native calibrated word merely because both represent a duration. A child without a selected-record/PRM duration capability must document its chosen default rather than claim it inherited the parent's configured word. No ASIO extension or duration-default change is made by this compiler increment.

## Provenance and limits

`freeze_aspect_break_compiler.py` is an optional oracle-maintenance tool. It hash-checks the private original reports/probes before generating the public authored fixture. Normal compiler checks do not read those private inputs. Compiler SHA:

`7377e8ec9b18aec8adf4df8a630eacaa50d95a99f732137c94c3582e4633da6e`

The native storage evidence uses original application SHA `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`. Retained REA Evidence IDs:

- E8A7 setting: `ev_c1f8ea49cff3f3018ddc4f2a30f73fd7ca4308ee9c8b949ec84f28be401e02ea`
- E660 FETCH owner: `ev_e6c3914e2440970116fcc08444051afa572233ca56a5969a84218587b731a88b`
- DD9C bounds wrapper: `ev_9b31a6a0e41c8e66bed1141ace648a53b0876aba5e97abbbb849dfded088577d`
- DE3A typed store: `ev_8518b8617c5e0427229f4184d9fd660724c68ddea09aa2f9279b70eca23c375c`

The private native report SHA is `d47042e1e0eeb638b1e1cfb6bdd49128dfde927ef1f646d779c9f8b33a8379f9`. Status refresh was an explicit counted boundary, error1 was stopped at the native error boundary, and no actual UART BREAK, physical modem, user configuration or complete application was executed by that replay. Runtime integration and hardware timing remain independently scoped. No shared runtime or DOS product build is changed by this compiler work.
