# PCPlus 2.01 dialing directory

The host codec in `src/directory/codec.py` reads and edits the original **23,050-byte
PCPLUS.DIR layout**. It preserves every byte on round trip, including bytes after
string terminators, unrecognized enum values and explicitly accepted trailing
data. It does not read files implicitly. No user's dialing directory, telephone
numbers, passwords or DTP contents were used to recover or test this layout.

The raw codec is a host-side format recovery. A maintained DOS streaming reader,
startup browser and selected-entry connection path are now integrated into
TERMINAL.EXE; see [live directory selection](DIRECTORY_LIVE.md). Complete original
directory editing, accounting and script/key integration remain open. DTP compatibility
has not been established. There is no proved signature/version field: file length
alone cannot identify this revision or distinguish a directory from unrelated data.

## Proved disk structure

The file begins with ten 25-byte NUL-terminated dialing-code slots, **A through J**.
The 250-byte header is followed immediately by **200 records of 114 bytes**. Original
entry numbers are **1 through 200**; disk offset is `250 + (entry - 1) * 114`.

Overlay8 reader `e812..e8cd` calls C `fread` with `(destination=e484, size=25,
count=10)`, then reads forty five-record blocks of 570 bytes. It places those
records in a 22,914-byte far-memory allocation at offsets 114 through 22800,
leaving its first 114-byte slot unused. That unused memory slot is **not present
on disk**. Creator `e8ce..e929` writes the same header and 200 template records.
Sort/rewrite `e3b0` seeks to250 before writing the records.

The individual writer `dd28..dd93` seeks to `entry*114 + 136`, equivalent to the
formula above. Its full path writes 114 bytes. Its partial path adds 61 and writes
only 11 bytes, the last-call date and completed-call count. This corroborates the
layout independently of the bulk reader. The original reader ignores a suffix;
the host codec requires exact length by default and preserves an opaque suffix
only when `allow_trailing=True` is explicitly requested.

## Record layout

Offsets are hexadecimal relative to the start of a 114-byte record. String
capacities include their terminating NUL. Integers are unsigned storage values;
16-bit words are little endian. Consumers sometimes sign-extend byte fields, so
unknown values must not be sent blindly to an unrecovered DOS consumer.

| Offset | Bytes | Codec field | Observed use |
|---|---:|---|---|
|00|25|`name`|Entry name, editor limit24 bytes|
|19|21|`number`|Dial string, editor limit20 bytes|
|2e|2|`baud_index`|Baud table index 0..8: 300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200|
|30|1|`parity_index`|0 NONE,1 ODD,2 EVEN,3 MARK,4 SPACE|
|31|1|`data_bits`|Actual bit count|
|32|1|`stop_bits`|Actual stop-bit count|
|33|1|`duplex_index`|0 FULL,1 HALF|
|34|9|`script`|Postconnect script name, maximum8 bytes|
|3d|9|`last_call_date`|NUL-terminated `MM/DD/YY` text|
|46|2|`completed_call_count`|Incremented on a successful connection|
|48|1|`protocol_index`|Transfer protocol table index; original default4 is XMODEM|
|49|1|`terminal_id`|Terminal table index; original default6 is ANSI|
|4a|1|`dialing_mode`|0 MODEM,1 DIRECT|
|4b|11|`password`|Password string, maximum10 bytes; not encrypted in the record|
|56|9|`keyboard_file`|Per-entry keyboard file basename, `.KEY` appended after selection|
|5f|9|`meta_file`|META FILE editor field; feeds per-terminal `.KBD` key translation file|
|68|1|`port_override`|0 DEFAULT,1..8 COM1..COM8|
|69|9|`note_file`|Note basename, `.NOT` appended by note editor|

These fields cover all 114 bytes without padding gaps. Padding *within* strings
remains opaque and is preserved. The codec returns raw bytes for strings; callers
choose an encoding explicitly. A field without a terminating NUL remains lossless
as raw storage, but its string accessor raises `ValueError`. New string values
must fit and cannot contain NUL. Edits update the prefix and terminator only,
preserving the remainder of the old slot. Numeric setters validate storage width;
they do not normalize enum values or claim all possible values are usable.

The template used by the original creator is zero-filled except for baud index 2
(2400),8 data bits,1 stop bit, date `00/00/00`, protocol 4 (XMODEM), and terminal 6
(ANSI). `DialingDirectory201.blank()` re-authors these values; actual execution of
the original creator emits precisely the same 23,050 bytes.

## Consumers and bindings

The editor is overlay6 `e3b0..f023`. Its114-byte local copy, pointer-table lookups,
input limits and labels corroborate field offsets. The selected record resides
at DS:e650; bulk storage base/segment are DS:e64c/e64a. Overlay4 `ddb6..dde0`
loads a selected record and sets current entry DS:e482. `dd94..ddb5` stores the
selected record back to far memory. Original startup filename is DS:66d2,
`PCPLUS.DIR`; startup data is overlay32 of the verified EXE.

Overlay5 dial engine `e5e3..e8ac`, specifically `e6ea..e729`, applies the serial
settings. Port override 0 retains current DS:1b84. For a nonzero override, it closes
the old port at `adba` when needed and sets the zero-based port to `override-1`.
It copies baud/parity/stop/data into DS:1b86/1b88/1b8a/1b8c and duplex into DS:1d1a,
then calls serial reconfiguration `03a7`. Thus DEFAULT applies only to the port;
it does not suppress the other per-entry serial overrides. The mode byte at4a
selects modem dialing versus a direct connection; it is not a port selector.

Overlay4 `d4d0..da4d` records successful-call statistics and applies the selected
protocol and terminal. In `d991..da04`, a nonblank META field is copied to DS:3262;
a nonblank keyboard field is copied to DS:21d8, `.KEY` appended and the result
uppercased, setting result bit 2. A nonblank script is copied to DS:ce6a and sets
result bit 1 for its caller. This proves the stored binding and handoff; the codec
does not implement ASPECT script execution. Blank here means first byte NUL or
space, matching the observed test rather than trimming all whitespace.

The META label needs care: an alternate directory heading calls it MAC FILE, but
resident `0cd2..0dac` appends **`.KBD`**, opens that file with fallback `PCPLUS.KBD`,
and reads a 948-byte terminal-dependent block into DS:3378, using an offset of
`terminal_id*948`. It is a key translation table binding, not proof of an ordinary
`.MAC` script file. The separate keyboard field appends `.KEY`. Overlay7 note
editor `e9ed` appends `.NOT`, despite another alternate heading saying JOT FILE.

Overlay5 `ec61` expands letters **A..J** inside the uppercased phone string using
25-byte header slots: the pointer formula is `letter*25 + de2b`, which equals
`e484 + (letter-'A')*25`. That routine also supports a separate quick-dial command
syntax and a 60-byte result limit. Those command semantics are not silently
substituted into the codec; it preserves the number as stored. Protocol/terminal
indexes are kept raw, including implementations not recovered in TERMINAL.EXE.

## Reproduction and tests

Run the source-only synthetic suite, with no originals or installed data:

```sh
./tools/dev --command python3 src/directory/test_codec.py
```

Seven groups cover a hand-built disk layout, all 200 slots and every byte in
randomized round trips, exact edit spans and padding preservation, enum storage
bounds, unterminated/maximum-length strings, malformed sizes/indexes/suffixes,
complete layout coverage and template semantics.

The separate optional analyst replay requires an explicitly supplied original
EXE, checks its full SHA256 before execution, and never opens any directory file:

```sh
./tools/dev --command python3 src/directory/check_original.py \
  analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

It runs actual original `e812/e8ce/ddb6/dd94/dd28` x86 instructions with synthetic
memory-only FILE data. C path/stdio and far-memory-copy calls are explicit modeled
boundaries. It verifies creator output against the host template byte-for-byte,
reader counts and far-memory placement for all 200 randomized records, full and
11-byte writes for entries 1, 97, 200, and rejection of a truncated last record.
It does not establish real DOS filesystem error handling, timing or a working UI.
The local result is `build/directory/original-replay.json`; it is not an input to
the normal source-only suite.

## Provenance and remaining work

`src/directory/provenance.json` records original instruction range hashes, file
positions and retained REA evidence IDs. All recovery refers to PCPlus 2.01 EXE
SHA256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Saved exports are under ignored `analysis/pcplus-overlay-anchored-{04,05,06,08}`
and`analysis/pcplus-main`; original startup data mapping begins at file 153936.
Only hashes, the inferred schema and newly authored code are public inputs.

The maintained DOS adapter and startup browser now select supported records,
apply serial/profile fields and connect in MODEM or DIRECT mode. Remaining work
includes full directory editing, automatic redial cycles, date/count updates,
complete protocol/terminal coverage, note/keyboard editors, META and ASPECT
script/password bindings. Other PCPlus versions or DTP layouts require independent
identification and proof. No private directory was modified.
