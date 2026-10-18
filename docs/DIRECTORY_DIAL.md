# Directory target expansion and selected-entry effects

Original overlay5 `ec61..edf1` quickdial expansion (400 bytes), its resident
uppercase/length/integer/append helpers (194 bytes), and the selected serial
apply fragment `e6ea..e72c` (66 bytes) are recovered with exact flat hashes.
A separate maintained, DOS-callable pure helper provides bounded literal or
legacy number expansion without touching records, ports or files.

This recovery uses PCPlus2.01 original SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`, retained REA
exports and synthetic records/codes only. No user directory, password, PRM or
contact data was read. A directory reader/browser or live connection engine is
not implemented by this module; the normal build requires no original artifact.

## Stable maintained C ABI

Only `reconstruction/directory_dial/bounded.asm` is required by a live caller:

```c
unsigned __cdecl directory_number_expand(
    const unsigned char *number21, const unsigned char *codes250,
    unsigned char *destination64, unsigned mode);
```

Its OMF export is `_directory_number_expand` (also an undecorated alias), using
near C arguments, caller cleanup8. Return **full AX**:0 success,1 invalid/wrapping
extent,2 no source NUL within21 bytes,3 no NUL in a25-byte code slot,4 output too
long/insufficient capacity,5 invalid mode. BP/BX/CX/DX/SI/DI are preserved; DS=SS
and clear DF are required. Source/output buffers must be caller-owned DS memory.

Mode0 copies the number literally, preserving case and bytes. It does not read
or validate the unused codes pointer. Mode1 first validates **all ten**25-byte
code slots, then uppercases ASCII a..z in number bytes and substitutes A..J with
the corresponding code. Code content is copied as stored, without uppercasing
or recursive substitution. Other number bytes remain literal. No whitespace
trimming, caret expansion, modem prefix/suffix or extra CR is added here.

The source must terminate within21 bytes (maximum20 content bytes); legacy
output must fit the original60-byte content limit plus NUL. The64-byte output
buffer has spare bytes. An overlong expansion is **rejected**, rather than
silently truncated as in the original. A scratch buffer holds the complete
validated result before writing any destination byte. Errors leave destination
unchanged; success writes only result plus NUL, preserving the remaining tail.
Inputs/header are never changed. Overlapping caller input/output is safe because
the result is built before commit, but caller buffers must not alias the
callee's own stack frame and must not change concurrently.

The general near C helper `directory_dial_number_bounded(source,source_capacity,
codes,destination,destination_capacity,mode)` additionally exposes source/dest
capacities. Source capacity is1..21. It returns CF0/AX output length or CF1/AX
error1..5; caller removes12 bytes. The C convenience wrapper converts success
to full AX0. Legacy validates the complete250-byte header even when the number
references only one code; this is an explicit bounded import policy.

Modern hostnames should use literal mode. Original legacy rules do more than
change letter case: with empty codes, `bbs.example` becomes `S.XMPL`, because
its B/E/A characters are code references and disappear. Code insertion may also
introduce modem caret commands. Charset and final modem-command validation belong
to the live caller before UART effects. The existing explicit `/D` literal target
syntax need not inherit quickdial command grammar.

## Original quickdial grammar and side effects

`directory_dial_expand_original(selection_slot,destination)` is near C, caller
cleanup4; selection slots are0..14. It clears destination immediately and uses
a seven-byte slot at DS`70b4 + slot*7`, including an active/done flag at+6. It
assumes that token and all referenced strings terminate correctly. Its destination
has no capacity argument and must hold at least61 bytes. BP/SI/DI are saved;
ES/AX/BX/CX/DX/flags are scratch through runtime helpers.

Observed order is:

1. Uppercase ASCII a..z in the quickdial token **in place**.
2. Expand leading A..J into the result from header DS`e484 + (letter-'A')*25`.
3. Parse the remaining token with the original integer converter. Accept its
   signed16-bit result0..200; otherwise return201. Nonzero loads that selected
   record through overlay4 `ddb6`. Zero retains the current selected record.
4. Uppercase the selected record's number DS`e669` (record+19h) **in place**.
   Expand A..J anywhere in it; copy other bytes literally.
5. Skip decimal digits from the token's numeric position, then expand following
   A..J as suffix codes. Stop on other punctuation/letters. Return entry0..200.

Each append is bounded by remaining space up to60 content bytes. Excess content
is silently truncated. Code strings are not themselves recursively expanded or
uppercased. Header indexing uses the arithmetic `letter*25 + de2b`, equivalent
to the A-based formula above. Signed character tests mean high-bit number bytes
are ordinary bytes after ASCII-only uppercasing, rather than code letters.

These are mutations of quick-token/selected-record working memory, not a claim
that ec61 writes the directory file. The successful-call caller reloads a selected
record before its statistics write.

The integer converter skips spaces/tabs, supports +/- and ignores nonnumeric
suffixes. The caller tests only its low16 bits. Therefore token `65537` selects
entry1 and `65536` selects current-entry0; malformed nonnumeric text can also
become0. Later digit/suffix scanning does not mirror atoi's whitespace/sign
handling. These quirks are preserved by recovered code, not offered as a modern
safe selector. The maintained helper covers **number expansion only**; a future
quickdial UI needs separate strict token/range validation.

Original stdlib helpers have no bounds contract. The append helper at9852 is
used by ec61 only with positive remaining lengths, after checking current output
length. The bounded live API does not call these unsafe string helpers.

## Serial settings, MODEM/DIRECT and successful-call bindings

The selected record is DS`e650`,114 bytes. The exact apply span is internal to
overlay5 e5e3; it has no original standalone prologue/return. `apply_fragment.asm`
adds a documented RET only in OMF mode, after the original66 bytes. Its actual
port-close/reconfigure imports remain unresolved in the standalone diagnostic.

| Selected record | Original effect in e6ea..e729 |
| --- | --- |
| +68h port override |0 retains current port DS1b84. Otherwise sign-extend byte, compare override-1 to current; if changed call adba before setting new zero-based port. |
| +2eh baud word | Always writes DS1b86. |
| +30h parity byte | Sign-extends and writes DS1b88. |
| +32h stop-bit byte | Sign-extends and writes DS1b8a. |
| +31h data-bit byte | Sign-extends and writes DS1b8c. |
| +33h duplex byte | Sign-extends and writes DS1d1a local-echo/full-half setting. |
| after all fields | Calls serial reconfiguration03a7 unconditionally. |

DEFAULT applies to the port only; it does not retain the prior baud or line
format. Raw fields are not validated here. For example port overrideff becomes
fffe after sign extension/decrement, an invalid selector. Maintained callers
must validate supported ports/rates/enums and all unsupported bindings before
hardware changes. The controlled replay observes pre-close and post-configure
state; it does not claim physical port effects or a complete rollback policy.

At `e7de..e7f2`, mode byte record+4ah zero calls modem dial-attempt e8ad. Any
nonzero byte bypasses it and supplies connected result1. A maintained importer
should validate0 MODEM/1 DIRECT rather than treating unknown bytes as supported
DIRECT. DIRECT still applies all serial fields first, can have an empty target,
and still follows successful-entry binding behavior afterward.

On successful selected entry, overlay4 `d943..d96c` reloads the selected record,
increments its completed-call count, stores current date, and writes its partial
persistent stats. `d96d..da04` then performs these handoffs:

| Record field | Postconnection action |
| --- | --- |
| +49h terminal | Sign-extends to DS1d18 before terminal reset20a4 later. |
| +48h protocol | Sign-extends to DS3996. |
| +5fh META | If first byte is neither NUL nor space, copy to DS3262. Later terminal-key loader appends `.KBD`; this is not proof of an ordinary script. |
| +56h keyboard | If nonblank by the same test, copy to DS21d8, append `.KEY`, uppercase filename, set return-bit2. |
| +34h script | If nonblank, set selected-entry identifier DS4afe, copy name to DSce6a, set return-bit1 for the caller's script handoff. |

Blank means only first byte NUL or ASCII space. A leading tab is not blank; text
after a leading space is ignored by these tests. META copy alone sets no result
bit. Examined handoff code does not establish automatic password transmission;
no password behavior is invented by this recovery. Runtime unsupported terminal,
protocol, keyboard, META or ASPECT/script bindings must be surfaced explicitly,
rather than silently ignored. Notes and other directory UI actions remain
separate consumers. See DIRECTORY.md for complete disk layout.

## Build, source-only tests and optional original comparison

```sh
./tools/dev --command python3 standalone/build_directory_dial.py
./tools/dev --command python3 standalone/check_directory_dial.py
./tools/dev --command python3 standalone/test_directory_dial_dos.py
# Optional explicit original; no directory/PRM file is opened:
./tools/dev --command python3 standalone/check_directory_dial_original.py \
  analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

The independent build checks660 exact bytes against tracked hashes. It links
`DIRDIAL.EXE` with original ec61, actual recovered string helpers, maintained
bounded API and an explicitly synthetic in-memory selected-record reader.
The field-apply fragment is assembled unlinked, not connected to fake live UART
services. The raw OMF quickdial calls the original integer body directly instead
of retaining its resident jump stub.

Four CPU groups pass across525 cases:512 randomized literal/legacy expansions,
four nonrecursive/case/60-byte boundaries, eight malformed/extent/atomicity cases,
and actual original prefix+selected-number+suffix behavior with in-place
uppercasing. Tests use the requested full-AX C ABI and check preserved registers,
caller stack and output guards/tail bytes. Actual DOSBox-X self-checks exercise
both original quickdial and maintained literal/legacy output.

The optional actual-original replay passes127 cases:115 quickdial tokens and
synthetic code/record combinations, four default/same/different/malformed port
applications, four MODEM/DIRECT control outcomes, and four postconnection binding
cases. Original uppercase/atoi/strlen/strncat/strcpy/strcat instructions execute.
Selected-record loading, port services and two UI boundaries are explicit models;
the DIRECT block's modem call is a modeled return boundary. It confirms the
field effects/grammar, not a complete live directory/UI or physical modem.
Reports remain ignored under `build/directory-dial/` and `build/directory-dial-dos/`.

## Evidence and remaining boundaries

Saved REA evidence/context was reused; no duplicate tool setup or original
customized data was needed. `provenance.json` records every original range,
source-file offset/hash and source identity. Principal Evidence IDs:

| Code | REA Evidence |
| --- | --- |
| Overlay5 ec61 | `ev_31c74a3a2ee99b7b7f9df548c1d0c0c0365ef6e32fdade436978005929fd3b6b` |
| Overlay5 e5e3 field/dial consumer | `ev_39a79d6b6cc8461be5670ec966b27debcb038be51912017ad7373672722d08c6` |
| Overlay4 d4d0 postconnect consumer | `ev_f036ab3465803d9a80443a35288a0b90a521ce636c225f4f110b7c49cf621ac4` |
| Resident ASCII uppercase9128 | `ev_af474791eca9acf2db71969ff3c292523e8ed769a7f02f274f430beb977ddc2c` |

Resident9852 lacks a retained Ghidra function at its entry; its53-byte actual
instruction span was independently decoded with pinned Nix ndisasm and checked
against the original hash, then exercised by both source-built and original
replays. The remaining resident helper Evidence IDs are included in provenance.

Live directory reading/selection/browser, stats persistence, terminal/protocol
support policy, keyboard/META/ASPECT loading and full original UI/port adapters
are separate integration work. This scope does not edit the terminal, shared
Makefile or live binary. Modern literal mode and strict legacy-overflow errors
are explicit maintained behavior alongside, rather than hidden changes to,
the original flat baseline.

## Live integration

The maintained helper is now linked to the [live directory reader/browser and
connection path](DIRECTORY_LIVE.md). Literal mode is its explicit network default;
legacy mode is available through `/C:LEGACY`. The original full quickdial token
routine and port-apply fragment remain separate recovered code, with their
original service imports and scope boundaries preserved.
