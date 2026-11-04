# Retained keyboard dispatcher bank

The full local-controls candidate had only four bytes of resident code space
left. `--keyboard-bank` moves the existing foreground keyboard dispatcher to
KEYBOARD_CODE, leaving 454 bytes free in the same 64KiB resident code segment.
This creates room for subsequent original terminal commands; it does not add
commands or change their availability.

The bank is retained in memory. It is neither a DOS overlay nor an additional
keyboard reader. Serial polling and pending-menu servicing still precede the
dispatcher in the resident parent. The same source body implements both builds.
Only its return and calls to resident services change when the flag is enabled.

## Real-mode contract

The parent's BP/SI/DI/ES save frame stays resident. The dispatcher adds a far
return frame; each of its 29 resident service adapters performs a near call to
the unchanged implementation followed by RETF. These services pass arguments in
registers or take none. DS=SS, return registers and flags cross the adapters
unchanged. Stack-argument services must not be added through this adapter shape.

The typed [service list](../src/terminal/keyboard_bank_targets.json) is a declared
build input. The MZ/map validator checks the bank extent and RETF, all 29 exact
adapter targets, all 39 far call sites and relocations, and the single resident
entry. The local-controls validator follows its dispatch call into this bank.
The optional flag defaults off; disabling it reproduces the previous candidate
byte for byte.

## Verification and limits

The banked terminal is SHA256
`854e8add51fe3311fa2fbb829dc4eb1bb4bc588a711639e3a4f072df826f9651`.
Its near DS/SS extent remains 64800 bytes. Resident code is 65082 bytes and the
retained keyboard bank is 649 bytes. The resident saving is 450 bytes; this is
code-space relief, not a reduction in total application memory. Far calls add
execution overhead; no physical throughput improvement is claimed.

The differential CPU test executes every 8-bit character and every extended
scan byte, plus exclusive-owner and menu/duplex sequences: 551 cases. It compares
actual screen cells, history, output, deferred FIFO, state, files and remaining
BIOS input with the unbanked candidate. The actual linked routines execute;
only BIOS, UART and DOS boundaries are modeled. The capture key supplies an
Escape to its real synchronous filename prompt. History is initialized as in
main, rather than comparing the loader fixture's uninitialized far BSS.

Separate negative ABI checks reject 31 corrupted images without executing them.
Source-only reproduction, actual DOS controls, BUSY/retry, three calls in one
process, paced UART endurance and lab BBS evidence are recorded in the
[validation receipt](validation/keyboard-bank.json). Physical modem timing and
the reported BUSY/lockup still need user-operated acceptance. This candidate
does not change the selected physical installation or any modem setting.

An earlier Enigma run passed its semantic/screen/log checks but failed its
source-freeze check because source comments and validator code were edited
during the run. That result is retained as failed evidence; the receipt uses
the later run with frozen final sources.

Use fresh output names when repeating:

```sh
./tools/dev --command python standalone/check_keyboard_bank_live.py \
  --baseline build/UNBANKED/TERMINAL.EXE \
  --terminal build/BANKED/TERMINAL.EXE --output build/NEW-comparison
./tools/dev --command python standalone/check_keyboard_bank_abi.py \
  --terminal build/BANKED/TERMINAL.EXE --output build/NEW-abi
./tools/dev --command python standalone/prove_terminal_manifest.py \
  --terminal build/BANKED/TERMINAL.EXE --output build/NEW-source-proof
```
