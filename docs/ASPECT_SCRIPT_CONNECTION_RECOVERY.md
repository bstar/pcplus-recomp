# Scripted connection control: original contracts and remaining work

This audit covers DIAL, MDIAL, REDIAL and HANGUP as one connection lifecycle.
The initial audit established original compiler observations and static native
control flow. A subsequent isolated component recovers the native bodies and
executes them with controlled service boundaries, as described below.
The capability27 screen checkpoint remains separate from this component.
F13 and the [complete reconstruction scope](FEATURES.md) remain open;
Host remains the final implementation stage.

The executable identity is PCPlus2.01,214016 bytes, SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Addresses below are original near offsets, qualified by resident/overlay
context. Retained Ghidra exports use linear addresses with load base10000h.
Overlay exports describe analysis carriers whose hashes differ from the original
executable; original-file range mappings and hashes were independently checked.
No analysis carrier or original terminal was executed. Only the original
ASPCOMP compiler ran, under owned DOS8086 with authored sources.

## Compiler grammar and emitted operands

The original ASPCOMP identity is
`5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`.
Two batches contain288 observations:68 accepted and220 rejected. Deduplication
by complete source gives280 sources:65 accepted and215 rejected. Repeated
sources agree on acceptance and every successful ASX digest. These are bounded
observations, not a claim to exhaust the original lexer or language.

| Command | Observed grammar | Opcode and operand sequence |
| --- | --- | --- |
| DIAL | `DIAL selection_string [index_destination]` | `22`, string input, presence byte0/1, optional writable string |
| MDIAL | `MDIAL number_string [display_name_string]` | `70`, string input, presence byte0/1, optional string input |
| REDIAL | `REDIAL [index_destination]` | `92`, presence byte0/1, optional writable string |
| HANGUP | `HANGUP` | `55`, no operands |

The square brackets describe optional syntax; they are not literal tokens.
Inputs accept quoted strings, ordinary string globals/locals/parameters, S0/S1
and observed read-only string builtins `$DATE`/`$D_PWORD`. The DIAL/REDIAL
destination accepts ordinary string storage and S0/S1, but rejects literals,
read-only string builtins and integer/long/float storage. MDIAL's second input
accepts literals and read-only string builtins, including an empty string. It
must not be implemented as the DIAL output parameter.

Integer constants/variables and N0 are rejected in string positions. Tested
parenthesized operands, concatenation expressions, extra operands and trailing
commas reject. Commas between operands are optional. Adjacent `,,` rejects;
comma–whitespace–comma between the two string operands accepts. Comments after
a complete statement accept. All four exact command names reject as integer
global/local/parameter declarations with original C028. This audit does not
define new identifier-prefix rules or repeat the existing string literal codec.

The ignored receipts preserve LF source hashes, actual CRLF compiler input
hashes, logs/errors, successful bytes and ASX hashes:

| Receipt | Cases | SHA256 |
| --- | --- | --- |
| `analysis/aspect-script-connection-20261119/grammar/report.json` |132,23 accepted|`9a3030ed30f97c6a22988c230021f049390347aaaf9d38da17f3ff77217dd719`|
| `analysis/aspect-script-connection-20261119/grammar-edges-v2/report.json` |156,45 accepted|`d246a4e7bcb0b3ac09af6d98bf03a1fa838a8aad55c09c043e7b33f2e76fc277`|
| `analysis/aspect-script-connection-20261119/audit-receipt.json` |Combined identities/counts|`f89e15915d02cde8077e0ab2fdb46d0659d2812c47010c29d660c96a70f81301`|

These analysis files are not application inputs or public maintained fixtures.

The later compiler binding has its own maintained
[fixture](../standalone/fixtures/aspect_connection_compiler_vectors.json) and
[checker](../standalone/check_aspect_connection_compiler.py). Its original
observations include a further32 separator probes, producing320 observations
and311 unique sources:82 accepted and229 rejected. The dedicated host and actual
DOS8086 compiler proof is `build/connection-compiler-oracles-v1-20261118/result.json`;
compiler SHA256 `ce833af2eb8bf56acb61ee89b7a5f659d668882e5530cfe65fe8c2a901e2f459`.
Grammar acceptance does not enable a runtime connection service.
The initial audit alone did not establish maintained compiler equivalence. The
subsequent311-case proof above covers those authored sources; full language
compatibility and runtime connection ownership remain open. See the
[compiler/component record](ASPECT_SCRIPT_CONNECTION_COMPILER.md).

## Native entry and shared command contract

The original215-entry dispatch inventory maps the four opcodes as follows.
The three resident wrappers were checked directly against original bytes;
their mode values are significant.

| Command | Entry | Exact wrapper bytes | Shared mode |
| --- | --- | --- | --- |
| DIAL22 |resident567E|`2bc050e81100c3`|0|
| MDIAL70 |resident5685|`b8020050e80900c3`|2|
| REDIAL92 |resident568D|`b8010050e80100c3`|1|
| HANGUP55 |residentCACB→overlay18:E759|`b8010050e8e51c5be95448` at E759|Separate hangup path|

The HANGUP bytes include relative calls/jumps in the original shared CS layout;
relocatable source must preserve their targets, not their literal displacements.
The wrapper invokes resident0445 with argument1, removes its argument, then
tail-jumps to resident2FB8 status refresh. It does not parse a command operand.

Resident5695 is105 bytes, near DS=SS, one mode WORD at BP+4, `RET2`.
It saves BP/SI/DI; ordinary scratch registers/flags follow its dependencies.
Its actual assembly is authoritative: retained decompiler output collapses
different overlay thunks into one misleading placeholder name.

1. For modes0/2, obtain the first string through CE1F→overlay16:DF04.
   Mode1 uses pointer0 and consumes no first string.
2. Push mode and first-string pointer. Read presence through CD5F→16:E0E4;
   that reader consumes the byte and returns whether it equals1.
3. If present, obtain the second string through CE2B→16:DF0B; otherwise use0.
   Push this pointer and call CDB3→overlay4:E182 with three words.
4. Save the returned adoption flags. For modes0/1 with a supplied destination,
   call CD47→16:E0A4 to flush pending far-global string output. Mode2 skips it.
5. Flag bit2 calls BAE7→overlay3:E18A, the KEY-file path. Flag bit4 calls
   resident0CD2, the META/KBD loader. The command returns these flags in AX;
   they are not its language-level success/failure boolean.

DF0B is a writable-capable string reader, not an intrinsic type check. Native
DF13 also accepts literal/builtin encodings; the compiler enforces the different
DIAL/REDIAL destination and MDIAL input grammars. Far globals use near scratch
and pending-copy state; bank/local strings can be direct pointers. A future
binding must preserve those existing string ownership/flush semantics.

## Selection, result publication and side effects

Overlay4:E182 takes `(second_pointer, first_pointer, mode)` and returns with
`RET6`. It saves cursor/display context and selects a dialing layout from the
physical row count before entering either branch.

For DIAL/REDIAL, it calls CFE7→overlay5:E423 with the supplied selection string
for mode0, or the original empty string at DS4942 for mode1. Nonempty selection
text resets the retained15-slot list, uppercases/tokenizes the input on space,
comma and semicolon, copies at most5 token bytes per seven-byte slot and clears
each selected slot's byte+6 flag. An empty string retains the previous list.
Thus DIAL `""` also reaches the retained-list path; grammar acceptance alone
does not guarantee a selected number or a connection.

E423 enters the shared overlay5:E5E3 selection/attempt loop. Each selected token
passes through EC61, the recovered quickdial expansion described in
[DIRECTORY_DIAL.md](DIRECTORY_DIAL.md). Its result is0 for the current/manual
record or a **one-based** directory entry1..200. Values outside that range are
discarded. The loop returns the successful index unchanged, or signedFFFF/-1
on cancellation/exhaustion/nonconnection. It does not return an AX boolean.

After E423 returns, E182 calls E20A with that index. If an output string was
supplied, resident8E6C writes the index as base10 text **even on ordinary dial
failure**: failed/cancelled/exhausted selection writes `"-1"`; current-record
success writes `"0"`; directory success writes `"1"`..`"200"`. The helper then
flushes a far-global output. Operand-decoding aborts before the engine are a
different path and do not establish this publication. No original behavior for
a future maintained broker/service failure is inferred here.

E182 finally writes DS:D124=`(selected_index<0)`, the native FAILURE result;
SUCCESS tests its zero value. The [string comparison result](ASPECT_STRING_COMMANDS.md)
uses the same state, so these conditions must observe the latest operation.
This result is distinct from maintained fatal runtime error codes.

E20A returns0 immediately for indexFFFF. For index0 it skips directory reload,
count/date update and persistence, but still adopts/reset fields from the
current record. For index1..200 it loads the record, increments the call count,
formats the date, updates cached storage and calls the partial directory writer.
It then adopts terminal byte+49h and protocol+48h, invokes reset20A4(1), and
handles nonblank META(+5Fh) and KEY(+56h) names. META produces flag4; KEY produces
flag2. The original year/date/count defect remains as documented in
[DIRECTORY_ACCOUNTING.md](DIRECTORY_ACCOUNTING.md); a maintained date policy
must be stated separately.

There is **no record+34h automatic-script branch in this script E20A/helper
path**. Foreground directory code D943..DA04 has an extra script handoff/bit1.
Reusing that entire foreground binding path would add behavior absent here.
Successful DIAL must not silently replace the currently executing script with
the directory's login script.

For MDIAL, E182 calls CFF3→overlay5:E556 with the number and optional display
name. E556 initializes a single quick slot `"0"`, constructs a manual record
from current port/baud/parity/data/stop/duplex/terminal state, uses `MANUAL DIAL`
when the second pointer is0, and enters E5E3. It does not call E20A or publish an
index destination; E182's returned adoption flags remain0. It still writes
FAILURE from the returned signed index. The native number copy is unbounded
strcpy into the record's phone field; compiler string acceptance is not a
runtime capacity guarantee. No unsafe long-number runtime probe was executed.
The manual initializer clears protocol, DIRECT-mode, accounting and KEY/META
fields rather than inheriting those fields from a prior directory selection.

The working record E650 and selected-directory index E482 are separate state.
E556 changes the working record without an explicit E482 write in that body.
Likewise FROMDDIR is the script-launch origin at4AFE; the examined helper/engine
and manual-record bodies do not assign it. Dial results must not be substituted
for script-launch origin. Existing maintained child directory getters use a
private114-byte snapshot and return no record for entry0. Native getters read
the working record, including manual/current-record data. The exact handoff
rules for that distinction need implementation/tests; clearing every directory
field for manual0, or leaving the old private record after selection changes,
would both require evidence rather than assumption.

## Cancellation and the native serial dependency

E5E3 applies the selected record before the attempt: it may close/change the
port through ADBA, writes line settings and duplex, then calls03A7. Any nonzero
record mode+4Ah bypasses modem dialing and supplies success1 (DIRECT); unknown
bytes are not validated in the native body. The exact native apply fragment and
its limitations are already in [DIRECTORY_DIAL.md](DIRECTORY_DIAL.md).

MODEM calls overlay5:E8AD. It initializes resident response matcher4A1D, flushes
input through ABCA, sends configured dial prefix, expanded number and suffix
through48CC, restores temporary command pacing/duplex settings, and waits using
DOS seconds3323, keyboard6530/7878 and UART availability8E20. Response slots0..6
mean connect;7..10 stop the attempt as failure. Successful autobaud updates the
baud selector and calls AC27. [MODEM_RESPONSES.md](MODEM_RESPONSES.md) and
[MODEM_SEND.md](MODEM_SEND.md) distinguish exact recovered bodies from bounded
maintained adapters; the complete original attempt remains unlinked.

Observed native attempt controls are Escape→1Bh, Space→2, Delete5300h→3,
End4F00h→edit the timeout, timeout/failed response→0, connect→1. The selection
loop treats Escape as sequence cancellation, Space/ordinary failure as a retry
path, Delete as removing that selection, and1 as successful return. EB89 owns
the retry pause; Space ends that pause early and Escape cancels the sequence.
Both cancellation exits ultimately produce index-1/FAILURE1 and resume the
script. They do not call the script's fatal abort routine in the examined path;
mapping Escape directly to fatal CANCELLED13 would change this contract.

Cycle/timeout/pause comparisons are signed and do not match the maintained
foreground controller's bounded deadlines automatically. The loop starts with
cycle1 before testing the cycle limit on wrap; timeout and pause checks occur
after a seconds change. Zero/negative settings require explicit compatibility
tests rather than an assumed immediate return. Native48CC itself has no cancel
poll and can block in UART transmit; bounded CTS/clock behavior in the maintained
[connection controller](CONNECTION.md) is a separate policy.

HANGUP's resident0445 can return immediately when both DS1D78 and DS3986 are
nonzero (Host mode active on a DIRECT connection; see the lifecycle section
below), and that early path retains the previous FAILURE value. Otherwise it clears
FAILURE, brackets cursor state, optionally displays a message, conditionally
drops DTR, sends the configured hangup command if carrier is present, tests
carrier again and sets FAILURE1 if still asserted. It reconfigures through03A7,
clears received input through ABCA and restores cursor state. The wrapper then
refreshes status. No generic return AX or fatal cancellation status is proved.

## Retained-state lifecycle (2026-11-25 cross-reference audit)

This section answers the earlier open questions about the selection list, the
201-byte marker area and the HANGUP gates. Every reference was found twice:
by grepping the retained per-function exports (`analysis/pcplus-main` and
`pcplus-overlay-anchored-*`) and by an independent raw-byte scan. That scan
decoded every little-endian occurrence of each address, including negative
displacements, in the resident image (EXE offset 4608, 53456 bytes) and all 31
overlay payloads. The two methods agree. All other raw hits were misaligned
noise that the per-function exports confirm. Overlay addresses below are CS
offsets (overlay 4 at D4D0, 5/7 at E3B0, 9/15/21 at D0D0, 10 at E530, 19 at
E660). Analysis output stays outside Git, as always.

**DS:1D78 is the Host-mode Connection type setting.** It is PRM offset 1F4h,
inside the 1264-byte PRM image at DS:1B84. No instruction writes it by
direct address. Setup overlay 19 edits it at CS:EE67 (`mov ax,1D78h; push ax;
call` the shared word editor). That handler is item 1 of the setup dispatch
table at DS:4E46 (trampoline BE8F). Items 10/11 of the same table edit the
answer-off/answer-on commands at 1C2F/1C16. PCSETUP's Host Mode Options screen
lists "Connection type", and both PCSETUP and DGROUP DS:6125/612B contain
MODEM/DIRECT. Every reader treats nonzero as DIRECT:

- Overlay 9 Host paths (for example CS:E4B1 and E34E) skip the carrier test and
  use session state instead when it is nonzero.
- Overlay 10 Host exit (E71B) sends answer-off 1C2F and modem op 9 only when it
  is zero.
- Between-caller resets (E76D/E7D0) run the modem path only when it is zero.

The installed PRM stores 1 at offset 1F4h. Naming it "Connection type" is an
inference from the matching dispatch-table, setup-text and behavioral evidence.
No string pointer links the overlay 19 item directly to its label.

**DS:3986 is Host mode active.** Its only writers are in overlay 10. Host entry
(CS:E645, `mov [3986h],ax` with AX=1, alongside saved session settings) sets it,
and Host exit (E759) clears it. Its readers are:

- resident0445 HANGUP;
- overlay 15 transfer (EABF), whose existing alias is `session_wait_mode`;
- overlay 21 (F080);
- Chat ([CHAT_NATIVE.md](CHAT_NATIVE.md)).

The HANGUP early return therefore means: during Host mode on a direct
connection, do not drop DTR or send the hangup command. **The maintained parent
has no Host mode.** DS:3986 is therefore always zero, and that gate is
constant-false for scripted HANGUP. If Host mode is ever reconstructed, its
active flag and the PRM Connection-type word must feed this gate.

**DS:E57E[0..200] holds the dialing directory's per-entry "marked" flags,
retained across commands.** DS:6F50 is the marked-entry count. Writers:

- the overlay 4 directory UI toggles a mark at D6EB..D702 (count ±1);
- Clear Marked zero-fills all 201 bytes at D767 and resets the count;
- loading another directory zero-fills them at D8C8 (then opens PCPLUS.DIR,
  DS:66D2);
- overlay 7 entry erase (E45A) clears one entry's mark;
- the overlay 5 selection loop clears the connected entry's mark (E866) or
  the entry Delete removed (E814), decrementing the count each time.

Overlay 5 E48E (dial marked entries) is the only producer that reads the marks
into selections. It writes the decimal entry number of each marked entry
1..200 into successive slots. ASPECT DIAL/REDIAL never sets a mark; it only
clears one on connect/Delete. The area is foreground directory state, not
per-attempt scratch. The maintained directory has no multi-entry marking UI,
so no maintained producer exists, and an all-zero area with a zero count is
behaviorally exact today. Do not discard this as disposable without that
condition. Once foreground marking exists, the parent's marks and count are the
single authoritative copy that scripted connect/Delete must clear.

**DS:70B4 holds fifteen seven-byte slots, retained across commands, but
foreground dials rewrite them.** Each slot is a ≤5-byte token plus NUL, with a
done flag at +6. Only overlay 5 touches them:

| Routine | Effect on the slots |
| --- | --- |
| EC49 reset | Clears every token and sets every flag to 1. |
| E423 (DIAL/REDIAL text) | Nonempty text resets, then parses tokens into slots with flag 0. **Empty text keeps the list.** |
| E48E (dial marked entries) | Resets, then fills from the marks. |
| E4C8 (dial one entry) | Resets, writes slot 0 as decimal text, flag 0. |
| E556 (MDIAL / manual record) | Resets, copies the manual token, flag 0. |
| E5E3 loop | Sets the flag to 1 on connect (E849), on Delete (E814), and when EC61 rejects the token (index outside 0..200, via E6A1→E836). |
| EC61 expansion | Uppercases the slot token in place. |

An empty-text REDIAL (or DIAL `""`) therefore re-dials exactly the slots that
were not consumed in the previous run. That run may have been a foreground
directory dial, a dial of marked entries, or a script. The maintained product
has only one producer: scripted DIAL/MDIAL/REDIAL. Its foreground directory
dial does not populate this list. Faithful REDIAL needs the 105 bytes to live in
parent-owned storage that survives child (script) process exits and transient
PCCONN reloads. If foreground directory dials are not to diverge, they must
also perform the E4C8 rewrite on that shared copy. Otherwise, document the
divergence as an explicit maintained policy: REDIAL after a foreground dial
reuses the script's last list.

## Ownership gap and a coherent implementation gate

The current child owns its UART IRQ, raw RX ring, translation/flow/carrier
policy and unread-byte handback while the parent's PROGRAM launch is suspended.
See `src/aspect/serial.c`, `serial_backend.asm`, `serial_handoff.h` and
`src/terminal/script_launch.asm`. The foreground modem controller assumes the
parent owns its UART and keyboard. Existing capability27 rendering calls do
not transfer UART ownership or authorize port/line reconfiguration. Calling
foreground DIAL/HANGUP from a renderer callback while the child ISR is live
would create competing owners.
The existing PROGRAM serial pause only suspends child serial use while retaining
its ring/descriptor; it is not a complete parent-UART acquisition operation.
The parent's current connection controller also contains foreground
program-cancellation and automatic-script hooks. A script context needs explicit
behavior for both, rather than relying on the current active-kind guard to
incidentally suppress them. Intentional modem abort/carrier drops during dialing
also need a connection transition state distinct from unexpected carrier loss
in an ordinary connected script.

Before enabling any of these commands, one complete design must cover:

1. Compiler bindings for the four grammars, frozen original bytecode/rejections,
   local/parameter/bank strings and reserved-name behavior. Keep the opt-in
   runtime profile separate from original grammar acceptance.
2. Exact wrapper/shared/selection/result bodies and their distinct dependencies:
   pending string output, retained selection list/manual record, UI/key/time,
   modem sending/matching/abort, serial format/autobaud/port changes, reset,
   accounting/persistence and KEY/META loading. Recover or explicitly refuse
   unavailable producers before mutation; do not return invented success.
   Refresh the child's directory working-record/line/terminal/protocol view
   after adoption while retaining independent script-origin and active-script
   state. Current string/record pointers must not outlive replaced storage.
3. A checked child↔parent connection owner transition with one active ISR and
   consistent PIC/IER state, raw RX/TX/flow preservation, private lease/stack
   validation, and a defined handback after success, retry, cancellation,
   disconnect, reconfiguration and failure. This audit selects no new wire ABI.
4. Script-visible connection failure/selected-index publication independently
   from fatal broker/UART/ownership errors. Preserve held files/globals on the
   ordinary `FAILURE1` continuation; fatal error cleanup is a separate test.
5. Full actual-DOS scripts covering all four commands together: selected1/200,
   index0/current/manual, list retention/empty input, MDIAL label omission and
   literals, result `-1` on Escape/exhaustion, Space/Delete/retry limits, DIRECT,
   response/autobaud and same-write CONNECT+banner, HANGUP carrier outcomes,
   serial restoration, subsequent WAITFOR/TRANSMIT/screen/GET, and return to the
   same parent. Include missing KEY/META/reset/persistence failures, fatal
   service refusal and native near-abort/overlay reuse boundaries.

Wrapper byte equality or a modem-response helper alone cannot close this gate.
No physical modem/UART timing, live BBS, private configuration/directory data,
native terminal/DOS connection execution or end-to-end ASPECT dialing is claimed.

## Isolated native component

[connection_commands.asm](../src/aspect/connection_commands.asm) contains11
recovered units,1,527 bytes: the three dialing entries, shared5695, HANGUP entry
and0445 body, E182 engine, E20A adoption, E423 list parser, E556 manual-record
initializer and E5E3 selection loop. It reuses the existing576-byte
[attempt](../reconstruction/modem_responses/attempt.asm), giving2,103 native
connection-family bytes. The
[provenance ledger](../reconstruction/aspect_connection_commands/provenance.json)
records each original range/hash,16 retained REA exports,54 call bindings and71
data bindings. Both flat exact units and symbolic OMF objects assemble; no
ordinary application builder selects the new source.

[check_aspect_connection_native.py](../standalone/check_aspect_connection_native.py)
defaults to authored source/provenance inputs. Optional `--original` verifies
the pinned original SHA and compares every assembled new/reused range against
the original file without executing that executable. The CPU model executes
the recovered engine/selection/attempt instructions, existing native string
readers/far copy/writeback, signed decimal formatting, uppercase/length and modem
response matcher. UI, time/input, sender/receive, expansion, retry delay/abort,
directory/cache/file/persistence, reset and KEY/META callbacks remain explicit
modeled boundaries. Invalid operands stop at the native fatal-handler entry.
OMF assembly establishes symbolic relocations, not a maintained linked service.

The completed matrix has241 cases and4,330 explicit checks, including near
return/stack/canary/BP/SI/DI and DS=SS/IF/DF checks. It separates modeled selected
results -1/0/1/200 from full native-loop and complete-command paths. It checks
optional bank/global outputs, MDIAL literal/builtin/global inputs, decimal
publication and failure flush, adoption bits and ordering,15-slot parsing,
CONNECT+retained banner, Escape continuation, Space/Delete, native retry-limit
exhaustion, DIRECT bypass and HANGUP gating/DTR/pacing/call order. The stack
fixture occupies a separate region from the matcher's native8F58h cursor array.

E182 returns adoption bits in AX; shared5695 retains them in SI for dispatch,
then places them in AX before its optional META callback. META can overwrite AX.
Thus the outer command's AX and ordinary FLAGS are volatile; no public flags
result should be inferred from that return. DS=SS and DF=0 are entry contracts.
The shared helper uses RET2, engine RET6 and adoption RET2; the other recovered
entries use near RET with caller argument cleanup. All71 data symbols are
unallocated imports, with record/selection layout constraints stated in the
ledger. UART ownership, ASIO/PIC/ISR transitions, actual service failures,
resource ownership and application capacity remain the separate owner audit's
implementation gates.

## Reusable evidence ledger

The dispatch source is `analysis/aspect-vm/inventory-02.json`; compiler keywords
come from `analysis/aspect-vm-runtime/keywords-02/inventory.json`. The ignored
`analysis/aspect-script-connection-20261119/native-audit.json` binds12 original
code ranges, their original-file offsets/hashes and16 retained exports; SHA256
`4c067845b43a88729d0fe90eae58323445d4726bbb0d53fa53390d27349f7dca`.

| Context/entry | Retained assembly Evidence ID |
| --- | --- |
|resident5695 shared|`ev_68a224dfa7a066c6b1d9f93fb2ff91df97d5797d06419cb4176229341e4bc34f`|
|overlay4:E182 engine|`ev_5d453ec493498f14aadf5832f0c852b23209cb09130d32a08772c1f5028e9957`|
|overlay4:E20A accounting/adoption|`ev_c96024f10af2ad31a260e6dea4c9dae76858333b643478e9f742669eb90f3336`|
|overlay5:E423 selection text|`ev_455c98ac540b937eefd30d70b9873b72af18999b60ff0a50dc6e8d51d9d58b64`|
|overlay5:E556 manual record|`ev_3e617a9825a183fab03db388d66fb71b6c51feae30636e02aa30320ba5ebe843`|
|overlay5:E5E3 selection loop|`ev_39a79d6b6cc8461be5670ec966b27debcb038be51912017ad7373672722d08c6`|
|overlay5:E8AD attempt|`ev_5023f79a668e8360dce2412988c12d76db925a146c121f7b7531c9555fabec38`|
|overlay5:EB89 retry delay|`ev_32a78d43d8e3c9b0aceb52fe72152714f3c53dcd03e49982095faea5a03b33b4`|
|overlay5:EC0E abort modem|`ev_94814e7f388db888140f2079657a5ff4cd2adff9367e316f5fa3c90116dc7d3e`|
|overlay18:E759 HANGUP|`ev_b61736f28d3a464909f337db7988de806b8bd4e1a8719df82b07bc0b356ac1d0`|
|resident0445 hangup body|`ev_9a7bb35cde9b07a9e378a0b6babf104cb3daeef504c60c8d330431f079999cac`|
|resident2FB8 status refresh|`ev_37f3de96121de4b87b610528664677582883ea518eaecb770ba29ed10ada9cbe`|

Grammar/types/default operand roles, wrapper modes, selected-index publication,
ordinary cancellation and the dependency graph are established within the
boundaries above. Serial ownership implementation, unresolved hangup gates,
complete reset/KEY/META error behavior and native terminal/full application execution
remain open. Existing component documents retain their own narrower proofs.
