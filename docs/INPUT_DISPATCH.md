# Recovered continuous terminal input path

The source build now accepts a continuous byte stream through the actual
PCPlus resident input entry at `0610`. Printable characters reach the recovered
renderer; ESC selects the real ANSI handler through a symbolic startup pointer
table; CR, LF, BS and TAB invoke their recovered control functions. Printable
and newline paths also execute the actual history-ring writer and guarded
logging code. Enabled unrecovered sinks and unsupported controls trap explicitly.

```sh
./tools/dev --command python3 standalone/build_input_dispatch.py
./tools/dev --command python3 standalone/check_input_dispatch.py
./tools/dev --command python3 standalone/test_input_dispatch_dos.py
./tools/dev --command python3 standalone/check_input_dispatch_relocation.py
```

`build/input_dispatch/INPUT.EXE` is a source-only DOS diagnostic. Its DOSBox-X
self-test processes `AB<TAB>C<CR><LF><ESC>[31mD<BS>E` and checks actual video
memory (including direct negative-word normalization): tab placement, line movement, SGR red output and backspace overwrite.
The eight linked CPU groups additionally test all supported ANSI profiles,
NUL/DEL handling, mode-dependent CR/LF, embedded controls while parsing CSI,
wrapping/real bottom scrolling, history CR state and ring wrap, and explicit
unrecovered-feature failure. A relocation regression shifts code and data
independently across three placements and exercises both input CS jump tables,
the DS pointer tables and nested ANSI/render/control/history calls.

A separate verification copies declared source inputs and test harnesses into
a temporary directory with no `analysis/` directory; build, CPU tests and real
DOSBox-X stream self-test pass there. Originals are unnecessary for these tests.

## Recovery and entry ABI

The module recovers 1,017 instruction/table bytes in eleven flat source units:

| Resident range, end exclusive | Export |
| --- | --- |
| `0610..0730` | `terminal_receive_character` (both inline jump tables) |
| `09b6..0a3a` | `terminal_log_character` |
| `0a8c..0b4e` | `terminal_tab` |
| `0e60..0e61` | `terminal_ignore_control` (actual original RET) |
| `0eea..0f3d` | `terminal_backspace` |
| `0f3e..0f62` | `terminal_linefeed` |
| `1002..1040` | `terminal_carriage_return` |
| `1f56..1f6f` | `terminal_control_home` |
| `5832..58ce` | `terminal_history_character` |
| `58ce..58ea` | `terminal_history_pair` |
| `830c..8318` | `terminal_signed_divide` |

Build with `-DINPUT_DISPATCH_OMF`. `terminal_receive_character` takes a word
byte value at `[BP+4]`, returns near and leaves argument cleanup to its caller.
It preserves BP/SI; downstream original services require DS=SS and DF clear.
Maintained OMF mode normalizes the word argument to an unsigned byte before
control selection. Flat mode preserves every original byte. This prevents
negative-word input from indexing before the 32-entry control table. `terminal_history_character` instead **cleans its own one-word
argument**. `terminal_log_character` leaves its argument for the caller.
The CR/LF/BS/TAB table functions take no stack arguments.

The test host's `terminal_process_stream` repeatedly gets a byte from a memory
provider and calls the real entry. The actual ESC parser consumes subsequent
bytes through that same provider, and embedded control callbacks reenter
`terminal_receive_character`; they are not reduced to a counter callback.
This is a finite-stream test harness, not the application's serial event loop.

## Startup function-pointer tables

`tables.asm` re-authors 130 bytes of startup data as symbolic near pointers:
33 entries at original DS `445e`, and 32 entries at `44a0`. Flat output matches
the original startup-data32 region exactly. OMF emits linker relocations.
No original executable, startup blob or overlay image is a build input.

- `terminal_escape_dispatch_table` (`445e`) selects terminal emulation.
  IDs 2 through 11 all reference original stub `b973`, whose decoded overlay
  record targets overlay14 `ecd2`, the recovered `ansi_escape_entry`.
- `terminal_control_dispatch_table` (`44a0`) includes NUL (`0e60`), BS (`0eea`),
  TAB (`0a8c`), LF (`0f3e`), CR (`1002`) and control31 (`12c8`, real wrap).
- Other startup table entries are preserved as named unresolved dependencies
  and trap in this diagnostic. The genuine ignore-control RET is preserved;
  unsupported controls are not replaced with that RET.

## Maintained byte-argument guard

Original argument `ffb1` selects DS `4402`, outside the control table, and
interprets bytes `58 5d` from an `Alt-X]` help string as code pointer `5d58`.
Argument `ffff` instead selects DS `449e`, the preceding escape-table entry
`bb3b`. An optional original replay records these computed pointers and stops
before either indirect call. Maintained OMF code masks SI with `00ff` directly
after loading the argument, so these inputs become byte values B1 and FF.
Regression tests cover direct oversized/negative arguments and the real CSI
dispatcher CAN/SUB table branches that produce legacy word `ffb1`. The meaning
of that literal is not inferred, and complete parser CAN/SUB semantics remain
separate work. The recovery generator preserves this intentional guard while
flat output remains identical.

## Canonical DS state

Existing renderer/screen/ANSI/scroll symbols retain their documented mappings.
These aliases are especially important: original DS `8fe8` is both
`terminal_input_mode_8fe8` and `terminal_dec_keys`; DS `1d20` is both
`render_autowrap` and `cursor_state_value_1d20`. Each pair shares storage.
DS `372c` remains the neutral `terminal_mode_372c`.

| Original DS | Symbol | Width/use |
| --- | --- | --- |
| `1d24` | `terminal_cr_adds_lf` | word: CR also advances row; sink newline selection |
| `1d26` | `terminal_backspace_erases` | byte: optional erase branch |
| `1d30` | `terminal_c1_enabled` | word: C1 table gate with DS8fe8 |
| `3988` | `terminal_sink_3988_enabled` | word: enables sink36fc |
| `398a` | `terminal_sink_398a_enabled` | word: enables second sink |
| `398c` | `terminal_sink_398c_disabled` | word: suppresses second sink |
| `418a` | `terminal_sink_error_state` | word: error callback state |
| `4eba` | `terminal_history_start` | word near offset |
| `4ebe` | `terminal_history_pointer` | **far pointer**, offset then segment at4ec0 |
| `4ec6` | `terminal_history_end` | word exclusive end offset |
| `4ec8` | `terminal_history_wrapped` | word wrap/full latch |
| `4ecc` | `terminal_history_pending` | byte CR/LF coalescing state |
| `9020` | `terminal_newline_mode_9020` | word: LF also returns column; BS special branch |
| `903e` | `terminal_tab_wrap` | word: tab past final stop wraps |
| `8ff8` | `terminal_tab_mode_8ff8` | word mode gate |
| `9058` | `terminal_backspace_mode_9058` | word mode gate |
| `ce10` | `terminal_tab_stops` | ordered byte stops, FE sentinel,30 entries |
| `d114` | `terminal_sink_handle` | word sink argument |

History state must describe an allocated nonempty far-memory ring. The test
host supplies 4,096 bytes; small-ring tests exercise original wrap behavior.
History coalesces CR/LF and is not a raw transcript of every input/control byte.

## Evidence and remaining work

`provenance.json`, `tables-provenance.json` and `rea-index.json` record the
verified original digest, exact region hashes, retained REA identities,
startup-pointer provenance and coverage limits. Explicit analyst-only
`recover.py` reads the ignored original and checks every instruction encoding,
all flat regions and startup-table pointer values. It is never a build input.
`evidence/` records the latest test snapshots.

An optional original-resident comparison is available:

```sh
./tools/dev --command python3 standalone/compare_input_dispatch_original.py
```

It executes the unmodified original resident input/control/render/video/cursor/
history/guarded-log instructions, using actual original control pointers, and
compares screen/state/history/BIOS calls after each input byte. The comparison
covers ordinary/high bytes, TAB/CR/LF/BS, wrapping and ring rollover across 330 operations. Original
ANSI overlay loading is outside its scope; ANSI continuous-stream integration
is established separately by the source-only tests.

Still unresolved are the other terminal/control families, optional font and
complex attribute/viewport services, enabled sinks36fc/8436 and their error
callbacks427f/bb23, and the renderer's mode372c callbackb9f7. Global application
startup must initialize the function tables, modes, tab stops, history ring and
other configuration. These diagnostics do not reconstruct serial polling,
application UI, dialing, transfers or scripting.
