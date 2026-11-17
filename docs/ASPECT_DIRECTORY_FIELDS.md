# Selected-directory integer expressions

The opt-in `directory_fields=True` interpreter executes eight more original
read-only ASPECT operands. Both maintained compilers accept their original
integer selectors. Each getter reads the owned selected114-byte directory
snapshot; it does not query or change the UART.

| Expression | Selector | Overlay16 entry | Record offset | Native read |
| --- | --- | --- | --- | --- |
| `$D_DATABIT` |1 |D9AB |49 |signed byte |
| `$D_DUPLEX` |2 |D9B0 |51 |signed byte |
| `$D_MODE` |4 |D9B9 |74 |signed byte |
| `$D_PARITY` |5 |D9BE |48 |signed byte |
| `$D_PORT` |6 |D9C3 |104 |signed byte |
| `$D_STOPBIT` |8 |D9D5 |50 |signed byte |
| `$D_TERM` |9 |D9DA |73 |signed byte |
| `$D_TOTAL` |10 |D9DF |70 |word |

The seven byte getters retain the exact native `MOV AL; CBW; RET` bodies.
Values128..255 therefore become negative ASPECT integers. TOTAL retains the
exact word getter; integer-to-long conversion sign-extends its16-bit result.
These are raw stored values, without enum normalization or one-based port
conversion. The existing `$D_ENTRY` selector3 is unchanged. `$D_PROTO` selector7
uses a different indexed table owner and remains unsupported.

[Provenance](../reconstruction/aspect_directory_fields/provenance.json) links
retained REA dispatcher/getter evidence. A separate optional original comparison
checks all39 getter bytes, eight original dispatch slots and resident overlay16
stubs against the SHA-bound executable. Synthetic analysis images are never
executed or consumed by application builds.

[Validation](validation/aspect-directory-fields.json) binds67,328 exhaustive
native CPU cases, all80 original compiler probes, the2,516-case DOS8086 compiler
regression and1,153 actual DOS8086 runtime cases with27,858 assertions. The
disabled runtime passes1,146 cases and rejects the new operand before replacing
a prior destination. Authored runtime cases cover signed boundaries, distinct
field offsets, full-word totals, integer-to-long promotion and cleared records.
No-entry zeros remain the maintained reset policy, not a claim about the original
application's startup state.

Two full-parent source-compilation/GET cases pass97 checks, including all eight
fields before/after input and through EXECUTE. The actual serial handoff projects
pending accounting into its snapshot: the synthetic total0 file is observed as
total1 by the script after connecting. The initial test expected0 and correctly
failed; the expectation was corrected after inspecting `serial.c`'s accounting
projection. The native getter was unchanged. The first compiler regression also
found missing reserved-name entries; those were added before the passing run.

The full checked-overlay interpreter is SHA256
`d4b6b92dfc4a8f5ea5046533b7942f83a56a83acbab1b5f227739e1a2a5a6a5e`.
Its near code is64676 bytes, with860 spare; DGROUP40496 and stack8192 are
unchanged. Exact DOS minimum is125552 bytes,80 more than the preceding baud
profile, with the same125712-byte page-rounded minimum. No buffer, bank or VM
limit was reduced. A cold export of1050 sources reproduces the parent,
interpreter, compiler and overlays and repeats both source/GET cases without
original executables, prior objects or ancestor Git.

This profile is not packaged, BBS-qualified, installed or physically accepted.
The preceding [baud-only package](ASPECT_DIRECTORY_BAUD.md) has separate bytes
and validation. Broader loader/Help fault composition, remaining ASPECT
operands/commands, full emulation/protocol parity and all whole-application gates
remain open. Host stays last.

Reproduce the component checks with the pinned toolchain, using fresh output
directories under `build/`:

```sh
./tools/dev --command python3 standalone/check_aspect_directory_fields.py \
  --output build/directory-fields-native-check
./tools/dev --command python3 standalone/test_aspect_directory_fields_compiler.py
./tools/dev --command python3 standalone/check_aspect_runtime.py \
  --directory-baud --directory-fields --output build/directory-fields-runtime-check
```

The optional `--original analysis/pcplus-originals/PCPLUS-main-2.01.EXE` argument
to the native checker adds the private comparison; application builds never use
that input. Exact full-parent and cold-build product/receipt identities are in
the validation record.
