# Modem settings and command expansion

The existing lossless PCPlus2.01 PRM codec now maps six modem command buffers,
eleven response slots and selected dialing/control settings from original
instructions. It can read/edit these fields without normalizing the opaque
remainder. This is a tested host decoder and pure command-event plan, not the
full startup initializer or complete modem configuration UI. The maintained
DOS controller now imports the proved subset and performs explicit-target
dialing; see [CONNECTION.md](CONNECTION.md). No customized PRM/dialing files were read.

The source identity is the verified214,016-byte executable, SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
PRM bytes map DS`1b84..2073`; original initialized DS data is overlay32 at file
offset`25950`. See CONFIGURATION.md for full-image I/O provenance. Values below
are derived from code and field-edit capacities, rather than guessed from
existing user settings. All word values are unsigned little-endian storage;
several original comparisons interpret them as signed.

The DOS modem plan also appends the raw BREAK delay word at01A4h. Its startup
calibration and maintained conservative timer policy are documented in
[LIVE_BREAK.md](LIVE_BREAK.md); the historical command-character delay remains
a distinct setting.

## Proved fields

| PRM offset | Original DS | Storage / meaning and proof |
| --- | --- | --- |
| `000a` | `1b8e` | Word: dial connection timeout in seconds. Overlay5 e8ad increments elapsed count when resident3323's DOS seconds value changes and compares this limit; UI labels say SECS. |
| `000c` | `1b90` | Word: pause between redial attempts, seconds. Overlay5 eb89 uses the same seconds-change loop; dialing screen labels confirm SECS. |
| `000e` | `1b92` | Word: adjust baud from recognized response index. Overlay5 eabf writes serial baud index and calls baud setter when nonzero. |
| `0010` | `1b94` | Word: drop/reassert DTR during dial abort. Overlay5 ec0e conditionally calls82a8 with operation10, delay6bb6, then operation11. Physical modem behavior is not established by this field map. |
| `0012` | `1b96` | Byte: optional dial-abort transmit character. Overlay5 ec0e sends it when nonzero. Following byte0013 remains opaque. |
| `0014` | `1b98` | Word: permit startup modem initialization with carrier already asserted. Overlay3 d99a skips initialization when carrier is present and this flag is zero. |
| `0016` | `1b9a` | Word: selected-number dialing-cycle limit. Overlay5 e5e3 increments cycle count after scanning15 selection slots, then compares this limit. It is not a per-byte retry count. |
| `0018` | `1b9c` | Initialization command:47-byte C buffer, maximum46 content bytes (overlay19 ef8a). |
| `0047` | `1bcb` | Dial prefix:25-byte C buffer, maximum24 content bytes (ef5e). |
| `0060` | `1be4` | Dial suffix:25-byte C buffer, maximum24 content bytes (ef6a). |
| `0079` | `1bfd` | Hang-up command:25-byte C buffer, maximum24 content bytes (ef7e and resident0445). |
| `0092` | `1c16` | Answer-on command:25-byte C buffer, maximum24 content bytes (ef28). Command content/name corroborates role; full Host enable path remains to recover. |
| `00ab` | `1c2f` | Answer-off command:25-byte C buffer, maximum24 content bytes (ef1c; overlay10 e729 sends it when leaving Host mode without carrier). |
| `00c4..0173` | `1c48..1cf7` | Eleven16-byte response slots; maximum15 content bytes each. Overlay19 eee2 indexes by16 and edits15 bytes; resident4a1d builds11 matching cursors. |
| `0198` | `1d1c` | Word: software flow enable; overlay19 ec1a copies it to live UART DS3354. |
| `019a` | `1d1e` | Word: hardware flow enable; overlay19 ea2c copies it to live UART DS3356. |
| `01e2` | `1d66` | Byte: command pause marker, tested before sentinel/ordinary transmission in48cc. Next byte remains opaque. |
| `01e4` | `1d68` | Word: calibrated per-character delay argument to6b72. Actual time unit remains unproved; the API deliberately exposes `command_character_delay_units`. |

Response slots0..6 are successful connect/baud selectors for300 through38400.
Slots7..10 stop the dialing attempt as failure. The embedded baseline labels
are generic CONNECT, six rate-specific CONNECT forms, NO CARRIER, BUSY, VOICE
and TIMEOUT. Labels are configurable and are not a format signature. No
57600/115200 response slot is present in this eleven-slot loop, despite the
serial baud selector supporting those rates. Exact consequences for a modern
modem returning those speeds need a deliberate policy and tests.

Command buffers store caret notation. Response buffers store **already expanded
bytes**: the response editor copies the text into a temporary buffer, then
calls resident4934 into its PRM slot. The codec exposes both as raw bounded
bytes and does not accidentally expand a response twice. A command-buffer
setter checks storage bounds/NUL only; expansion validation is a separate API.

Original receive codeaa65 treats each flow word as nonzero for its resume path;
transmit codeab0b gates CTS only when the hardware word equals1. A maintained
importer must therefore validate0/1, rather than treating arbitrary nonzero
words as a consistent Boolean. Both can be independently selected in storage;
the recovered receive resume path gives software flow precedence when both
are enabled. A live mixed-flow policy requires dedicated tests.

## Actual command semantics and timing

Resident4934 expands a NUL-terminated source to destination. For valid input:

- `^@` emits byteff, a sentinel used by the sender to transmit NUL.
- Three carets `^^^` emit one literal caret. Two carets `^^` emit1e.
- Every other `^x` emits `x & 1f`, including lowercase controls. `^?` is1f,
  not DEL. Ordinary bytes are copied unchanged.

The maintained bounded decoder rejects a trailing caret, embedded raw NUL and
input longer than128 bytes. Original4934 has no length argument, and a trailing
caret can advance past its source terminator; this undefined memory access is
not reproduced. Original48cc uses a130-byte stack expansion buffer. If an
escape such as `^` followed by backtick produces zero, the sender stops at that
expanded zero because it traverses a C string. This differs from `^@`'s ff
sentinel. Rawff is also interpreted as a NUL sentinel by the sender.

Resident48cc checks the expanded byte against DS1d66 first. A match calls6b98
with9. That helper increments its argument, then waits for **ten changes of the
BIOS tick low word** at0040:006c. This is approximately half a second on the
standard PC BIOS clock; exact wall time depends on tick phase/environment.
It is not nine seconds. Sentinelff transmits NUL without ordinary pacing.
Other bytes optionally echo locally through0610, transmit throughab0b, then
call calibrated delay6b72 with DS1d68. The pure event planner describes these
transmit/delay operations without performing I/O; local echo is explicitly
outside that plan.

Original dialing e8ad temporarily disables local echo and raises pacing to at
least30 using a signed comparison while sending prefix + supplied number +
suffix, then restores both settings. Resident hang-up0445 similarly raises
pacing around the configured hang-up string. Original initialization at3a25
sends DS1b9c with echo disabled and minimum30 pacing, then restores both.
The saved REA database lacks a procedure at3a25; its exact original48-byte
instruction span3a25..3a55 was independently decoded using pinned Nix ndisasm.
This absence does not justify treating the routine as missing application code.

Resident4a1d matches response bytes incrementally and case-sensitively. Empty
slots are skipped. It returns as soon as a slot reaches its NUL terminator;
there is no requirement to wait for a whole line or the longest matching
response. On mismatch, it preserves at most a matching first byte rather than
a general prefix-function fallback. Overlapping response labels and modern
modem result variants require explicit compatibility tests before integrating
this legacy parser. No complete response-parser replacement is claimed here.

## API and verification

`LegacyPrm201.modem_bytes(name)` / `with_modem_bytes(name, bytes)` cover the six
command names in `MODEM_COMMAND_FIELDS`. `modem_bytes('response', index)` and
`with_modem_bytes('response', bytes, index)` cover slots0..10. `byte`/`with_byte`
cover the pause/abort characters. Existing `word`/`with_word` expose the proved
word fields above. Mutations change only value bytes plus their terminating
NUL; old tail bytes and unknown neighbors remain exact. Unterminated fields
raise on access while the complete opaque image remains round-trippable.
`expand_modem_command` and `modem_command_events` are pure source-owned helpers.

```sh
./tools/dev --command python3 -m unittest discover -s src/config
# Optional analyst replay, explicitly needs local original; no PRM is read:
./tools/dev --command python3 src/config/check_original_modem.py \
  analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

Eleven host unit tests pass, including six new modem test groups: field limits
and opaque-tail preservation, all response slots, malformed field handling,
byte/word offsets, caret controls and sender priority/delay behavior. The
optional replay executes actual resident4934/48cc instructions with synthetic
inputs: **516 expansion cases and64 sender plans** pass against the maintained
implementation. Transmit, calibrated delay and BIOS delay are declared modeled
boundaries; this is not physical timing or an end-to-end dialing test. Its
JSON report is ignored under `build/modem-config/` and contains no original
configuration data.

## Retained REA provenance and remaining work

Saved assembly evidence was reused. A live REA request initially reported no
active target, so the explicitly authorized original was opened; querying4934
reaffirmed the same evidence. No global tool/configuration changes were made.

| Code | Assembly Evidence |
| --- | --- |
| Resident4934 expansion | `ev_059b2b6f9c5a4c8603920897ea8ceb541feea65be2c5787a294ab008abf9155d` |
| Resident48cc sender | `ev_3a29c9753cf6188658686eb46944e813fddeb172758c9bded7dc265f9aeac907` |
| Resident4a1d response matcher | `ev_eaf6bfcee78dea8d82da1fec58a76a1138dcf75801e5e52cc3063094472bfc9e` |
| Overlay19 eee2 response editor | `ev_5caa91b5ccd91837938ebfd9452785908d7d4af5bc8485d5466526272907842a` |
| Overlay19 e72a bounded copy | `ev_9124e8d28403cd4424ab7f766d58907f5be2fa03c2e51baf218a919cd3937dd5` |
| Overlay5 e8ad dial attempt | `ev_5023f79a668e8360dce2412988c12d76db925a146c121f7b7531c9555fabec38` |
| Overlay5 eb89 redial pause | `ev_32a78d43d8e3c9b0aceb52fe72152714f3c53dcd03e49982095faea5a03b33b4` |
| Overlay5 e5e3 selection cycles | `ev_39a79d6b6cc8461be5670ec966b27debcb038be51912017ad7373672722d08c6` |
| Overlay5 ec0e abort | `ev_94814e7f388db888140f2079657a5ff4cd2adff9367e316f5fa3c90116dc7d3e` |
| Overlay19 ec1a flow config | `ev_2f5d4a1da59a62310d80299b8a945d6ceec054b1ab81bd16afd5215d6304a2f0` |
| Overlay19 ea2c flow config | `ev_06cc591e0b2deda30a35dbec41a6dbdb512b79c45297658c90e14fb8933acfb6` |
| Resident6b98 BIOS delay | `ev_cc5df7fd3b4baa1350abfad9245198f09d55989c263134af069ea519ff7a51f9` |
| Resident6b72 calibrated delay | `ev_a30bfa2cee5690318dc8252472fd4570367e365219605a4b4a1e2253170377fc` |

The bounded live sender and explicit-target connection controller are now linked
to the actual UART and covered by DOS and real local BBS workflows. The original
blocking sender/delay routines are separately recovered and tested. See
[CONNECTION.md](CONNECTION.md) and [MODEM_SEND.md](MODEM_SEND.md). Automatic dial
cycles, complete modem UI/database, modern result policies, calibrated pacing
units and physical mixed-flow behavior remain unresolved. Public tests use only
synthetic PRMs, never an installed/private modem configuration.

## Source-built DOS expansion module

`reconstruction/modem_commands/expand.asm` contains the actual87-byte
resident4934 decoder with an exact flat baseline hash in `provenance.json`.
The OMF export `modem_expand_original` takes near C arguments
`(source_offset, destination_offset)`; the caller removes four stack bytes.
DS must equal SS for the small-model stack convention, and DF must be clear.
The original routine preserves BP/SI/DI but provides no bounds protection.

`modem_expand_bounded` is an explicitly maintained wrapper around that original
code. Its near C arguments are `(source, destination, source_capacity,
destination_capacity)`, all unsigned16-bit values; caller removes eight stack
bytes. Source capacity must be1..129. Both declared extents must remain inside
the16-bit DS offset range without arithmetic wrap. The wrapper requires a NUL
within source capacity, rejects an unpaired trailing caret, verifies destination
capacity for all expanded bytes plus its terminator, and rejects overlapping
used source/destination ranges. It scans/validates the whole source before
calling the recovered decoder. Rejected calls leave the destination unchanged.

Success returns CF0 and AX=expanded byte count excluding the final NUL; an
embedded expanded zero still contributes to that count. Error returns CF1 and
AX=1 invalid extent,2 missing terminator,3 unpaired trailing caret,4 insufficient
destination capacity,5 overlapping buffers. BP/BX/CX/DX/SI/DI are preserved.
The wrapper performs no DOS, clock or UART calls and does not change the raw
recovered routine's flat baseline behavior.

```sh
./tools/dev --command python3 standalone/build_modem_commands.py
./tools/dev --command python3 standalone/check_modem_commands.py
./tools/dev --command python3 standalone/test_modem_commands_dos.py
```

The independent build reads only maintained source/provenance, assembles the
flat baseline and checks its87-byte hash, then links `MODEMCMD.EXE` without an
original executable. Four CPU groups pass:516 recovered-core expansion cases,
eight validation-error cases with unchanged destination, six exact-capacity
edges and four overlaps. They check return flags, length, guards, registers and
caller stack behavior through the actual relocated OMF code. The real DOSBox-X
executable independently checks valid control/NUL/literal-caret expansion,
trailing-caret rejection, destination-capacity rejection and guard preservation.
This diagnostic is a concrete DOS-callable decoder milestone; no live sender
wait loop or complete dialing subsystem is implied.
