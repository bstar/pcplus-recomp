# Default ANSI EOT, ENQ and GS services

The [component receipt](validation/c0-controls.json) binds the recovery and checks.
Stock Enigma's logoff routine writes 20–84 random CP437 bytes followed by
`NO CARRIER`. A real carrier-loss/redial test completed its file retry but
stopped while displaying this logoff noise: ENQ reached the replacement's
unrecovered resident `0E7Ch` boundary. Testing the ANSI6 dispatch table found
two more missing default services, EOT (`4CD7h`) and GS (`1292h`).

The replacement now implements the admitted original branches. These controls
are not replaced with an ignore function. The current application candidate is
SHA256 `e2e1f7ec210da06c36be2f8129a622c70788179daf5ab10c4dac22981cc98059`;
its exact source-only rebuild uses 570 public inputs without originals or
ancestor Git objects. Resident CS is 65,534 bytes, with two bytes spare; near
data/stack remains 65,120 bytes. The new policy executes in the existing far
code bank, with small resident render/transmit callbacks. Future resident growth
requires banking or a separately verified size reduction.

## Recovered behavior and explicit boundaries

| Control | Admitted behavior | Remaining boundary |
| --- | --- | --- |
| EOT, `04h` | With the optional remote operation disabled, display glyph4 under the ANSI glyph policy; otherwise leave the display alone. An active script also selects this original default tail. | The enabled original EOT operation creates a `$REM_ASP` script. Its evaluator and configuration import are not implemented or exposed. An enabled request outside a script still stops at `4CD7h`. |
| ENQ, `05h` | With original `9020h` set, queue raw `1Fh,column,row`, without adding one. Otherwise default answerback mode0 displays glyph5 only under the ANSI glyph policy. | Configured modes1/2 remain explicit `0E7Ch` failures; their string formatting, callbacks and configuration import remain open. |
| GS, `1Dh` | With `9020h` clear, invoke the real native cursor-left service under the ANSI glyph policy; otherwise leave the display alone. | The legacy `9020h` escape-service branch remains an explicit `1292h` failure. |

The source-owned optional-policy words default to zero. No PRM field or command
enables them yet. This is default-path compatibility, not full control/emulation
or configuration parity. Queued response bytes use the existing foreground
transport, including its ASPECT callback and carrier/flow policy. The new code
does not install another UART writer, interpreter or terminal-reply generator.

## Evidence

REA6.8.0/Ghidra12.1.2 opened the verified original executable, SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Automatic analysis did not define ENQ as a procedure, so an attempted function
query was rejected. The recovery uses exact REA byte observations and local
16-bit instruction decoding rather than claiming a successful C decompilation:

- `ev_d1a958da0dbbc714e947754f482b7c2f1a0cbfa85e7f23888b06df4f01a99641`:
  original resident `0E7C..0EDD`, 98 bytes.
- `ev_5085dd67e4a2d4e8bd3250d2a1a5d13e93c99f304e8206710cf04826a4ae0ee3`:
  `1292..12AF`, 30 bytes including the trailing NOP.
- `ev_9774307f997ad7aeb92c89cae82d801b6b9675a4159c3264e79532f7fe64d9c9`:
  `4CD7..4DE2`, 268 bytes, not the complete EOT function.

The private exported evidence bundle stays under ignored build storage. Static
bytes establish branch structure, not execution. Optional controlled replay
executes the unmodified original dispatcher, renderer and cursor instructions
against the linked replacement for both glyph policies and three positions.
All 18 comparisons match the complete 4000-byte video frame and cursor/offset/
wrap state. The synthetic history ring is bounded to fit the replay's DS layout;
these are CPU/model comparisons, not original DOS or analog-modem runs.

The source-only checker covers 31 isolated non-ESC C0 bytes, a real continued
ESC/CSI sequence, glyph/cursor policies, three raw coordinate reports and four
explicit nondefault refusals: 45 linked cases. It also replays the exact captured
Enigma logoff fragment that stopped the preceding parent. ESC by itself is a
protocol prefix rather than a complete test input. Other terminal modes and
arbitrary mixed-stream behavior need their own evidence.

```sh
./tools/dev --command python standalone/check_terminal_c0.py \
  --terminal build/SELECTED/TERMINAL.EXE --output build/NEW_C0_CHECK
```

Add `--original analysis/pcplus-originals/PCPLUS-main-2.01.EXE` for the optional
analyst comparison. Ordinary application builds and source-only checks do not
read the original. `--noise-capture` accepts the saved bridge serial-output
capture from this stock Enigma logoff workflow. No physical deployment or full
feature-parity acceptance is implied by these component results.
