# Directory successful-call accounting and editor evidence

Original PCPlus2.01 accounting is recovered as220 exact bytes: overlay4
`d943..d96d` successful-call fragment42, `dd28..dd94` writer108, resident
`36d4..36fc` date formatter40 and `776e..778c` DOS date helper30. Tracked
`reconstruction/directory_accounting/provenance.json` binds each range to the
verified original SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`, file
offset, flat digest and retained REA evidence. No private directory or PRM was
read. Normal builds consume authored source only.

## Maintained pure DOS API

Only `reconstruction/directory_accounting/patch.asm` is needed by an application:

```c
unsigned __cdecl directory_accounting_patch(
    const unsigned char *source114, unsigned char *destination114,
    unsigned year, unsigned month, unsigned day, unsigned count_delta);
```

OMF exports `_directory_accounting_patch` and an undecorated alias. Near C
arguments, caller removes12 bytes, DS=SS. Full AX returns0 success,1 invalid
record extent/alias with the active callee frame,2 invalid date. BP/BX/CX/DX/SI/DI
and ES are preserved; DF is cleared. Both buffers must provide114 bytes in DS,
without wrapping the64K segment. The helper stages the complete source record
before any output write, so identical or overlapping input/output works. Buffers
must not alias this callee's scratch/register/argument frame; those extents are
rejected. Callers own buffers and prevent concurrent mutation.

Dates use full year1980..2099, month1..12 and Gregorian day validation, including
February29 in2000. The year bound is this maintained DOS-facing API's explicit
policy, not a claim about every DOS replacement's date range. The helper writes
exactly `MM/DD/YY` plus NUL to record61..69, with `YY=year%100`, and adds
`count_delta` modulo65536 to the little-endian word70..71. All other record bytes
are preserved. Failure leaves the complete destination untouched. There is no
file IO, clock query, UART effect, connection-state change or private data import.
The caller decides when a successful connection merits a delta and captures its
date. Persistence/transaction/close failure handling belongs to the application.

## Original call path and year2000 defect

Overlay4 `d92e` stores the dial operation's return in `[BP-6]`. At `d934`, return
`ffff` branches back to the dialing UI (`d548`); return0 skips accounting and
continues bindings at `d96d`. A nonzero selected entry reloads the original record
through `ddb6`, increments DS:e696 (record+46h), formats/copies the date to e68d
(record+3dh), stores the modified record in the far-memory cache through `dd94`,
then calls `dd28(entry,0)` to persist only date/count. Each traversal performs one
increment; this code does not increment once per received CONNECT text line.
It contains no saturation check, so ffff wraps to0000 before date copying.

Overlay5 `e7de..e7f2` supplies result1 immediately for nonzero MODEM/DIRECT mode,
whereas mode0 calls modem attempt `e8ad`. The successful branch `e849..e878`
returns selected entry SI to the overlay4 caller. Thus a selected DIRECT entry
also follows successful accounting; zero/current-entry return bypasses it.
Cancellation/nonconnection retry exits do not traverse `d943`. These control-flow
claims concern the inspected caller/attempt paths, not a new definition of every
ASPECT or external dial API. The maintained application may defer persistence
until UART shutdown while retaining pending successful-call deltas in RAM.

The original DOS helper776e executes INT21h/AH2ah and stores month,day and
**year minus1900** as three words. The formatter36d4 passes them to sprintf using
original startup string DS4729, `%2.2d/%2.2d/%2.2d`. Width/precision2 is a
minimum, not a two-digit truncation. Therefore2026 formats `10/17/126`, nine
content bytes plus NUL. Its unbounded strcpy8268 writes that terminating NUL at
record+46h, the completed-count **low byte**. The9-byte date field itself has no
NUL. Original execution with actual sprintf/strcpy confirms this, including
old count255 incrementing to256 and old count0 incrementing to1 then becoming0
after copying the date. This is an observed original defect, not speculation
from a host-side format approximation.

The maintained API deliberately fixes this by storing year modulo100, making
the date exactly9 bytes including NUL, and preserving modular count addition.
The exact flat original sources retain the defect for comparison; they are
assembled unlinked so original unsafe date/cache/FILE services are not silently
presented as safe live IO.

## Original writer and error boundary

`dd28(entry,full)` first reloads the record from cache (`ddb6`). It computes
signed16-bit `114*entry+136`, sign-extends for the seek, and selects either:

| Flag | File offset | Source | Bytes |
| --- | --- | --- | --- |
|0 |`136+114*entry+61` | DS:e68d |11 date/count bytes |
|nonzero |`136+114*entry` | DS:e650 |114 full-record bytes |

For validated entry1..200 this is the same canonical250-byte-header record
layout. The routine calls fseek853a with origin0, fwrite86ac with item size11
or114/count1, then fflush8c54. It ignores each IO return; no write-error reporting
or rollback is recovered here. Calling the writer without first updating cache
would discard changes when it reloads the record. Full streaming transactional
directory persistence must preserve this cache ordering intent while supplying
maintained size/range/write-error handling.

## Original record editor: observed constraints

Overlay6 `e3b0..f024` loads the selected record, copies114 bytes into a stack
working copy at `[BP-76h]`, and edits that copy. The retained assembly is evidence
`ev_a670247eb182152abfa485c376d9a8e080d3f2c4d36e8b37505cc8e8e5f7ea3b`.
This investigation recovers field rules and control flow, not its complete
window/input implementation.

| Field | Observed editor rule / supporting call |
| --- | --- |
| Name | input7880 limit24, record00h; `e5d8..e5e8` |
| Number | input7880 limit20, record19h; `e628..e638` |
| Baud | picker f094,9 table entries at29de; descriptor7196 |
| Parity | picker f094,5 entries NONE/ODD/EVEN/MARK/SPACE at6b32; descriptor71a2 |
| Data | entering field forces8 for parity NONE and7 otherwise (`e76b..e77b`), then numeric f024 bounds7..8; chosen nonzero-result value copied back |
| Stop | numeric f024 bounds1..2 (`e7f2..e82f`) |
| Duplex | picker FULL/HALF at6b3e; descriptor71ae |
| Port | picker DEFAULT,COM1..COM8 at6b42; descriptor71ba |
| Script | input7880 limit8; record34h |
| Transfer protocol | picker18 entries at6b54, including15 internal and3 external placeholders; descriptor71c6. `ea1f..ea29` maps visible index through WORD table714c, taking its low byte. Stored IDs in visible order:4,17,5,11,2,10,8,6,13,7,18,3,1,9,12,14,15,16. |
| Terminal | family selector at266e followed by family-specific table selection; selected value mapped back through table+1ah, not simply copied as a visible list index |
| MODEM/DIRECT | picker2 entries at6794; descriptor723e |
| Password | input7880 limit10; record4bh, no uppercase9128 call in this field path |
| KEY/META/note | input7880 limit8; records56h/5fh/69h, each followed by uppercase9128 |

No evidence here establishes a modern filename allowlist, hostname parser or
strong field validation for data imported directly from disk. The original
picker assumes prior enum values are valid indices. Maintained disk import still
requires range, termination and unsupported-binding checks before hardware.

At `ef0f..ef4f`, the editor asks `CLEAR LAST DATE AND TOTAL? (Y/N)`; yes clears
the working-copy count and copies `00/00/00`. It separately asks
`ACCEPT THIS ENTRY? (Y/N)` at ef50 and, if accepted, copies the working record to
DS:e650 and stores it in cache through dd94. The final
`SAVE ENTRY TO DISK? (Y/N)` gate calls full writer dd28 with flag1. Declining disk
save can therefore retain accepted in-memory edits. Escape/-1 exits restore
window/input state; Tab/f00 navigates to the previous field. Original UI behavior
is not a transactional editor design requirement for the maintained application.

## Password is a stored/script-accessible string

The field is plain stored bytes, maximum10 plus NUL. Overlay16 `daba` returns
pointer DS:e69b, exactly selected record+4bh. Its expression dispatcher `da83`
accepts string selectors0..21 and invokes DS[4cf8+2*selector]. Original startup
table index6 points resident overlay stub `bf67`, which transfers to overlay16
`daba`. This is a positive consumer: the script expression engine can obtain the
selected-entry password string. The human language identifier/token has not yet
been proved in this scope.

The original editor displays this field with format DS6654 `%-10.10s`, rather
than masking it. Masking in a maintained editor is an intentional privacy
improvement; this investigation never uses real password contents.

This is **not evidence of automatic password transmission**. The independently
traced successful-call binding path d96d..da05 handles terminal/protocol and
script/KEY/META but does not request this password consumer. A maintained reader
may preserve a nonblank password as opaque metadata while no script binding is
requested, without printing it or sending it automatically. Unsupported ASPECT,
script, KEY or META behavior remains an explicit application capability boundary;
preserving the password alone does not implement that script expression engine.
The negative claim is bounded to these inspected paths, not every original
application feature or keyboard macro.

Password accessor evidence:
`ev_e3f650bfffab60992c118fde98500ec7182b528142bbcef50917e23047679b87`;
dispatcher:
`ev_fd97b786da4f20c25feede9d635c6f46d8d5afc91ab5c53f51eb0c8702faf115`.

## Reproducible checks

```sh
./tools/dev --command python3 standalone/build_directory_accounting.py
./tools/dev --command python3 standalone/check_directory_accounting.py
./tools/dev --command python3 standalone/test_directory_accounting_dos.py
# Optional explicit original, synthetic memory-only records/cache/FILE:
./tools/dev --command python3 standalone/check_directory_accounting_original.py \
  analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

Source-only build verifies220 exact flat original bytes and emits the maintained
`DIRSTATS.EXE` diagnostic. Five CPU groups cover534 cases:512 random valid
records/dates/deltas, seven overlapping layouts, nine invalid dates, four
wrapping/active-stack extents, and two last-nonwrapping extents with preserved
register checks. Actual DOS checks2026 and2000 dates, counter wrap
and invalid-date atomicity. Optional original replay executes actual
date/getdate/sprintf/strcpy, success fragment and writer instructions for29 cases
covering years1980/1999/2000/2026/2099, five initial counts, cancel/current-entry
bypasses, and full/partial writes. Only the DOS date interrupt, cache and
memory-only FILE services are modeled; no private files or physical serial
devices participate. Editor field rules and script consumer have static evidence;
full interactive original editor/script runtime is not claimed.
