# PCPLUS.PRM recovery ledger

Actual PCPlus 2.01 code establishes a **1,264-byte (`04f0h`) binary memory-image
format**, copied to/from DS `1b84h..2073h`. A separate command saves its first ten
bytes only. The serial prefix, port tables and selected terminal/attribute fields
are now mapped from instructions; the rest remains opaque. No installed or
user-customized `.PRM` contents were opened for this investigation.

This is a partial format recovery, not a complete configuration subsystem or a
DOS configuration implementation. `src/config/prm.py` is a source-only host-side
lossless codec with a validated serial editor. It preserves unknown bytes and
performs no file IO. It does not generate a complete usable default configuration.

## Evidence and concrete call paths

The verified original executable is 214,016 bytes, SHA-256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Overlay 32 contains initialized DS data beginning at original file offset
`25950h` (153,936). Thus original embedded DS offset `x` is found at file offset
`25950h+x`; this mapping was corroborated by filename references and the saved
overlay manifest. Code overlays are context-sensitive: `d734` below belongs to
code overlay 3, not an identically addressed routine in another overlay.

| Context and entry | Observed instructions and consequence | REA assembly Evidence |
| --- | --- | --- |
| Overlay 3 `d5f8` | Calls locator d647. Zero result selects d60c (create/save); nonzero passes resolved path to d734 (load). | `ev_6e41f4315160eed484c6985434e0c2e36cd741f5c39358a4cfed577bd8937e40` |
| Overlay 3 `d60c` | Opens DS5ec0 path in `wb`; writes one element of size04f0 from DS1b84 using resident86ac; closes. Open failure calls error335c with the creating-PRM message. Write result is not checked in this routine. | `ev_39cec3eeeb0684b87998dd63fdacb5e25ecc38140de5a9226de9d84532418bab` |
| Overlay 3 `d734` | Opens caller path `rb`; reads one04f0-byte element to DS1b84 through845a. A zero returned-element count closes/reopens `wb` and writes current DS1b84 memory. | `ev_45e3897063c74080373317d5c7421f5f9cf03ff252df70c61a29e4c5641afde9` |
| Overlay 3 `d647` | Resolves PCPLUS.PRM. A successful current-directory text-mode `r` open is accepted, then current-directory path is expanded. Otherwise shared path helper353d searches its configured environment fallback; that branch checks file length equals04f0 before accepting it. | `ev_0b7e0098ca824727703a9c43e5df54c85c2b94a7564b9ae9830451d095e2ce34` |
| Resident `353d` | Tries requested filename, otherwise gets environment name through DS324c; that initialized pointer names `PCPLUS`. Appends path separator/name when appropriate. | `ev_1cd43dbde8697560fddafd763fd3ab56971d91bd6badd8b88553d8e1cc1d6417` |
| Overlay 20 `f260` | Opens resolved configuration `r+b`; writes one ten-byte element from DS1b84; closes. Failed open follows a UI/error path427f. Write result is not checked here. | `ev_d52db527211bf1c3ffed8dd5924051027974ff1fcd63bd9dc4f05d7bc3e0211e` |
| Overlay 3 `d4d0` | Launches PCSETUP.EXE with a constructed command containing the PCPlus path and a converted DS:1b84 address; snapshots selected live settings and reapplies changed screen/terminal/other state after the child returns. | `ev_dd1d40e9cbad7523a355eeea9364e2483b3b2d79e4a051b4911a7905b8eda450` |
| Resident `033e`, `0366` | Uses baud selector, parity/data/stop words, selected port's I/O base and IRQ table entries to configure actual recovered UART code. | `ev_25025ce97e87aa22d04eb4d6b2903b39d9c15b68e3fc91a5aaf4ed75e06d23a1`, `ev_29b4f4536b443b5d3ee7209840b7c813c466c488e71d287a8ca20f7cfb8c806a` |

No new native session was
opened: saved REA exports were reused. Runtime-library call names such as
fopen/fread/fwrite are analyst identifications corroborated by their actual
argument layouts, read/write implementations and open-mode strings.

The full read path performs **no signature, checksum, embedded version or field
validation before applying the memory image**. The locator's size check is not
universal: its successful current-directory branch bypasses that check. This
bounded observation does not establish what the separate original installer or
PCSETUP might validate; those programs remain unrecovered. A matching length by
itself cannot identify an arbitrary file as a compatible PRM version.

## Proved layout

All fields below are unsigned little-endian words. Relative offsets are measured
from file/memory-image start, not from original executable start.

| PRM offset | Original DS | Meaning and evidence |
| --- | --- | --- |
| `0000` | `1b84` | Zero-based COM selector; UI writes0..7. UART setup indexes the per-port tables with it. |
| `0002` | `1b86` | Baud index; UI digit selections cover0..8. |
| `0004` | `1b88` | Parity selector0=N,1=O,2=E,3=M,4=S, proved by overlay20 f1fa and UART ac5d. |
| `0006` | `1b8a` | Stop bits, UI1/2; passed to UART line-control helper. |
| `0008` | `1b8c` | Data bits, UI7/8; original ac5d distinguishes7 from its8-bit fallback. |
| `0174..0183` | `1cf8..1d07` | Eight UART I/O base words, selected by COM index. |
| `0184..0193` | `1d08..1d17` | Eight IRQ-number words; resident0366 adds8 to derive interrupt vector. |
| `0194` | `1d18` | Terminal ID, also consumed by recovered dispatcher/reports/reset paths. Complete enum validation remains open. |
| `019c` | `1d20` | Autowrap enable state, written by recovered CSI mode7 handlers and consumed by rendering. |
| `019e` | `1d22` | Scroll-enable state, consumed by recovered linefeed. |
| `01ae`, `01b0`, `01b2`, `01b4`, `01b6` | `1d32..1d3a` | Configured normal, bold, additional preset, reverse and underline attributes; see ATTRIBUTES.md. |
| `03ec` | `1f70` | Current attribute word, also mutated by recovered SGR helpers. This illustrates that the legacy image contains live state as well as configuration values. |

The baud labels pointed to by DS29de's nine-word table are:
300,1200,2400,4800,9600,19200,38400,57600,115200. The table stores **pointers to
strings**, not those numeric baud values. Overlay20 f05c writes serial selectors;
f1fa maps parity/display values. Their REA Evidence IDs are
`ev_d7f2fc242e462dd12849254b6bbfdcd58b5b54250ccfb45a8a76649ed6579b7a`
and `ev_8c0df54528020eff4ed07227d19c5490c4b357d975b6065fd517b270973687b6`.

Initialized words in the verified original executable give COM index0, baud
index1, parity0, stop1, data8 (COM1/1200/N/8/1). These are embedded baseline
initializers, **not measurements of this user's settings**. Other startup code,
command-line processing, the full PRM, modem configuration and external setup can
change effective values. The complete source-owned default schema and startup
initialization sequence remain unrecovered. The codec deliberately offers no
"new default PRM" constructor because zeroing unknown fields is not a justified
replacement.

## Original call-path replay and codec tests

```sh
./tools/dev --command python3 analysis/config_format.py
./tools/dev --command python3 -m unittest discover -s src/config
```

The analyst script reads only the verified executable, overlay manifest and
retained REA metadata. It executes actual overlay3/20 instructions with explicit
synthetic stdio boundaries. Six cases prove whole-image save/load, zero-element
read fallback, a modeled partial read followed by fallback rewrite, failed-open
error dispatch, and ten-byte serial-prefix save. Output under
`build/config-analysis/result.json` includes exact source identity, call arguments,
evidence IDs and synthetic hashes; it contains no copied user config data.

The original caller rewrites current memory after a zero-element read. Given
fread's partial-copy contract, a truncated read can therefore lead to rewriting a
mixture of newly read bytes and prior memory. The replay explicitly models that
contract and proves the subsequent caller behavior; it does **not** claim to have
observed real DOS filesystem corruption or a full original application startup.
Open-error handling reaches the real335c error call boundary; its broader cleanup
and exit chain remains outside the replay.

Five host-codec tests cover opaque roundtrip, serial-prefix-only mutation,
UI-supported range rejection, exact image length/immutable snapshot, and proved
word/port-table locations using synthetic data. Unknown bytes are preserved;
parsing does not silently normalize invalid serial words. Editing serial settings
validates supported UI values, while raw proved-word edits validate only uint16
storage. Synthetic fixture images are **not bootable startup defaults**.

Remaining recovery is field/schema coverage beyond the proved words, string and
modem-command layouts, PCSETUP's shared-memory/command ABI, conversion/version
rules in PCINSTAL, complete defaults/startup order, actual DOS persistence/error
handling, and integration into source-built application configuration services.
A maintained loader should reject malformed files without the original implicit
rewrite behavior, but that deliberate change is not implemented as a DOS loader
by this host codec.
