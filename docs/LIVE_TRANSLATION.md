# Live XLT input translation

The source-built DOS terminal accepts an explicit XLT table before connecting:

```dos
TERMINAL /X:C:\PCPLUS\CUSTOM.XLT COM2 19200 8N1 HARD
```

The file must contain exactly256 bytes. Table entry `n` replaces received byte
`n`; binary NUL, SUB, FF and repeated outputs are valid. With no PRM selector or `/X`, normal
terminal input is unchanged. An identity table is `00 01 ... FE FF`; no original
table or user configuration is imported automatically.

The path has the existing explicit-file contract:1..63 printable characters,
no spaces, quotes or wildcards. Duplicate selectors or invalid command tails
reject the entire option transaction, retaining all previous options. DOS path
spelling is normalized as for `/K` and `/T`.

## Saved PRM selection

PRM word01e0h selects the following startup behavior after complete validation:

| Value | Input behavior | Resource |
| --- | --- | --- |
|0|Identity, receive maskffh|None|
|1|XLT mapping on normal terminal bytes, receive maskffh|`PCPLUS.XLT` in the DOS current directory, then bounded `PCPLUS` directory fallback|
|2|Strip bit7 in the actual UART dequeue, receive mask7fh|None|

`/X:FILE.XLT` overrides these valid saved modes with its explicit table andffh
mask. It cannot hide an invalid PRM mode; values above2 reject the whole settings
load before UART ownership. The original falls back to identity for unknown
values; strict rejection is a documented maintained difference.

The45-field PRMEDIT exposes Input translation on the TERMINAL page. Its field
ID44 preserves earlier IDs; Tab and reverse navigation use page membership,
including this appended field. During live Alt-F10 a saved mode change is
classified with mask0800h. The foreground owner stages the default table in a
frozen pre-child namespace and offers a separate confirmation before committing
the mode/table/mask. Declines or failures retain the active selection while
independent edits can apply. See [live mode setup](LIVE_TRANSLATION_SETUP.md). `/X`
remains an effective override during later edits, after raw-file validation.

Mode2 applies before parser, monitor and other receive consumers and does not
change the UART's physical data-bit setting. Binary upload/download is refused
before filename/file ownership while the mask is notffh. Mode1 still permits
byte-exact binary transfer through the separate raw protocol owner.

Default mode1 lookup now tries the current directory, then the inherited
`PCPLUS` directory only after file/path-not-found. It stops on a damaged or
unreadable current table. Explicit `/X` bypasses fallback. See the bounded
[resource lookup policy](RESOURCE_LOOKUP.md). A table must contain exactly256 bytes.

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
The XLT table does not map typed output, key strings, macros, modem commands, terminal
replies, dedicated print-controller bytes, monitor dumps or binary transfer
payloads. These separate owners preserve their existing byte contracts.

RIS keeps the selected table; it performs no resource reload. PROGRAM retains
the table with the parent's normal data and retains its loader code with the
complete configuration code extent. The offline [XLTEDIT editor](XLT_EDITOR.md)
provides checked table editing/save/reload. Bounded default XLT environment lookup
is integrated, and confirmed live mode changes now stage/commit their table and
receive mask. A dedicated same-mode reload command remains open. See
[native recovery](TRANSLATION.md).

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
are modeled; no application callback is skipped. The far-code suite rejects154
damaged call frames, targets, returns, relocations and segment layouts, including
the startup and three live XLT entries plus three DOS adapters.

Twelve actual DOS cases use synthetic files and an owned loopback modem: encoded
ESC controls and mapped text, an explicit identity table, an ignored table with
no selector, empty/short/extra/missing file rejection, saved current-directory lookup,7-bit
masking of an encoded high-bit banner, explicit override and invalid PRM modes. They check actual
cursor/device replies, text video, unchanged typed output/modem commands, file
identities, process exit and independent before/after UART/vector snapshots.
The generic modem harness also verifies that a same-write CONNECT+banner burst
retains its first byte. There is no physical UART/Wi-Fi modem claim.

The complete terminal regression and fresh source-only rebuild remain separate
checks. [Validation](validation/translation-live.json) binds the selected live
and DOS reports to executable and source hashes and records their scope.

The additional saved-mode suite covers561 linked inputs, all nine active/saved
mode pairs, both directions of live mask deferral, candidate/owner atomicity,
editor byte preservation, a complete1024-byte binary transfer under an allzero
active XLT table, all256 driver-mask values and post-mask monitor bytes. Five
optional genuine-original overlay3 cases confirm the native selector behavior
through controlled CRT boundaries. This executes original instructions, never a
synthetic analysis executable. See `validation/translation-modes-original.json`.


The [confirmed live setup report](LIVE_TRANSLATION_SETUP.md) adds331 linked
inputs and10 actual DOS workflows for mode adoption. The earlier561-mode suite
continues to exercise default-policy/declined-change deferral; it does not replace
accepted live-change tests.
