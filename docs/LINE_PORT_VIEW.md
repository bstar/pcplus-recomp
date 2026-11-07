# Native Alt-P display and persistence

The maintained popup renderer now matches the authentic 2.01 popup for the
observed default-color 80x25 cases. This follows the [414-byte key selector
recovery](LINE_PORT_RECOVERY.md). Live Alt-P integration remains pending; the
installed RBADE091 release still opens the general settings editor.

## Observations of the authentic program

Two separate DOSBox-X 8086 runs execute the unmodified original PCPLUS.EXE,
SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
They use dummy COM1 and a copied local configuration with a deliberately seeded
COM1 /19200 /8N1 prefix. The passive timer watcher reads VGA/BDA; it does not
patch the original or its UART. Captured screens and all copied configuration
remain in ignored build storage. No synthetic analysis image is executed.

Each run opens Alt-P, selects 9600 then even parity, closes the popup, and
reopens it. Escape leaves the entire 1264-byte PCPLUS.PRM unchanged, while
reopening displays 9600 /8E1. Alt-S preserves the file length and changes only
byte offsets 2 and 4 (baud 5→4, parity 0→2). The other configuration bytes remain
identical. This corroborates session edits versus explicit persistence; it
does not prove physical UART timing or serial-register correctness.

Both runs restore all 1920 live display cells above the status bar after the
popup exits. The popup cursor is row 18, column 67, zero-based. Its footprint is
rows 2..19, columns 18..76 with a bottom-row LINE/PORT SETUP title. These coordinates
are specific to the observed 80x25 mode.

REA reads of the original-derived data in the static overlay image establish:

| Data | Evidence | Finding |
| --- | --- | --- |
| DS5EC0 | `ev_4d6f43f46beccb2dc8f6933da8b759acefbe0ef366fdf55ee38121b05b48d0cd` | Default filename PCPLUS.PRM |
| DS77EA | `ev_710bd9933042b1807b7dd947b3b970748f6c0d33288fb8897901c2d99124898e` | Update mode `r+b`, rather than truncate/create |
| DS29DE | `ev_d7c0a31a9daa6bcf9e5773d842e2d6c6690a2a15aa9a92d5a7347f292a7f660f` | Nine baud-label pointers |
| DS12C2 | `ev_118c01a0f259ca8ada2af5e8c276e2be18c5942bcfd4f84000eb7ab3cf60574a` | 300,1200,2400,4800, 9600,19200,38400,57600,115200 |
| Refresh function | `ev_193514aaee3d2993a8a56461b1411b90c6287572d9b14df069d7a64d5f8e3497` | Native baud field is a string pointer, followed by parity/bits/stops/port |

Data DS offsets are mapped through original overlay 32's file offset 153936 and
relative image offset 64368; REA linear addresses use load segment 1000h. Static
bytes show defaults, while the authentic DOS observations establish this run's
actual file persistence. A speculative read at DS031F was **not** a settings
format string:031F is the refresh service's display coordinate argument.

## Maintained source and verification

`src/line_port/view.c` draws only the documented popup/footer footprint into a
caller-owned far text frame. It rejects invalid native state indices and short
frames without writing. It has no DOS file, UART, saved-screen, keyboard or
cursor dependency. The eventual terminal caller must own those services.
Default attributes 7/11/113 match the observed configuration; configurable colors
and alternate row counts require further work before live integration.

The actual DOS diagnostic produces three states: 19200 /8N1, 9600 /8N1 and
9600 /8E1. Comparing each with native initial/edited/reopened captures in both
sessions gives **9136 identical character/attribute cells**, zero differences.
Cells outside the source renderer's declared footprint retain a sentinel.
Invalid port, baud, parity, stop and data values, insufficient length and null
arguments are rejected without frame mutation. A five-file public-source export
reproduces the DOS EXE and all three output frames exactly, without originals,
configuration, analysis databases, earlier objects or Git metadata. The outer
pinned Nix environment supplies tools.

The initial render comparison found code-segment pointer expressions losing
their segment frame under this 16-bit compiler. Explicit far pointers before
indexed arithmetic and separate preset branches fix that defect. The accepted
receipt records only the corrected build.

```sh
./tools/dev --command python standalone/build_line_port_view.py
./tools/dev --command python standalone/test_line_port_view_dos.py
./tools/dev --command python standalone/prove_line_port_view_source.py
# Explicit original-dependent observations, each requiring a fresh output path:
./tools/dev --command python standalone/test_line_port_original_dos.py \
  --output build/NEW-line-port-escape
./tools/dev --command python standalone/test_line_port_original_dos.py \
  --save --output build/NEW-line-port-save
./tools/dev --command python standalone/record_line_port_view.py \
  --escape build/NEW-line-port-escape --save build/NEW-line-port-save
```

The source-proof command also requires a fresh `build/line-port-view/source-proof`
destination. [The receipt](validation/line-port-view.json) binds source hashes,
DOS output, independent export and the two private original-session receipts.

Next connect the renderer and recovered selector to the maintained foreground,
saved-screen and serviced-input owners; map native line indices into current
settings; provide checked persistence and serial application; handle unsupported
COM5..8 explicitly. Verify connected traffic, refusal/failure paths, modal return
and configuration colors before package or physical deployment. The original
save function lacks visible write/close checks, so copying that unchecked I/O
would not satisfy the maintained build's persistence requirements.
