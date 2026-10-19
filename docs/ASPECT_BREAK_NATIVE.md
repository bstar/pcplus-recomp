# ASPECT serial BREAK

ASPECT opcode0Dh invokes the same resident serial BREAK action as Alt-B, then
refreshes the native status row. It does not represent switch/case control flow.
The original compiler accepts `BREAK` without arguments, `SET BREAK integer`,
and `FETCH BREAK integerDestination`. The setting selector is09h. `BREAKLEN`
and `GET BREAK` are rejected in the retained original-compiler probes.

## Native mapping and source

The original215-entry dispatcher table at DS4B08 maps0Dh to residentCA53.
That12-byte overlay thunk selects overlay18 and jumps toE67B. The recovered
E67B handler calls0401, then tail-jumps to status refresh2FB8. SET/FETCH table
DS4D24[09] points toC5F7, whose thunk selects overlay19/E8A7.

`src/aspect/break_commands.asm` recovers249 exact bytes, in six independently
selected flat units and one relocatable OMF object:

| Unit | Native range, end exclusive | Original file offset | Bytes |
| --- | --- | --- | --- |
| Serial action | Resident0401..0445 |1601h|68|
| ASPECT handler | Overlay18 E67B..E681 |1CE8Bh|6|
| SET/FETCH accessor | Overlay19 E8A7..E8BD |1DD97h|22|
| Cursor pop | Resident6B42..6B59 |7D42h|23|
| Cursor push | Resident6B5A..6B71 |7D5Ah|23|
| Notice helper | Resident31BB..3226 |43BBh|107|

The public fixture `standalone/fixtures/aspect_break_native_units.json` pins
all ranges and hashes to original executable SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Normal builds read maintained assembly and the public hash fixture only.
No original bytes, initialized data image or private PRM are build inputs.

Fresh REA assembly evidence is retained privately in
`analysis/aspect-break/rea-native-break-01.json`:

- E67B: `ev_6991b6ad6dadc7458dc64aff938f5ece36fe8dbfa2d4d967d3f3f5704e6a928d`.
- 0401: `ev_e68736e5e2f3dc4890c79e7a7f8c235df1d1a06c32a96a6a559071e0357a9b8c`.
- 6B42: `ev_2e606e9a6e3ab6282e4022fecd18a22ea0c5dded522d45c32db9f831d99048c0`.
- 6B5A: `ev_8a46f6bcd77ccc363138a3bc93ca38c193782cd1ec91f2f4eabe7ead8636b2aa`.
- 31BB: `ev_d71ab793c16f4711c0726bdd2155db59e579fd9c31bd7f5c1c08211b72306327`.

The overlay18 carrier is a static analysis artifact; it was never executed.
Resident bytes and overlay ranges are separately checked against the pinned
original when the optional original comparison is requested. E8A7 retained REA
assembly evidence is `ev_c1f8ea49cff3f3018ddc4f2a30f73fd7ca4308ee9c8b949ec84f28be401e02ea`.

## Operation and UI

0401 saves SI and pushes the current hardware cursor through6B5A/798E. It calls
31BB with the near string pointer atDS2074 and delay0, reads the UART LCR at
DS8FEE, writes the read value OR40h, calls calibrated delay6B72 withDS1D28,
then writes the original read value AND00BFh. It pops the cursor through
6B42/6E78 and restores SI. The ASPECT handler subsequently refreshes status2FB8.
The input helper829A zero-extends its byte result; output82A8 takes cdecl
port,value words. The calibrated delay consumes its word argument with RET2.

31BB computes a screen position from3250,7A82 and7A84. If1D46 is nonzero,
it skips the notice entirely. Otherwise it saves15 cells, fills them using
attribute1F6E with AH OR20h, and prints the supplied string with the original
attribute. A nonzero delay would wait via6B98 and restore those cells; BREAK
passes zero, so no wait or saved-cell restoration occurs in31BB. The later
ASPECT status refresh is a distinct call. This is not the same entry point as
status_message3226. DS2074 is initialized to0000h, a valid near pointer to
DS:0000, where overlay32's initialized data contains `*** BREAK ***` followed
byNUL. No later resource-pointer initialization is needed. The adjacent table
entries2076=000Eh and2078=001Ch point respectively to `DISCONNECTING` and
`AUTO ANSWER...`, independently corroborating the string-offset table. This
corrects the earlier interpretation of0000h as an unresolved/null resource.
Actual native writer6BF0 loads SI from the pointer and executes LODSB before
checking the character; it never rejects a zero pointer.

The original data mapping is overlay32 file25950h+DS offset, already established
in [CONFIGURATION.md](CONFIGURATION.md). Fresh REA reads in the static carrier's
overlay32 analysis range confirm the text, table and suppression default:

- DS0000 text: `ev_d49f11269a8e4b403492831b20e2dd9bfe30827eaa857c4d8b0b0e6705fbea35`.
- DS2074 table: `ev_7de0970b226426f97cb3925bae4e9494f4cb1d46e0a88f17bd69ce2e0a657605`.
- DS1D46 default0000: `ev_5ea482294f162ef71c0cf35c795376c40c90e5c156989ef54e7e0a6ce4376e2c`.
- 6BF0 assembly: `ev_f15bb69907416d09a5e8604104f8a1fcb10270a1c2526883151351b3ba4bc66d`.

These are retained privately in `analysis/aspect-break/rea-native-notice-01.json`
and `rea-native-notice-02.json`. The first bundle also preserves incomplete reads
from initially incorrect analysis addresses; only the second bundle's complete
overlay32 reads establish data identity. Analysis coordinates1FB70h+DS offset
are carrier mappings, not a claim about the original running DS segment.

A separate original-dependent CPU observation, `analysis/aspect-break/notice-proof.json`,
executes actual31BB and6BF0 with DS:0000 as the string, mapped bottom-row geometry,
attribute1Eh and delay0. Native LODSB/STOSW writes all13 characters
`*** BREAK ***` with attribute1Eh to modeled VRAM and returns with balanced SP.
Screen save/fill, coordinate conversion and CGA blank/unblank are explicit
callbacks. This does not execute the original application or measure a physical
display; it directly proves the native zero-offset string path.

The maintained parent already links exact31BB as `pcplus_flow_message` from
`reconstruction/ui_windows/flow_message.asm`, using actual native6BF0 as
`ui_write_string`. Its existing `ui_flow_suppressed` word corresponds to1D46;
`src/terminal/state.asm` initializes it to0. The same word is copied into
`reset_status_hidden` by `terminal_status_live`. Its `ui_flow_attribute` word
corresponds to1F6E and defaults to001Eh. Thus a maintained UI adapter can call
the existing flow-message service with a relocated, source-owned
`db '*** BREAK ***',0` and delay0 while preserving the shared suppression policy.
A source-owned notice must use its actual near offset; reproducing original
pointer0000h in a different data layout would be wrong. This recovery adds no
production adapter and does not authorize a new divergent suppression shadow.

The cursor helpers preserve a native quirk:6B42 compares BX with the **word
stored at7A38**, rather than immediate7A38. The initial cursor-stack pointer
7A36 is7A38, and the first saved cursor overwrites7A38. Balanced ordinary
push/pop works, but this is not a conventional checked stack. At the upper
limit7A4C, a push overwrites the slot without advancing; pop then usually
subtracts2. An unmatched pop can move below the initialized stack. The exact
recovered code retains this behavior; production integration must supply its
own lifetime and stack admission.

There is no native local UART ownership check, TEMT drain, cancellation,
exception cleanup, or service polling during this action. A preexisting LCR
BREAK bit is cleared at the end. If the delay callback stops execution after
assertion, no native release or cursor/status cleanup runs. Recovery of the
handler is not evidence that it is safe to invoke under a child UART owner.

## Setting, default and lifetime

The word1D28 lies in the imported PRM block at offset01A4h. Its original
installed default is015Eh (350). It is persistent configuration state, unlike
per-script E38E query mode, and these handlers contain no invocation reset or
save/restore. SET replaces that same word, affecting subsequent BREAK actions
and FETCH. CALL does not create a private copy. The loader's broad PRM import
and maintained configuration import are separate ownership operations.

E8A7 tests E38E: zero reads DD9C, stores AX directly into1D28 and returns;
nonzero pushes1D28 to integer destination storeDE3A. DD9C supplies lower0 and
upper7FFFh to bounded integer readerDD68. Thus source-level negative integers
can compile but fail the runtime bound. FETCH does not apply that bound, and
BREAK passes an imported full16-bit word unchanged to delay6B72. There is no
unit conversion in this accessor. The fresh compiler probes emit
`9e 09 ab 5e 01` for `SET BREAK 350` and `37 09 8d 00` for a first global
integer destination in `FETCH BREAK duration` (excluding program framing).

[BREAK_NATIVE.md](BREAK_NATIVE.md) documents exact calibrated delay6B72 and
startup7956. The nominal unit comes from measured loop iterations per BIOS
clock transition divided by55. This supports millisecond-style intent, not an
exact physical duration. [LIVE_BREAK.md](LIVE_BREAK.md) describes the maintained
parent's deliberately different serviced BIOS-tick owner. The source module
here does not alter that owner, publish an ASIO capability, or establish child
BREAK integration. No physical UART pulse duration has been measured.

## Verification and boundary

```sh
./tools/dev --command python3 standalone/build_aspect_break_native.py
./tools/dev --command python3 standalone/check_aspect_break_native.py
# Optional private comparison, never an ordinary build input:
./tools/dev --command python3 standalone/check_aspect_break_native.py \
  --original analysis/pcplus-install/PCPLUS.EXE
```

The checker executes the actual recovered8086 instructions with DS=SS. Its
2585 cases cover all256 input LCR bytes, five raw duration values including0
andFFFFh, enabled/disabled notices, exact action/UI/status order, unchanged
near stack and preserved BP/SI/DI, bounded SET and unrestricted FETCH, cursor
edge/alias behavior, notice wait/restore branches and a stopped-delay cleanup
boundary. Screen operations, hardware I/O, cursor read/write, calibrated delay,
status refresh and bounded operands are explicit synchronous component callbacks.
No hardware timing, actual DOS execution, complete native renderer, compiler
conformance suite or maintained child lifecycle is claimed by this component.
The optional original pass additionally checks both dispatch thunks/tables and
installed350 default. Current reports remain under `build/aspect-break-native/`.


## Native FETCH and cursor prerequisites

`src/aspect/fetch_command.asm` recovers opcode37h's actual owner, overlay19
E660..E672 (18 bytes), reached through residentC237. Overlay18 E660 is an
unrelated handler and must not be used for this recovery. FETCH sets E38E to1,
reads the selector through4CB4, doubles AX into BX, calls the near table entry
atDS4D24+BX, and returns. It leaves E38E=1 and performs no status refresh.
There is **no native selector bounds check**: FFFFh and doubled-word wrap remain
unchecked. A maintained SET/FETCH table must therefore provide its own typed
unsupported entries and any pre-dispatch safety policy explicitly. Native table
indirection alone does not establish malformed-bytecode safety.

DD9C is already recovered as `aspect_console_pause_operand` in
`src/aspect/console_commands.asm`, unit6 (11 bytes). It pushes0 then7FFFh and
calls the actual52-byte `aspect_string_bounded_integer` atDD68, which consumes
both bound arguments with RET4. No duplicate `break_operand.asm` is needed:
an adapter can alias `aspect_break_operand` to `aspect_console_pause_operand`.
DD68 reads the actual integer operand and, when E37C is nonzero, checks signed
bounds. On failure it calls error1. If that error callback returns and E378 is
nonzero, the helper returns the lower bound0; if the callback returns with
E378=0, it returns the original invalid operand. With E37C=0 it skips the check.
A real nonlocal abort prevents the later SET store. A fixture that always
clamps, or always prevents return, would conceal these native distinctions.

`src/aspect/break_cursor_read.asm` separately recovers resident798E..79A8,
26 bytes. It exports `aspect_break_cursor_read` and uses the existing
`screen_use_bios_cursor` alias for7A66. When the word is0, it sets ES=0040h
and returns the packed cursor from BDA0040:0050. Otherwise it clears BH,
executes INT10h/AH03h for page0, and returns DX in AX. It preserves BP/SI/DI
and its near stack; BX/CX/DX/ES/FLAGS are volatile. This reader plus the
existing `screen_cursor_output` can support a maintained one-level cursor
bracket without linking the native alias-prone cursor stack.

A separate original-free builder/checker pair, `standalone/build_aspect_fetch_native.py`
and `standalone/check_aspect_fetch_native.py`, binds these107 exact source bytes
in `standalone/fixtures/aspect_fetch_native_units.json`. Tests execute all45
native instructions across FETCH's256 byte selectors plus FFFFh/word-wrap
indices, range-check enabled/disabled, returning/stopped error policies,
exit-state branches, and both BDA/BIOS cursor legs. BIOS output is an explicit
INT10 callback; operand reads, table services and errors are explicit callbacks.
The test does not replace those boundaries with invented opcode semantics or
claim a production longjmp or actual DOS cursor test. Optional original
comparison verifies all107 bytes and the original37h dispatch thunk. Normal
builds emit `fetch_command.obj` and `break_cursor_read.obj` plus four flat units
without reading the original executable.

Retained REA procedures corroborate these recovered instruction listings:
FETCH `ev_a00a7be8d7da304e618a0a8020ccfd9e4bc65ed43739974b00ca471be5226ca9`,
DD68 `ev_3853bd77e3355996a36a7c4df5b8564c9abceffd8f01df517678f942b7650da9`,
DD9C `ev_8cdf42580163a2eecce5b217c38fd9a07b1f20e95da53882981a9bd58598de23`,
and798E `ev_e9e9c3bf9a2e8bb274ff8eb19635bebf12c9e20b9932dcf3ae65e922bbba91c3`.
Pseudo-code is supporting evidence; exact public range hashes and optional
original byte comparison establish the8086 encodings and branch boundaries.
