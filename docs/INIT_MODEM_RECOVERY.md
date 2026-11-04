# Original Init Modem control recovery

Alt-J (BIOS2400) selects resident CS:3A25 through initialized DS:44E0 scan24.
The48-byte handler through3A54 now rebuilds exactly. It calls the already
recovered104-byte sender at48CC, which uses the87-byte expander at4934.
All239 bytes match the genuine2.01 executable. Relocatable OMF also assembles.
These are separate native recovery inputs, not an enabled application command.

## Original behavior

The handler saves the local-echo word and command-character pacing word. It
sets local echo to zero, clamps pacing to at least30 with a **signed** word
comparison, sends the configured initialization string at DS:1B9C, then restores
both words exactly. Values8000h..FFFFh therefore take the minimum30 path; they
are not large unsigned delays. Restoration does not normalize the saved words.

The original sender expands control notation, applies the selected pause
marker, transmits FF's embedded-NUL representation and applies calibrated delay
to ordinary bytes. The configured input string remains unchanged. Init Modem
does not dial, wait for an OK/result code, reset the call timer, or insert escape/
hangup bytes. The wrapper has no carrier/configuration-while-connected check.
This is distinct from the maintained startup initialization-and-dial controller,
which has optional acknowledged transactions and its own connection states.
The native handler is blocking and only restores settings after its sender
returns; neither it nor that sender supplies an intrinsic deadline/unwind.

Thirty is a calibrated native unit count, not an established millisecond value.
The maintained startup sender currently uses an explicitly different BIOS-tick
pacing policy. No physical pacing equivalence follows from these CPU checks.

## Evidence and verification

Fresh REA byte Evidence
`ev_63c75f97423f6a94b44eaf6a4e4d6239482b070fc467c03a0d5d971cd24db928`
contains3A25 and its terminal RET at3A54; the next routine starts3A55. Ghidra did
not automatically define a function at3A25, so this boundary is established
from the bytes/caller/RET rather than an automatically created function record.
The sender listing is fresh Evidence
`ev_09900f7c894d9ba645828379964b02da759d4881a85e2c4bd83c519ef5f31c27`.
Public [provenance](../reconstruction/local_controls/init-modem-provenance.json)
binds original offsets, state and byte hashes. Full REA records remain ignored.
The original executable is read only by the optional analyst comparison.

The source-only suite executes all65536 pacing WORD values and verifies the
clamp while the send service owns control, exact duplex/pacing restoration,
one configured-string send, DS=SS, preserved BP/SI/DI and stack guards.
Another1344 cases execute the composed239 native bytes. They vary saved duplex,
pacing, pause marker and safe synthetic initialization strings containing
control escapes, pauses, FF/NUL representations, caret quoting and an embedded
zero produced by the original expansion policy. Independent command-event
expectations require exact transmitted bytes/delays and no local echo; input
strings stay unchanged. UART/calibrated/BIOS delay services are explicit modeled
boundaries. The optional genuine-original comparison verifies the scan-table
slot and all239 code bytes before repeating both groups.

The [receipt](validation/init-modem-native.json) identifies source-only and
original-comparison runs separately. This is no actual DOS/modem timing,
nonblocking live ownership, active-call safety, BBS or physical acceptance proof.

## Live integration still required

Keep this a send-initialization operation, distinct from initialization/dial and
optional ACK policy. Reusing the startup state machine as-is would dial or
consume replies, contradicting the original command. Do not turn a manual Init
into a fabricated successful connection or log/timer event.

Bind the direct/reference/browser action only after the old view is restored
and parser/transfer/PROGRAM/ASPECT owners release admission. Use an explicit
foreground send owner so normal output cannot interleave into a partial modem
command. Preserve the call/carrier, parser, flow-control and call-log ownership
while sending. Incoming ordinary data/replies must retain their normal route;
this operation must not swallow BBS text as initialization acknowledgements.
Keep the configured bytes and private configuration unchanged. Achieve the
no-local-echo/settings-preservation contract without lending mutable settings
to concurrent owners.

The maintained owner needs bounded THRE/CTS/XOFF behavior and cancellation,
with cleanup on normal completion, refusal, cancellation, carrier loss and exit.
A partial command must retain the existing retry/resynchronization semantics;
do not invent a DTR drop or call retirement just to finish Init Modem. Check
idle/raw, confirmed online, repeated invocation, ordinary receive/CPR, owner
deferral, partial escapes, cancellation/stalls/loss and subsequent redial. Keep
calibrated-native versus maintained pacing scope explicit. Repeat source,
DOS, Enigma/Synchronet and package gates before marking Alt-J available.

The candidate340cb4ba, ten-file package and installed9f2a37e7 remain unchanged.
Alt-J still belongs to the15 unavailable original menu entries. Other controls,
file/DOS, directory/key, Chat, full ASPECT/emulations/protocols/Host and physical
BUSY/modem/SIP acceptance remain in the full goal.

```sh
./tools/dev --command python standalone/check_init_modem_native.py \
  --output build/NEW-init-modem
./tools/dev --command python standalone/check_init_modem_native.py \
  --output build/NEW-init-original \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```
