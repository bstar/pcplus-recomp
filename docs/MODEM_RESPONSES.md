# Modem response matcher and dial-attempt decisions

Actual PCPlus2.01 resident `4a1d..4aa7` is now recovered as a138-byte source
module with exact flat equality and a relocatable OMF export. Overlay5
`e8ad..eaed`, the576-byte dial-attempt function that consumes its result, is also
recovered exactly and assembled as an **unlinked** OMF object with explicit
imports. The standalone DOS executable links the real matcher, a maintained
bounded one-byte input adapter, validated state and a pure decision classifier.
It does not claim the full attempt loop or modem subsystem works in DOS yet.
No private PRM, dialing/contact file or modem connection is used by these tests.

## Exact matching behavior

Original `modem_response_match_original(init_flag)` uses near C arguments; the
caller removes two stack bytes. Nonzero initializes eleven cursor words to the
start of their respective16-byte response slots and returns `ffff`. Zero polls
available input, returning index0..10 on completion or `ffff` when no response
completes before input availability reaches zero. BP/SI/DI are preserved;
AX/BX/CX/DX and flags are scratch. DS=SS and clear DF are required.

The function owns no timer. Its original UART-read boundary is `aad9(1)`, called
only after DS8e20 indicates input is available. It consumes bytes through that
boundary and maintains partial-match cursors between calls. Resident UART code
also applies its selected receive mask; a maintained byte-feed caller must
supply the byte after any desired serial masking.

For each byte it walks response slots in ascending index order:

- Compare bytes exactly, without case folding or CR/LF/line framing. Responses
  can match within noise, before a trailing CR/LF or without any line ending.
- Empty slots are ignored. A successful byte advances that slot's cursor; a
  following NUL completes the response immediately.
- The first slot completing on a byte wins. Later slots are not processed for
  that same byte. Shorter overlapping labels can therefore win before a longer
  response is complete, independently of which baud would be desirable.
- On mismatch, retain one matched prefix byte only when the new byte equals the
  slot's first byte; otherwise reset to its start. This is not a general longest
  prefix/suffix algorithm. Pattern `ABABAC` against `ABABABAC` fails even though
  a substring search would find a match.
- A completed slot remains pointing to its NUL terminator and is ignored on
  further polls until initialization resets cursors. The original dial attempt
  initializes before sending a new dial command.

The embedded generic CONNECT slot can finish before configured longer CONNECT
rate labels. The recovered behavior is preserved and tested, rather than
silently changed to longest-match or line-based matching. A modern modem result
policy should be a separate maintained mode with explicit tests.

## State ownership and bounded API

| Original DS | Relocatable symbol / storage |
| --- | --- |
| `1c48..1cf7` | `modem_response_slots`, eleven16-byte NUL-terminated byte buffers; these are already expanded response bytes in PRM, not command caret text. |
| `8f58..8f6d` | `modem_response_cursors`, eleven near offsets into their corresponding slots; live parser state, outside PRM. |
| `8e20` | `modem_response_available`; original UART RX count. The bounded pure module owns a private one-byte availability word instead. |
| `aad9` | `modem_response_read_byte`; original timed UART read. The maintained adapter consumes exactly its owned one-byte input and clears availability. |

`state.asm` owns the diagnostic/pure-helper singleton buffers. Copy validated
response bytes into those buffers, then call `modem_responses_reset_bounded()`.
It validates all slots before resetting cursors; CF0/AX0 is success. If any slot
lacks a terminator within16 bytes it returns CF1/AX1 without mutating matcher
state. Empty slots are valid.

`modem_responses_feed_bounded(uint16 byte)` takes a near C argument; caller
removes two bytes. It validates input0..255, all slot terminators and all cursor
pointers before changing state. Each cursor must lie between its own slot start
and first terminator, inclusive. CF1/AX1 means unterminated slot, AX2 invalid
cursor, AX3 input outside byte range. Invalid calls preserve all matcher/input
state. Valid calls return CF0/AX0..10 for a completed response or CF0/AXffff for
none, after consuming exactly one byte through the recovered core. No callback
is faked and no host input/clock/UART routine is needed. Both bounded functions
preserve BP/BX/CX/DX/SI/DI; ordinary flags are scratch except reported CF.

After editing response text, reset cursors before feeding again. Buffer edits
must not race a matcher call. The singleton state follows the original
foreground-consumer model; it is not a reentrant or concurrent API.

The raw matcher retains original unsafe behavior for malformed buffers/cursors.
The bounded wrapper deliberately adds validation without changing that flat
baseline. Its one-byte adapter is **not** a replacement for a real UART driver.
To link the full original attempt, bind its matcher availability/read services
to the actual UART queue through a correct near-ABI adapter, rather than linking
the standalone one-byte source as though it were live serial input.

## Dial-attempt caller and outcome mapping

Recovered overlay5 `modem_dial_attempt_original(number_pointer)` is near C,
caller removes two argument bytes. It temporarily disables local echo DS1d1a,
raises calibrated command pacing DS1d68 to at least30 via signed comparison,
initializes response cursors, flushes RX, sends configured prefix + supplied
number + suffix, then restores echo and pacing. It loops through elapsed-time,
keyboard and response handling. Its UI/command/clock/UART imports remain explicit
in `attempt.asm`; the diagnostic does not replace them with no-op services.

| Condition / response | Original attempt result and action |
| --- | --- |
| Response index0..6 | Connected: AX1. If DS1b92 is nonzero and baud index differs, write DS1b86=index and call baud setter `ac27` with the corresponding32-bit value. |
| Response index7..10 | Failure: AX0; these are configured result labels, not elapsed-time expiration. |
| No completed response | Continue waiting unless time/key action terminates the attempt. |
| Elapsed count greater than configured DS1b8e limit | Failure AX0. Elapsed increments when DOS seconds field changes, not by monotonic tick subtraction. |
| Keyboard AX001b (Escape) | Calls abort helper overlay5 ec0e, returns AX001b. |
| Keyboard AX0020 (Space) | Returns AX2, the outer dialing loop's action code. |
| Keyboard AX5300 (Delete) | Returns AX3, another outer-loop action code. |
| Keyboard AX4f00 (End) | Opens wait-time editor; accepted input can update DS1b8e, then continues waiting. It is not the AX3 return path. |

Other keys are ignored by this function. A complete definition of the outer
loop's action2/3 policy remains separate from this caller recovery. The timer
uses signed comparisons, and its change-count method can miss elapsed seconds
when execution is stalled; no modern timeout policy is silently substituted.

Successful response indices map `0=300,1=1200,2=2400,3=4800,4=9600,5=19200,
6=38400` through the baud table at DS3270. The matcher has no additional rate
slots for57600/115200, even though serial configuration supports those baud
indices. The baseline text labels for failure slots are configurable; tests
use synthetic labels rather than original/user contact data.

The maintained `modem_response_classify(index,current_baud_index,autobaud)`
returns CF0/AXffff pending, AX0 failure or AX1 connected; DX is effective baud
index and BX is0/1 indicating whether baud must change. It performs no baud or
UART write. It validates current baud0..8, Boolean autobaud0/1 and response
index0..10/ffff; invalid inputs return CF1/AX3,2,1 respectively. Caller removes
six stack bytes; BP is preserved, AX/BX/DX carry results. This is a pure,
maintained extraction of the proved action mapping, not an original routine.

## Source-only validation and optional original replay

```sh
./tools/dev --command python3 standalone/build_modem_responses.py
./tools/dev --command python3 standalone/check_modem_responses.py
./tools/dev --command python3 standalone/test_modem_responses_dos.py
# Optional explicit original analysis, never reads a PRM:
./tools/dev --command python3 standalone/check_modem_responses_original.py \
  analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

The independent build checks flat hashes for138 matcher bytes and576 attempt
bytes against tracked provenance. It links `MODEMRSP.EXE` from source alone and
assembles `attempt-unlinked.obj` without linking it into the diagnostic. No
original executable, REA export or proprietary data is read by this build.

Five CPU groups pass: seven focused matching semantics,12,800 randomized
binary-byte/state comparisons across all eleven slots, nine partial/reset
checks, four unchanged-state validation failures, and220 classification/range
cases. Actual relocated OMF instructions execute through the bounded adapter;
return flags, cursor state, ABI preservation and bounded consumption are checked.
The actual DOSBox-X self-check exercises reset, partial input, successful
completion and invalid-cursor rejection using synthetic OK text.

The optional analyst replay executes **actual original overlay5 e8ad and
resident4a1d** for27 cases: all eleven response slots with autobaud off/on,
timeout, Escape, Space, Delete and wait-editor path. It proves result codes,
selected baud writes/calls and echo/pacing restoration. UI drawing/editing,
command transmission, clock, keyboard and UART-read boundaries are explicitly
modeled. A synthetic response is made available after sending the three dial
command pieces; no original PRM/initialized DS data is loaded. The wait editor
case models a declined edit. This is a controlled original-code replay, not an
end-to-end modem connection or a source-built full dial attempt. Reports remain
ignored under `build/modem-responses/`.

## Provenance and integration gaps

Original SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Saved REA assembly was reused; a live REA query reaffirmed matcher evidence
`ev_eaf6bfcee78dea8d82da1fec58a76a1138dcf75801e5e52cc3063094472bfc9e`.
Overlay5 attempt assembly evidence is
`ev_5023f79a668e8360dce2412988c12d76db925a146c121f7b7531c9555fabec38`.
The hashes/context/ranges are retained in
`reconstruction/modem_responses/provenance.json`. Static Ghidra coordinates are
linear addresses with load segment1000; a code offset alone does not identify
an overlay context.

The bounded byte feed and classifier are ready for a maintained DOS state
engine. Remaining integration must provide real UART input/output, bounded
command sending, clock/cancel deadlines, modem DTR/hang-up behavior and real
caller UI/resources. Original attempt UI coordinates/resource pointers are
named by their original addresses when their meaning remains unresolved.
Original seconds-change timeout behavior and response overlap quirks need
explicit modern policy choices. No terminal build/Makefile or live binary was
changed by this recovery.

## Live integration

The maintained [connection controller](CONNECTION.md) now passes bytes received
from the actual UART to the bounded byte-feed API and applies the classifier.
The one-byte adapter remains an owned matcher boundary, not a fake replacement
for a serial routine. Physical command writes use the bounded real UART API.
The original full-attempt OMF object remains unlinked with explicit dependencies;
its directory/UI/retry behavior is not implied by this integration.
