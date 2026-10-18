# PCPLUS.PRM recovery ledger

Actual PCPlus 2.01 code establishes a **1,264-byte (`04f0h`) binary memory-image
format**, copied to/from DS `1b84h..2073h`. A separate command saves its first ten
bytes only. The serial prefix, port tables, selected terminal/attribute fields, modem
commands and selected dialing/flow settings are mapped from instructions;
the rest remains opaque. No installed or
user-customized `.PRM` contents were opened for this investigation.

This is a partial format recovery and maintained DOS I/O backend, not a complete
configuration subsystem. `src/config/prm.py` is a source-only host-side
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
| Overlay 3 `d4d0` | Launches PCSETUP.EXE with a constructed command containing the current PRM path, literal PCPLUS and an unsigned decimal packed DS:1b84 address (see SETUP_NATIVE.md); snapshots selected live settings and reapplies changed screen/terminal/other state after the child returns. | `ev_dd1d40e9cbad7523a355eeea9364e2483b3b2d79e4a051b4911a7905b8eda450` |
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

Modem command/response layouts and selected dialing settings are now proved;
see [MODEM_CONFIGURATION.md](MODEM_CONFIGURATION.md). Remaining recovery is
additional schema coverage, PCSETUP's shared-memory/command ABI, conversion/version
rules in PCINSTAL, complete defaults/startup order, actual DOS persistence/error
handling, and integration into source-built application configuration services.
The maintained DOS backend below now rejects malformed files without the
original implicit rewrite behavior; the host codec remains separate from those
DOS filesystem operations.


## Maintained DOS I/O backend

`src/config/prm_dos.c/.h` now provides source-owned, executable DOS load/save
services for the proved opaque 1,264-byte layout. This is a deliberate maintained
implementation, not recovered original instructions or a complete initialization,
settings editor, schema validator or upgrade converter. It contains no original
configuration bytes and performs no automatic missing-file creation or repair.

```sh
./tools/dev --command python3 standalone/build_config_dos.py
./tools/dev --command python3 standalone/test_config_dos.py
```

The Nix-managed Open Watcom build targets DOS/8086 small model (`-bt=dos -0 -ms`),
with compiler warnings treated as errors. Outputs are `build/config-dos/CONFIG.EXE`
and a separate fault-injected `CFGFAULT.EXE`. The normal executable links actual
DOS handle operations; the second recompiles the same backend against named
injected services to test failures that mapped emulator files cannot reliably
produce. These injected operations are test boundaries, not production DOS code.

Public API:

```c
prm_dos_status __cdecl prm_dos_load(
    const char *path, prm_dos_image *destination, prm_dos_result *result);
prm_dos_status __cdecl prm_dos_save(
    const char *path, const prm_dos_image *source, prm_dos_result *result);
```

Use near data pointers with DS=SS; the explicit 16-bit C calling convention places
three pointer words on the stack, right to left, and the caller removes six
argument bytes. Status typedefs are explicit DOS16-bit unsigned values,
returned in the full AX register; small compiler enums would leave AH
unspecified. `result` may be NULL. `prm_dos_image`
contains exactly 1,264 opaque bytes; no interpreted field is changed during I/O.
`prm_dos_result` reports status, primary DOS error, close error and bytes processed.
Load uses a 1,264-byte stack staging buffer plus its frame/runtime calls; integration
must budget stack space accordingly. The diagnostic reserves an 8-KB stack.
Ordinary Open Watcom C callee preservation rules apply; no exact original PCPlus
register ABI is implied by these new C functions.

Load opens read-only, handles fragmented reads, requires exactly 1,264 bytes,
probes for an extra byte, and attempts close on every path after successful open.
Only a complete exact-size read **and successful close** commits the staging
buffer to the caller's destination. Missing, empty, truncated, oversized, read-error
and close-error paths leave the destination unchanged and never rewrite the input
file. This intentionally replaces the original zero-element-read rewrite behavior.
A matching size is still not a signature or version check; typed field validation
and selecting a known-compatible format remain higher-level requirements.

Save creates/truncates the requested file, writes the exact opaque image, checks
both the DOS result and actual written-byte count, and attempts close. A short
write is an explicit failure even when DOS returns no error code. Primary I/O
errors and a secondary close error are both retained. Close failure cannot be
claimed as a successful durable save. **Direct-save failure can leave a partial
or truncated destination**; transactional replacement/backup is separate
application integration work, not silently promised by this API. No user file
was used to test this behavior.

DOSBox-X passes thirteen real-filesystem cases: exact save/load and optional
result pointer; missing/short/long/empty loads with unchanged destination;
missing-directory and directory save rejection; argument validation; 48 repeated
failed loads followed by a successful open to catch handle leaks; source
preservation; and DOS read-only-file save rejection. The host runner also verifies
that short/long/empty fixture bytes remain untouched and the saved output matches
the complete synthetic payload.

Ten additional DOS-executed injected-error cases pass: failed open without a
spurious close, failed read with cleanup, read-close failure preventing commit,
primary read plus secondary close errors, oversized probe, fragmented reads,
write error with cleanup, short-write failure, save-close failure and exact
successful write. Error-close cases verify the cleanup attempt/reporting contract;
a returned DOS close error cannot itself prove the OS released a handle.
`build/config-dos/{manifest,result}.json` records exact binaries, source identities,
all case results and limits. Physical disks, disk-full persistence, transactional
replacement and full application configuration integration remain unverified.

## Staged DOS replacement

`src/config/prm_replace.c/.h` adds maintained replacement of the opaque image.
It writes a new, exclusive staging file and checks the exact byte count and
close result before moving the previous target to a backup. DOS rename then
installs the staging file. Failed installation attempts restore the backup;
failed rollback retains the original in that backup and reports its location
through explicit state flags. Successful installation removes the backup.
The separate `prm_replace_fs.c` uses DOS interrupt21h functions56h/41h for
rename/delete, preserving actual DOS error numbers and no-overwrite behavior.

```c
prm_replace_status __cdecl prm_dos_replace(
    const char *target, const char *stage, const char *backup,
    const prm_dos_image *image, prm_replace_result *result);
```

All three names must be distinct ASCII8.3 leaf names in the current directory.
The routine rejects case aliases, device names, separators, wildcards, malformed
names, existing recovery files and read-only/directory targets. It never removes
an existing staging/backup file to make a retry succeed. The caller must choose
recovery names, keep the directory stable during the call, and handle the
reported recovery state. Supporting other directories and complete application
settings integration remain work in progress.

`result` may be NULL. A supplied result records primary DOS error, close error,
cleanup error, rollback error, written bytes and three state flags: `installed`,
`original_in_backup`, `stage_exists`. An error after installation can mean the
new image is installed and the old backup remains; callers must inspect those
flags rather than blindly repeat the save. Stage cleanup is attempted after
failure, with any secondary error retained. A close error does not prove the
handle closed or the data reached stable media.

This protects the previous file across the tested operation failures; it is
**not a crash-atomic FAT transaction**. There is a rename interval during which
the original is in the backup and the target is absent. Power loss, filesystem
corruption, arbitrary concurrent modifications, multi-directory replacement,
attribute preservation and automatic recovery after restart are not proved.
Direct `prm_dos_save()` remains a separate create/truncate operation.

```sh
./tools/build test-config-replace
```

The diagnostic runs fifteen real DOS-filesystem checks and twenty-three
state-based fault cases. They verify exact installation, preservation of
preexisting recovery files, actual no-overwrite rename behavior, short/write/
close failures, backup/install failures, failed rollback, cleanup failures and
concurrent appearance of destination names. Fixtures use synthetic bytes only,
including an old file of a different size. Results and executable hashes are
recorded in `docs/validation/config-replace.json`; local files remain under
ignored `build/config-replace/`.


## Assembly-owned startup and C ABI

`./tools/build test-config-abi` links the real C load/save/replacement APIs into
a source-owned NASM DOS entry with DS=SS and an8-KiB stack. It checks complete
16-bit AX statuses, near-pointer argument order, preserved registers, caller
cleanup and an actual1264-byte DOS save/load roundtrip. It explicitly links
Open Watcom's small-model library subset without invoking C startup; this proves
the DOS-handle/string subset used here, not arbitrary C runtime initialization.
Offset zero is reserved as the C NULL near pointer. Future integration must not
pass a legitimate assembly allocation at DS:0000 as a C pointer.

This test exposed the compiler's small-enum return convention before terminal
integration. The APIs now use explicit unsigned status typedefs so assembly
callers receive the documented AX value. C callers retain the named status
constants and result layout. The live terminal now imports a validated read-only subset through `@FILE.PRM`;
see [startup configuration](STARTUP_CONFIGURATION.md). Complete application
settings, defaults and configuration UI remain open.


The maintained offline [PRMEDIT editor](SETUP_EDITOR.md) now stages and validates
44 mapped fields and saves through the checked DOS replacement backend. It does
not implement PCSETUP's original parent-memory consumer protocol, which remains
unavailable; see [native invocation evidence](SETUP_NATIVE.md). Complete schema,
defaults, path precedence and live setup integration remain open.

## Input translation selection

The native overlay3 owner at CSdef8 reads DS1d64, corresponding to PRM offset
01e0h within the DS1b84 memory image. Selection0 initializes identity;1 loads
PCPLUS.XLT;2 initializes identity and sets the driver receive mask to7fh. Other
native values fall through to identity/ffh. The maintained importer accepts0..2
and rejects other values with status12 before committing its42-byte settings
plan. Its saved-mode byte range is disjoint from pause byte01e2h and pacing
word01e4h. The raw host codec remains lossless and performs no implicit semantic
repair. See [translation recovery](TRANSLATION.md) and
[live selection and scope](LIVE_TRANSLATION.md).

The maintained45-field PRM editor exposes this word on its TERMINAL page. Live
setup classifies a change with mask0800h, keeps the active table/mask, and reports
it deferred until restart; independent edits can still apply. Explicit /X keeps
its effective table selection after validating the saved PRM, so it never hides
an invalid raw selection. The pure candidate ABI is now626 bytes: serial42,
modem368, directory214 and trailing change word2.
