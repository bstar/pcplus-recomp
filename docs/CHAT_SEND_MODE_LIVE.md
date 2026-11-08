# Live Chat send-mode configuration

The opt-in `--chat-send-mode` parent now imports the original PRM01F2 byte and
uses it when constructing Chat. Zero sends characters immediately; all nonzero
bytes buffer a line until Enter. Without an explicit configuration, the maintained
default remains buffered. The [recovered byte-field evidence](CHAT_SEND_MODE_SETTINGS.md)
and optional offline editor establish the file format; this checkpoint connects
that setting to the running application.

The byte follows the existing preference-reader path rather than enlarging the
44-byte serial settings structure or628-byte live plan. Serial-only, modem and
selected-directory startup readers publish it only after all decoding, mouse
staging and session-baseline publication succeed. Pointer aliases with the new
global are refused before file I/O. The stored byte is retained without boolean
normalization; Chat's existing send owner handles its zero/nonzero meaning.

After a successful settings child, the live owner classifies a changed mode with
bit8000h and adopts it only at acknowledgement after baseline validation. The
next Chat entry receives the updated value without resetting the terminal or
moving its UART. Chat's already implemented immediate/buffered owner is reused.
No setting is written merely by importing it.

The matched Chat module uses API0107; legacy builds retain API0106 and their old
behavior. The new constructor consumes the existing request's buffered field
and refuses values above255. The loader still checks exact file/image identity
and API before admission. Its descriptor, state, request and buffer sizes are
unchanged. This opt-in parent must be distributed with its matchingPCCHAT.OVL.

The [validation record](validation/chat-send-mode-live.json) binds the following
results to the exact parent, module and current source inputs.

## Validation

Three actual DOS8086 startup cases import0,1 and255. In immediate mode an
unfinishedPING reaches the serial peer before Escape; in both buffered modes
it is discarded. A second Chat entry submitsSEND with Enter, receives raw peer
text without answering a Chat-pane CPR, then returns to ordinary input/CPR.
Settings, executable/module bytes and final UART/PIC/vector state are checked.

Three further DOS8086 cases invoke the production52-field settings editor from
the running parent, change1→0,0→1 and0→255, save and return without restarting.
A second unfinishedLIVE line proves that the new mode is active; a third Chat
entry submitsSEND. Exact PRM changes are limited to01F2, with adjacentA7 intact.
The helper, parent and module bytes remain unchanged, and normal terminal input
and hardware restoration pass. No child shortcut rewrites the setting for these
live editor tests.

A separate actual DOS case supplies the previousAPI0106 module to the new parent.
Chat is refused and ordinaryNORMAL input receives a real terminal CPR response;
an admitted Chat pane would consume that query without answering it.

The linked preference-reader checks cover295 byte, refusal and alias cases:
all256 values in serial-only startup, selected noncanonical values in modem and
directory startup, read/decode/transfer/mouse/late-baseline failures and aliases
with every pointer role. File effects are modeled in those checks; BIOS keys,
real file writes and UART operation are established separately by the DOS cases.

The unchanged-feature control rebuilds the previous parent byte for byte. The
opt-in parent retains80 additional bytes, five DOS paragraphs. DGROUP remains
65520 bytes with16 spare; resident CS, stack/history capacities,63000-byte history
and65504-byte reset workspace are unchanged. The two source-digest pins were
refreshed without changing compiler options; disabled bytes establish that their
conditional additions leave the prior optimized product intact.

Nested startup and EXECUTE source compilation through the matching ASPECT child
and DOS compiler are checked separately. The first invocation omitted allocation
observation required by that checker and ended with a missing-probe error; it is
excluded. The observed repeat passes both final cases with exact compiled ASX,
real compiler execution in lent memory and success status. Intermediate log lines
precede final source-specific checks; the final case artifacts determine acceptance.

This remains an opt-in application checkpoint. No selected package, physical
installation, private settings or call history is changed. Current BBS regressions
for the preceding parent do not automatically certify these new bytes. The
[new BBS checkpoint](CHAT_MODE_BBS.md) now supplies selected fresh Enigma/Synchronet
results; complete package and hardware acceptance remain required.

A cold1042-file public source export reproduces the new parent, API0107 module,
matching ASPECT interpreter and DOS compiler byte for byte, then repeats both
nested compilation cases with identical final checks. Originals, private files,
prior objects and ancestorGit are absent from that export. This proof does not
build or certify a complete release archive or repeat the older BBS suite.
