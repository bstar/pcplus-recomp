# Keyboard mapping files and selection

The original2.01 KBD and KEY formats are proved by their actual loaders,
writers, editors and consumers. A lossless host codec and a strict DOS KBD
selection reader are implemented in `src/key_mapping/`. No installed KBD, KEY
or private PRM contents were read for this recovery. Original filename strings
and the selected EXE's generic startup table are separate evidence from any
historical per-profile factory defaults.

`src/key_mapping/provenance.json` records original SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`, exact code
ranges/file offsets/hashes and saved REA IDs. The normal host/DOS reader build
does not require that original artifact or a REA database.

## KBD: profile-indexed terminal sequences

Resident `0cd2..0dad` opens the selected META filename DS3262. If it has no dot,
the loader appends `.KBD`. It passes the filename through path resolver353d and
opens binary read mode. On open failure it reports a UI error, replaces the
selected name with `PCPLUS.KBD` and attempts that file. If both opens fail it
reports another error and returns0.

After a successful open it seeks to `terminal_id*948`, using DS1d18 as the
profile ID, and reads one948-byte block into DS3378. It then closes and returns1.
Each block holds **79 slots of12 bytes**, indexed at `profile*948 + slot*12`.
The emitter0a62 consumes each slot as a NUL-terminated string; normal content
therefore fits11 bytes. There is no header, magic, version or checksum in this
loader. It does not check fread/fseek/fclose results or EOF. A short selected
block can partly overwrite the old map while still returning success; suffix
bytes are ignored by original selection.

The program has33 named terminal IDs0..32, but that is **not a file-format block
count limit**. The installed inventory reports31,284 bytes, exactly33 blocks;
its filename/size do not establish that its contents are pristine defaults.
Maintained codecs/readers accept a positive whole number of948-byte blocks and
require the selected index to exist. They do not reject additional complete
blocks or invent a file-version signature.

Useful directly traced slot identities are:

| Slot | DS address | Consumer |
| --- | --- | --- |
|0..4 |3378,3384,3390,339c,33a8 | Keypad multiply/minus/plus/decimal/divide helpers |
|5 |33b4 | Extended/keypad Enter helper |
|6 |33c0 | Tab |
|8 /9 |33d8 /33e4 | Plain scan52 Insert /53 Delete |
|10 |33f0 | Backspace |
|54 /55 |3600 /360c | Alternate Insert /Delete route |
|72..75 |36d8,36e4,36f0,36fc | Ordinary Up,Down,Left,Right scan helpers |
|78 |3720 | Ordinary Enter |

The complete scan-to-helper table and keyboard routing are independently
recovered in the keyboard execution module; this list does not assert that every
key uses a KBD slot or that ASCII key codes are themselves slot numbers.

## Byte encoding, pacing and modes

The KBD emitter0a62 stops on stored00 and translates stored**ff** to serial**00**.
Other nonzero bytes are emitted literally. Its loop has no caret expansion or
tilde/pause grammar; `^M` is two literal characters in this path. Consequently a
literal serialff cannot be represented through this original slot emitter.
The host codec offers separate storage-byte and wire-byte accessors so this
distinction remains explicit.

After every emitted byte,0a62 calls the calibrated delay6b72 with DS1d68. That
setting is in the proved PRM memory image at offset**01e4h**, since its DS base
is1b84. It is a calibrated-loop argument, not a proved number of BIOS ticks or
milliseconds. File loading does not assign a pause-byte convention. KEY/TEXT
macro processing is a separate execution path, described below.

Mode helper0b4e scans all79 slots in memory when DS8fe8 enables DEC behavior.
It compares full strings against `ESC[A` through `ESC[D`, or their `ESCO` form,
and changes byte1 in matching slots to the requested `[`/`O` form. It does not
blindly replace every ESC sequence or reload the file. This matters for a custom
map: equivalent arrow strings in other slots change too, while longer sequences
or unrelated bindings remain untouched. Profiles4 VT220 and6 ANSI both enter
the original DEC-capable profile range2..11; this does not prove that their
historical KBD file blocks are identical.

## KEY: ten action definitions

Overlay3 reader `e1cc..e20b` and writer `e20b..e24a` transfer ten54-byte records,
total**540 bytes**, at DS3756. Each record is:

| Offset | Bytes | Meaning |
| --- | --- | --- |
|0 |2 | Little-endian action kind |
|2 |52 | NUL-terminated text/name with opaque tail |

Original label table DS2290 names kinds0 ASPECT,1 PROGRAM,2 HOOK,3 TEXT.
The editor `e294` cycles0..3 and limits input to50 content bytes, although the
52-byte storage region can hold51 plus NUL. The codec preserves the storage
capacity and unknown16-bit kinds; callers must validate execution semantics
separately. No header, magic, version or CRC is present in these IO calls. The
original reader also ignores short reads and suffixes; the host codec requires
exactly540 bytes as a maintained validation policy.

`e18a` uppercases the selected KEY filename DS21d8 and appends `.KEY` if no dot
exists. If loading fails, it calls default initializer e24a and writes a new
file at that name. Defaults set each action to3 TEXT and the first text byte to
NUL; they leave the other51 bytes untouched. The host `empty_text()` constructor
re-authors TEXT/empty semantics with deterministic zero tails rather than copying
original data. Original automatic file creation is **not** part of the maintained
read-only KBD reader.

The independently traced TEXT kind3 consumer47b6 calls sender48cc and caret
decoder4934. Unlike KBD slots, TEXT definitions therefore interpret caret
escapes: `^@` becomes storedff, then serialNUL. Sender48cc compares the expanded
byte against pause setting DS1d66 (PRM offset01e2h) before ff conversion; a match
uses BIOS delay6b98 with argument9. Other bytes use the original pacing1d68.
See `MODEM_CONFIGURATION.md` and `MODEM_SEND.md` for exact caret/pause behavior and
bounded maintained policies. The live terminal supports bounded TEXT and local
PROGRAM through explicit `/T:FILE.KEY`; see [LIVE_META_KEYS.md](LIVE_META_KEYS.md)
and [LIVE_PROGRAM.md](LIVE_PROGRAM.md). ASPECT/HOOK remain unsupported. Exact
native routing and executor recovery remain separate from the maintained runtime.

## Selection, precedence and defaults provenance

Original terminal reset20a4 calls KBD loader0cd2 after setting the profile state.
The selected directory entry's postconnect path writes its terminal ID to1d18;
a nonblank META field copies to3262. A nonblank KEY field copies to21d8, appends
`.KEY`, uppercases and sets a caller return flag. Resident5695 tests returned
flag2 to call the KEY loader stub bae7 and flag4 to reload KBD. Interactive keymap
editing145a invokes `PCKEYMAP.EXE` using current profile and META filename,
then reloads0cd2. This is profile/file-selection precedence; runtime command
hotkeys, keyboard action definitions and terminal binding precedence remain the
keyboard execution module's separate responsibility.

The raw1,264-byte PRM image includes profile1d18 at offset0194h and per-byte
mapping delay1d68 at01e4h. Active KEY filename21d8 and META filename3262 are
outside that PRM block, so neither is assigned a guessed PRM offset here.
Other observed dispatcher controls at1d6e/1d70/1d74 are in the image, but their
complete user-visible setting semantics have not been established by this file
format recovery.

The selected EXE's startup-data overlay contains a generic79-slot table at3378,
with punctuation, CR/Tab/BS, keypad digits and many empty slots. It is not a
separate profile4/6 mapping table. The normal loader replaces it with the
selected file block. No pristine companion KBD or PCKEYMAP default generator
has been verified in this scope, so exact historical VT220/ANSI default blocks
remain **unresolved**. Installed inventory size/hash is only corroborating
metadata. The public implementation does not copy those installed bytes or label
newly authored ANSI mappings as recovered factory defaults.

## Strict source-owned DOS reader

```c
unsigned __cdecl keymap_dos_read(const char *path, unsigned profile,
    unsigned char *destination948, keymap_dos_result *result);
```

Compile `keymap_dos.c` and `keymap_dos_fs.c` with include path
`src/key_mapping`. Near C caller cleanup8, DS=SS, full unsignedAX status. The
optional14-byte result has status0, DOS error2, close error4, bytes-read32 at6,
file-length32 at10; `keymap_dos.inc` mirrors these offsets. Status codes are:

| Status | Meaning |
| --- | --- |
|0 | Success |
|1 | Invalid path/buffer extent or overlapping caller buffers |
|2 | Open error |
|3 | End/selected-block seek error or unexpected seek position |
|4 | Empty/nonwhole file, absent requested profile or short selected read |
|5 | Read error |
|6 | A selected slot lacks NUL within12 bytes |
|7 | Close error after otherwise successful processing |

Paths have1..63 bytes and are explicit; there is no environment lookup or default
fallback. The reader checks nonwrapping, mutually disjoint near extents before
IO or result mutation. It queries file length with real DOS INT21h/AH42h, requires
a positive multiple948 and a present selected index, seeks and reads into a
948-byte local stage, validates all79 strings and closes before committing.
Every opened handle has a close attempt on every path. A close error is recorded
even when a preceding failure remains primary. Errors leave destination948
unchanged; rawff, opaque tails and unused bytes remain unchanged on success.
Only the selected block's strings are interpreted; other complete blocks can
contain unknown/malformed strings. No file is written and no UART is touched.
External mutation is not locked out; successful validation does not identify a
file version or prove every block is usable.

The host `LegacyKbd201`/`LegacyKey201` codecs similarly preserve arbitrary raw
bytes, including malformed strings. String access raises on missing NUL;
serialization remains lossless. Setters replace only content/terminator (and
KEY kind when requested), preserving opaque tails. Blank KBD fixtures are
synthetic empty maps, not historical defaults.

## Strict source-owned DOS KEY reader

```c
unsigned __cdecl key_actions_dos_read(const char *path,
    unsigned char *destination540, key_actions_dos_result *result);
```

Compile `src/key_mapping/key_actions_dos.c` with its header include path. Near C
caller cleanup6, DS=SS, full unsignedAX status. The optional8-byte result contains
status0, primary DOS error2, close error4 and bytes processed6; the NASM include
`key_actions_dos.inc` mirrors that ABI. Status0 is success;1 argument/extent/
alias rejection;2 open;3 read;4 nonexact size;5 unknown kind;6 unterminated text;
7 close after otherwise successful processing.

The path is explicit and1..63 bytes. Invalid, wrapping or overlapping path,
destination and result extents cause no IO or result mutation. The reader stages
540 bytes, requires exact EOF, validates all ten16-bit kinds as0..3 and every
52-byte text region for NUL, then closes before copying any destination byte.
Partial reads are completed, but truncated or oversized files are rejected.
Every opened path attempts close, and a close failure is recorded even after an
earlier primary error. Failures preserve all540 destination bytes. Success
preserves raw text, casing and opaque tails without normalization.

There is no default-file search, creation, write, caret expansion or action
execution in this API. Schema-valid ASPECT/PROGRAM/HOOK kinds do not establish
live handlers; those remain application capability checks. In particular, a
lone trailing caret is valid stored text but overruns the original TEXT decoder.
The bounded live TEXT invocation must reject it before emitting command bytes.
The reader intentionally does not confuse byte-layout validity with runtime
macro validity. Double `^^` expands to1eh, while triple `^^^` emits a literal
caret; these are consumer rules, not a KBD-slot escape grammar. Configured pause
takes precedence over ff-to-NUL translation in the original TEXT sender.

`standalone/check_key_actions_dos.py` passes11 real DOS groups and22 declared
IO/close/schema/alias fault checks. Cases cover all four kinds, raw caret/pause
shapes,51-byte valid text, stored trailing caret,539/541-byte files, last-record
invalid kind/string, nonzero kind high byte, fragmented reads, EOF read failure,
primary/secondary errors and48 repeated failures followed by a valid read. All
synthetic files remain unchanged and a missing file is not created. Original
KEY IO remains the separately replayed permissive behavior above.

## Checks and remaining gates

```sh
./tools/dev --command python3 -m unittest discover -s src/key_mapping -p 'test_*.py' -v
./tools/dev --command python3 standalone/check_keymap_dos.py
./tools/dev --command python3 standalone/check_key_actions_dos.py
# Optional explicit original; synthetic memory-only FILE/path/UI services:
./tools/dev --command python3 src/key_mapping/check_original.py \
  analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

Six host groups cover byte-exact roundtrip, all33×79 slot offsets in synthetic
fixtures, tail preservation, ff/NUL distinction, unknown kinds and malformed
storage. DOS tests pass9 real-file groups over80 profiles, including file lengths
and selected offsets beyond64K, plus22 explicitly declared IO/seek/alias fault
checks. All fixture files remain byte-identical. Original replay passes45 cases:
33 profile seeks, named-KBD fallback, five short/suffix cases each for KBD and
KEY, and missing-KEY default initialization/file creation. It executes the actual
original loader/save/default instructions; only FILE/path/UI services are modeled.

The explicit reader supplies a safe pre-UART import boundary. Complete keymap
editing, historical per-profile defaults, ASPECT/HOOK execution, the
complete original keyboard UI and remaining application features remain open.
