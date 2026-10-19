# Native terminal reset reconstruction

`reconstruction/terminal_reset/` recovers **2,301 exact instruction bytes** from
PCPlus2.01, verified SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
These are recovered instructions with analyst names, not vendor source. No
original binary, initialized data, private configuration or REA database is a
normal build input. All retained static REA evidence IDs, file offsets and byte
hashes are in `provenance.json`.

The SET recovery pass corrected an OMF relocation omission in the status
routine's script-label pointer at3044. `terminal_reset_script_label` now replaces
the fixed D464 immediate in relocatable builds; flat native bytes are unchanged.
The linked/original regression checks the actual label pointer and bytes before
the explicit UART-status dependency. See [SET recovery](ASPECT_SET_NATIVE.md).

| CS range, end excluded | Bytes | Export |
|---|---:|---|
|20a4..246c|968|terminal_reset_native|
|281c..2a35|537|terminal_reset_geometry|
|2a36..2a6e|56|terminal_reset_width|
|2fb8..31bb|515|terminal_reset_status_refresh|
|6f60..6f76|22|terminal_reset_clear_video|
|27ea..280a|32|terminal_reset_clear_shadow|
|2518..2530|24|terminal_reset_cursor_default|
|1f56..1f6f|25|terminal_reset_protected_home|
|4097..40aa|19|terminal_reset_status_fill|
|40c9..40df|22|terminal_reset_underline_default|
|40df..40f6|23|terminal_reset_underline_configured|
|5c20..5c41|33|terminal_set_underline_scanline|
|6edc..6ef5|25|terminal_reset_bios_rectangle|

## Reset modes and actual dependencies

`terminal_reset_native(mode)` is a near **cdecl** entry: caller pushes one
16-bit word and removes it afterward. It preserves BP/SI/DI; ES, flags and other
registers may change. It does not define a success/error result in AX.

Mode0 skips the full profile/state initialization and enters the common tail.
On the tested standard80-column, hidden-status configuration, it calls the real
clear/home, attribute reset, stable geometry handling and tab initialization,
then returns. A special family flag at DS903e instead saves the cursor, invokes
protected-home handling and later restores the saved position; it does not
clear the screen or normalize the current attribute. Both complete zero-mode
paths have been compared with actual original instructions.

**Nonzero mode is different.** It clears video/shadow, derives profile flags,
then unconditionally calls the original **KEY loader0cd2** before the remaining
state sweep. That loader handles filename/default lookup, opens a file, seeks
`948 * terminal_id`, reads the948-byte profile table into DS3378 and closes it.
Its result is ignored by20a4. It is not an in-memory reset callback. The native
KEY/file/UI fallback pipeline is not reconstructed in this module; the
standalone diagnostic traps explicitly at that boundary. The36 tested profile
prefixes stop there honestly, without substituting a successful no-op.

Original **ESC c pushes1**, so the completed zero-mode diagnostic does **not**
establish complete RIS support. CSI terminal-family selection also invokes
nonzero reset. The live application must supply an explicit maintained policy
for preloaded keymaps, geometry, state and application UI; it cannot simply
rename a partial reset to claim the original pipeline is complete.

## State derived by the nonzero prefix

Signed comparisons against DS1d18 produce these exact flags. Other IDs outside
each inclusive range clear the flag; specific-ID rows are explicit equality.

| DS word | Set for terminal IDs |
|---|---|
|d122|1..11|
|8fe8|2..11|
|8ff6|6..7|
|8ff8|13..14|
|9004|22..30|
|cd36|25..28|
|9038|22..29|
|900c|22..32|
|9018|31..32|
|9020|15..17|
|9026|18..19|
|9032|20..21|
|903e|22 or31|
|9048|29|
|904c|30|
|9056|24|
|9058|900c,9032 and9020 all zero|

Names in other modules such as `attributes_monochrome` at8ff6 are observed-use
aliases, not a claim that this flag describes physical monochrome hardware.
IDs4 and6 share d122/8fe8/9058=1;8ff6 differs0/1.

## Subsequent native state sweep: recovered, blocked by KEY dependency

The source after0cd2 is recovered exactly, but this diagnostic does not pretend
the missing loader has run to reach it. Code inspection establishes:

- It clears blink397e and reverse byte321c, but does **not** clear bold397c.
- It restores saved scrolling9016 into1d22 andd004. It does **not** overwrite
  configured autowrap1d20.
- Configured normal1d32 becomes current1f70, cdd4 and erase-attribute byted008.
- It resets the listed modes/charset/status fields, clears72 bytes atcc4a,
  clears100 line-flag bytes atcf86, fills3168 attribute-value bytes with normal
  and clears3168 flag bytes through the configured near-plane pointers.
- Top margins become0; physical last row334a becomes current bottomcee4/ce3a.
  The low byte of saved duplex903c is copied to1d26.
- It calls actual keyboard-mode initialization with `[`, selects the configured
  default cursor shape and initializes tabs through246c.
- It stores original **data pointers**461c/463e in9036, changes response-table
  bytes902d/462c, and stores original **code pointers**bb8f/bb9b incb30. Family
  modes can also select row23. These addresses are relocated named contracts,
  not public copies of original response tables or handlers.

The live application must not import raw stored pointers or assume these
original data layouts are its owned structures. `STARTUP_CONFIGURATION.md`
describes the independently validated configuration subset.

## Geometry, display and remaining contracts

The recovered geometry code handles80/132-column layouts, metadata movement,
viewport/shadow allocation, far freeing and failure reporting. Actual stable
geometry executes without a fake callback in the successful soft-reset test.
A requested wide transition reaches the real far-allocation boundary860f and
fails explicitly in the diagnostic; allocation is not fabricated. Attribute
repair2d98 and application error427f are also external contracts.

The recovered status refresh returns immediately when1d46 hides the status
line. Visible status rendering needs application status/message formatting,
strings and services3226/75e8/7630/82b6. The aa5c carrier-status call can map to
the already recovered live UART `uart_carrier_detect`; this diagnostic leaves
that unused visible-UI dependency explicit. Unknown data semantics retain
address-based `reset_data_*` symbols. Synthetic diagnostic storage contains no
vendor initialized data or private file contents.

Small helpers use actual text/far-fill, erase/cursor and cursor-shape modules.
5c20 writes CRTC underline-location register14h at the configured index port:
31 when disabled, or BDA0485 character height minus1 when enabled.40c9/40df
apply the original support/configuration conditions. These are video controls,
not UART flow settings. Tests observe actual OUT instructions against a declared
hardware model; physical hardware behavior remains separate.

## Building and evidence

```sh
./tools/dev --command python3 standalone/build_terminal_reset.py
./tools/dev --command python3 standalone/check_terminal_reset.py
./tools/dev --command python3 standalone/test_terminal_reset_dos.py
# Explicit analyst comparison; ignored verified original and overlay map required:
./tools/dev --command python3 standalone/check_terminal_reset.py --original
```

The diagnostic uses a256-byte prefix before its synthetic DS layout, so data
symbols move relative to original offsets. This caught and fixed a generator
bug where CS branch target1f6e collided with a DS attribute alias: flat bytes
alone could not reveal the invalid OMF branch. Branches are now classified as
code before data substitution. Both soft-reset paths validate the relocation.
Only BIOS/video/CRTC hardware is modeled; unresolved subsystems trap instead of
returning pretend success.

Eight CPU groups provide **46 genuine original comparisons**: complete standard
and special zero resets,36 full-profile prefixes, width modes, honest allocation
failure, CRTC controls, far-shadow clear and cursor shape. Actual DOSBox-X8086
checks clear/home/current attribute/default tabs on the complete standard
zero-mode path. Results are in ignored `build/terminal-reset/`, with source-only
and opt-in original results kept separately. Full nonzero reset, visible
application UI, allocation/error handling and the complete PCPlus application
remain unfinished.

Final diagnostic `RESET.EXE` SHA256:
`4e7cd57c0f73ad6a84642eedc3f4823548aa4ba0d5968f711c4c62310d52b72e`.
The DS=SS group is59,136 bytes and the build checks that it fits one near segment.
