# Recovered ANSI escape entry

`reconstruction/ansi/escape.asm` reconstructs the complete overlay-14 entry at
CS:ecd2 through eeaeh. It reproduces **477 bytes** exactly in flat mode and links
through named state/service references in OMF mode. This is recovered assembly,
not the original source. Source identity, REA assembly Evidence ID and region
SHA-256 are in `reconstruction/ansi/escape-provenance.json`.

The original region begins at file offset 100386 in the SHA-256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`
PCPlus 2.01 image. Its region SHA-256 is
`edd26bb97e8bf4968ff7e016d4baccd18f1ba2528c84ebbc0615246530008280`.
Twelve original NOP alignment instructions omitted from REA's function Listing
were recovered by checking the original bytes between listed instructions.
Normal builds use only source and the stored hashes, never the original image.

## Behavior and interfaces

The near entry `ansi_escape_entry` consumes bytes following an ESC. It preserves
BP and SI; AX, BX and flags are volatile. It calls the shared byte provider,
put-back service, parameter reader, transition helper and command dispatcher.
It clears the parameter count, first parameter, private flag and secondary flag
when entering the CSI token loop. Tokens `D`, `S` and `L` select parameter read,
transition and dispatch respectively; other tokens return.

External application services retain address-based names because their complete
implementation is outside this recovery scope:

| Input after ESC | Integration callback | Stack argument |
| --- | --- | --- |
| `#` | `ansi_escape_service_e0f8` | none |
| `7` | `ansi_escape_service_dd74` | word 0, caller cleanup |
| `8` | `ansi_escape_service_ddbc` | word 0, caller cleanup |
| `D` or 84h | `ansi_escape_service_da46` | none |
| `E` or 85h | `ansi_escape_service_12c8` | none |
| `H` or 88h | `ansi_escape_service_dac6` | none |
| `M` or 8dh | `ansi_escape_service_da84` | none |
| `P` or 90h | `ansi_escape_service_ec94` | none |
| `Z` | `ansi_escape_service_dd58` | none |
| `c` | `ansi_escape_service_20a4` | word 1, caller cleanup |

`[` and 9bh enter CSI processing. Legacy `*` and `+` consume one extra byte and
then enter that same CSI processing loop; this unexpected behavior is preserved.
Space consumes the next byte: `F` and `G` are ignored, and other bytes are put
back. NUL, repeated ESC and DEL are skipped at the main entry.

`(` and `)` choose the G0/G1 flag pairs. `A` sets `flag_a`; `0` or `2` sets
`flag_graphics`; other designators clear both. These names describe observed
state changes. Actual glyph rendering and the complete charset selection model
are not implemented by this unit.

## Verification

```sh
./tools/dev --command python3 standalone/build_escape.py
./tools/dev --command python3 standalone/check_escape.py
./tools/dev --command python3 standalone/test_escape_dos.py
```

The builder checks the exact flat-mode hash and links an independent DOS MZ
fixture. CPU replay executes the linked recovered instructions and checks
single-byte/eight-bit routing, stack cleanup, ignored bytes and put-back,
charset state, and the CSI token loop. External service fixtures **record calls**;
they do not implement screen or application services. The parameter-related
fixtures return controlled tokens, so this test does not prove end-to-end CSI
parsing. The separate DOSBox-X check executes one callback-routing self-check
under DOS. Results retain the exact executable digest in `build/escape/` and
`build/escape-dos/`.

## Remaining work and legacy waits

Link this entry with the actual parameter reader, transition and command
modules; supply the recovered or maintained application services and charset
state. Then test actual escape streams through serial receive and screen output.

No timeout fix is silently applied. The main skip loop and charset selector
loops have no local deadline: a provider that returns NUL indefinitely causes
an indefinite loop. The parser-token loop also depends on its callees advancing
or terminating. A future maintained fix should use an explicit abort/timeout
contract across byte provider, parser and escape entry, while retaining this
exact baseline for comparison. A provider returning ffffh at end of fixture
input currently follows the original unknown-command return path; it does not
establish live UART timeout behavior.
