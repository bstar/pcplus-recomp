# Ten KEY actions: native routing and TEXT semantics

This module recovers **978 exact original bytes** in14 assembly units, including
resident47b6 action dispatch,48cc TEXT sender,4934 caret decoder,1594 Alt-digit
consumer,414c HOOK command builder and its actual string/decimal helpers. Flat
NASM output matches recorded SHA256 region hashes from the original2.01
executable6401ccfd…7196904. `META_KEYS_OMF` assembles relocatable near-code
objects with explicit state/service symbols. The ordinary build reads source
and recorded hashes only. `recover.py` is a separate analyst operation requiring
the ignored original. Provenance includes saved and current REA evidence IDs.

The recovered action dispatcher is executable code; ASPECT interpretation,
external process execution/path resolution, message UI and UART are integration
interfaces. Standalone fixtures record those service calls and do not emulate
an ASPECT interpreter, shell or HOOK program. This is not complete live action
support. A separate maintained nonblocking application layer is required.

## Entry points and stack contracts

All calls are near, DS=SS, DF clear. Arguments below are listed in stack order
at entry, after the return address. Unless specified, caller removes arguments.

| Export | Arguments / contract |
|---|---|
|meta_keys_invoke|text pointer,kind word,context word; caller6; BP preserved; void/no stable AX result|
|meta_keys_alt_digit|No arguments; DS meta_normalized_scan must be78..81; indexes54-byte record by scan-78 and invokes it with context3; no index bound inside original helper|
|meta_keys_send_text|text pointer; caller2; BP/SI preserved, DI preserved through recovered decoder; other registers/ES/flags volatile through services; no status result|
|meta_keys_expand|source pointer,destination pointer; caller4; BP/SI/DI preserved; no capacity argument or stable AX result|
|meta_keys_hook|hook mode,extra argument pointer,context,program pointer; **callee removes8**; BP/SI preserved, AX and meta_hook_result receive executor result or1 for invalid name|
|meta_keys_validate_name|program pointer; caller2; BP preserved; AX0 accepted,1 rejected|
|meta_keys_decimal32|lowword,highword,destination,radix; caller8; unsigned32 formatting; BP/SI/DI restored|
|meta_keys_decimal16|value,destination,radix; caller6; signed16 decimal when radix10; BP/SI/DI restored|
|meta_keys_tick_delay|count word; **callee removes2**; waits count+1 BIOS low-word tick transitions; enables interrupts; volatile registers/ES/flags|
|meta_keys_pace|count word; **callee removes2**; calibrated delay using original DS7a4e/7ac4 state; zero skips delay|

`meta_keys_decimal_core`/`meta_keys_decimal_body` are shared internal entries,
not standalone APIs: they require the formatter's BP frame and saved registers.
Recovered strcpy/strcat use ordinary caller4 near-string contracts and do not
bound destination writes. Helpers keep their original behavior rather than
adding validation silently.

## Action routing

Original KEY records contain a16-bit kind and52-byte NUL-terminated text area.
Strict540-byte file loading belongs to the separate maintained reader; the
native dispatchers do not validate storage or scan bounds themselves.

| Kind | Original route |
|---|---|
|0 ASPECT|If meta_script_active(DS4b02) is nonzero, call message UI with the already-in-script diagnostic. Otherwise call external ASPECT service4b1f with arguments0,text; that service removes4.|
|1 PROGRAM|Call program service433d with text,0,1,1,1. Its third argument chooses command-processor execution: native896a uses COMSPEC /c and falls back to command.com. The fourth flag calls3745, which paints a prompt and reads a local key; the fifth enables screen/UI preservation around execution. Full executor/UI implementation remains external.|
|2 HOOK|Call recovered414c with1,0,context,text; this constructs the actual HOOK protocol command and calls external resolver353d/program service433d.|
|3 TEXT|Call recovered48cc, described below.|
|Other values|Original dispatcher performs no action; AX arithmetic is not a success/error contract. The strict maintained reader rejects unknown kinds.|

Alt1..Alt9,Alt0 correspond to scan78..81 and records0..9, independently of
function-key KBD slots. The consumer passes context3 to every action.
The earlier raw keyboard classifier returns a local-action boundary for these
keys; action execution is separate from sending a79-slot KBD string.

## Exact TEXT grammar and precedence

The decoder walks until stored NUL. Ordinary bytes copy unchanged. A caret
consumes the following byte, with these rules:

- `^@` writes storedFF, which represents wireNUL.
- `^^^` consumes three carets and writes one literal caret.
- Every other `^X` writes `X & 1f`. Therefore `^^` is control1e, not a literal
  caret. Lowercase operands work by the same bit operation.

A lone trailing caret consumes the string terminator as an operand and reads
beyond it. Recovered code preserves this legacy bug. A maintained bounded
wrapper must reject a trailing caret before starting output. Operands such as
backtick, space or80h produce an actual storedNUL. The decoder continues writing
later bytes, but the sender terminates at that firstNUL, truncating the macro.
`^@` is special specifically to avoid that storedNUL termination.

Sender48cc first expands into its own130-byte stack area, with no explicit
source/destination bound. Then each expanded nonzero byte is processed in this
order:

1. If it equals configured byte meta_pause_byte(DS1d66, PRM offset01e2), call
   actual BIOS delay6b98 with argument9 and transmit nothing. This is **ten BIOS
   tick transitions**, because the helper increments its argument before waiting.
2. Otherwise, FF transmits wire00, bypassing local echo and calibrated pacing.
3. Other bytes optionally call local echo0610 when DS1d1a is nonzero, transmit
   through UART serviceab0b and call calibrated delay6b72 with DS1d68 (PRM01e4).

Pause matching therefore takes precedence even overFF. Pause settingFF consumes
`^@` as a pause; it does not transmitNUL. An expandedNUL terminates the string
before pause comparison. The source diagnostic's pause setting `~` is a fixture,
not a claim about historical defaults. KBD-slot strings do not run this caret
or pause grammar.

## Supported HOOK command protocol

HOOK text is an external program name/command token passed to native process
services, not a TEXT-send macro. The recovered name guard rejects empty text
and any string whose first byte is `[`. It does not prove a richer filename
validation grammar.

For KEY kind2 the exact builder constructs:

```
 PCPLUS <packed DS:d126> <packed DS:d13a> <packed DS:1b84> <signed context>
```

There is one leading space, the literal `PCPLUS`, and single spaces between
arguments. Each packed pointer is formatted as **unsigned decimal of
(DS <<16) | offset**. It is not a linear physical address, COM number, or a
value read from that memory. The last argument is signed16 decimal; Alt digits
pass3. DSd126/d13a are shared exchange addresses whose complete external HOOK
structure remains untyped; DS1b84 is the PRM-image base. Relocated OMF symbols
supply the current offsets, so command values legitimately change after linking.
No undocumented HOOK input syntax or exchange-record layout is invented.

The more general414c entry with mode0 omits the two exchange pointers and
appends a space plus its extra argument string after context. Both modes call
resolver353d, then executor433d with program,generated command,0,0,0. Executor
result is returned inAX and stored at meta_hook_result(DSd124). Invalid names
set that result to1 after the message callback. The resolver's actual filesystem
search and native child-process setup remain external; the standalone identity
resolver and program recorder are explicitly diagnostic fixtures.

## Verification

```
./tools/dev --command python3 standalone/build_meta_keys.py
./tools/dev --command python3 standalone/check_meta_keys.py
./tools/dev --command python3 standalone/check_meta_keys.py --original
./tools/dev --command python3 standalone/test_meta_keys_dos.py
```

Five CPU groups cover297 cases, including every nonzero caret operand, triple
caret, controlled evidence of the terminator overread, embeddedNUL truncation,
pause/FF precedence, ten actual tick-loop transitions, nonzero calibrated pacing,
all ten Alt-digit records, action routing/flags, script-active precedence,
HOOK modes, signed contexts, name errors and exact generated pointer strings.
All297 compare against genuine SHA-pinned original instructions when requested.
HOOK comparisons verify each actual relocated pointer value against its own
memory layout rather than pretending pointer strings are relocation invariant.

The actual DOSBox-X8086 diagnostic exercises native kind3 invocation, caret
expansion, serialNUL recording, A/B output, a real BIOS-clock pause lasting at
least ten transitions, and Alt1 record dispatch. UART/echo/ASPECT/program/UI
services are declared recorders; no original synthetic analysis executable,
external program or public BBS is launched.
