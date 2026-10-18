# Live XLT input translation

The source-built DOS terminal accepts an explicit XLT table before connecting:

```dos
TERMINAL /X:C:\PCPLUS\CUSTOM.XLT COM2 19200 8N1 HARD
```

The file must contain exactly256 bytes. Table entry `n` replaces received byte
`n`; binary NUL, SUB, FF and repeated outputs are valid. Without `/X`, normal
terminal input is unchanged. An identity table is `00 01 ... FE FF`; no original
table or user configuration is imported automatically.

The path has the existing explicit-file contract:1..63 printable characters,
no spaces, quotes or wildcards. Duplicate selectors or invalid command tails
reject the entire option transaction, retaining all previous options. DOS path
spelling is normalized as for `/K` and `/T`.

## Ownership and behavior

Startup reads and validates the table after configuration/keyboard/actions but
before saving or changing UART hardware or installing its interrupt vector.
Load, size, read or close failures stop startup with exit7 and an XLT-specific
message. Reader status and DOS error detail remain in terminal-owned state.
The checked reader stages bytes and commits only after EOF and successful close;
failure leaves the table unchanged and mapping disabled.

Normal main-loop receive performs connection, raw-monitor, controller and
transfer-grace filtering first. Only unowned terminal bytes pass through the
XLT lookup into the native dispatcher. Mapped control bytes therefore affect
parsing, and mapped ordinary bytes enter rendering, history and processed text
capture. UART ring contents remain raw. Existing software-flow consumption and
receive masking happen in the driver before this owner.

Parser continuation remains raw, matching the recovered5ca0 boundary. A table
that maps `Q` to ESC can make `Q[6n` a cursor query, even if the table would also
map `[` to a different byte: `[` is consumed inside the raw parser continuation.
XLT does not map typed output, key strings, macros, modem commands, terminal
replies, dedicated print-controller bytes, monitor dumps or binary transfer
payloads. These separate owners preserve their existing byte contracts.

RIS keeps the selected table; it performs no resource reload. PROGRAM retains
the table with the parent's normal data and retains its loader code with the
complete configuration code extent. No live table reload, editor, automatic
`PCPLUS.XLT` lookup or saved-PRM translation selection is implemented here.
The original selection word at DS1d64 and its7-bit alternative are documented in
[native recovery](TRANSLATION.md); completing their settings transaction remains
part of F05/F06.

## Code and validation

`src/terminal/translation.asm` owns startup selection and the normal receive
entry. The checked C reader executes in CONFIG_CODE; explicit3/4/1-word cdecl
callbacks enter resident DOS open/read/close adapters. The adapters convert near
buffer pointers to the DOS CRT's calling convention inside the resident segment.
DS=SS remains invariant. This avoids forwarding a register-only call across
extra far frames when the actual CRT interface also needs stack arguments.

Run through Nix after building the terminal:

```sh
./tools/build terminal
./tools/dev --command python3 standalone/check_translation_live.py
./tools/dev --command python3 standalone/test_translation_live_dos.py
./tools/dev --command python3 standalone/check_config_far_live.py
```

The linked suite covers783 inputs: all256 mapping outputs through normal and
fragmented DOS reads, disabled/no-I/O startup, nine error cases, mapped ESC and
ordinary characters, raw continuation/replies/typed output, processed capture,
RIS retention and all256 raw monitor dump bytes. Only DOS/BIOS/UART boundaries
are modeled; no application callback is skipped. The far-code suite rejects119
damaged call frames, targets, returns, relocations and segment layouts, including
the new XLT entry and three DOS adapters.

Seven actual DOS cases use synthetic files and an owned loopback modem: encoded
ESC controls and mapped text, an explicit identity table, an ignored table with
no selector, and empty/short/extra/missing file rejection. They check actual
cursor/device replies, text video, unchanged typed output/modem commands, file
identities, process exit and independent before/after UART/vector snapshots.
The generic modem harness also verifies that a same-write CONNECT+banner burst
retains its first byte. There is no physical UART/Wi-Fi modem claim.

The complete terminal regression and fresh source-only rebuild remain separate
checks. [Validation](validation/translation-live.json) binds the selected live
and DOS reports to executable and source hashes and records their scope.
