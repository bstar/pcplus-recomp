# Original Auto Answer recovery

Original Alt-Y (BIOS1500) dispatches through initialized DS44E0/scan15 to
resident0553. The19-byte key handler requests the configured information sound,
displays DS:[2078] with argument36, then tail-jumps to the25-byte sender at053A.
That sender saves the pacing WORD, sets it to50 unconditionally, sends the
configured answer-on string at DS1C16 and restores pacing exactly on return.
All44 bytes now rebuild exactly in flat form and assemble as relocatable OMF.

This command is **not a toggle**. It does not select the answer-off string at
DS1C2F, wait for an acknowledgement, dial, insert a data-mode escape or create a
connection/call-timer event. Native sound is conditional: DS1D40 zero is quiet;
any nonzero value requests the existing information tone with arguments20/440.
The baseline message pointer001C identifies `AUTO ANSWER...`. These are call
arguments, not proof of sound duration, actual sound output or notice pixels.

Unlike manual Init, Auto Answer does not suppress local echo. The unchanged
sender echoes ordinary expanded bytes before transmitting them when DS1D1A is
nonzero. Pause markers and FF's NUL representation do not echo. Pause matching
precedes FF matching; an embedded expanded zero terminates the command. Saved
duplex, pacing, sound, message pointer, input and the unused answer-off bytes
remain unchanged.50 is a native calibrated delay-unit count, not established
milliseconds or the maintained sender's BIOS-tick policy.

## Evidence

REA byte Evidence
`ev_a7ef70db22c1b1b74d9213ae7e7955ddd9c4060cf25635f706660793183ed0e9`
contains053A..0565. The switch is fresh Evidence
`ev_86a8b7db30021bd751396b715932797fd7e69d0ed343267445f822cc57b6ea72`.
Ghidra did not auto-define a function/instruction at0553. The first RET0552,
key-entry tail JMP0563->053A, next prologue0566, pinned ndisasm and CPU checks
establish this boundary independently. No Ghidra pseudocode claim follows from
the byte reads. Full REA records remain ignored; the session was closed.

Public [provenance](../reconstruction/local_controls/auto-answer-provenance.json)
binds offsets/hashes/state. The optional original comparison separately checks
the initialized scan-table entry and message pointer/text in appended startup
data. Those data are not claimed mapped by ordinary MZ resident analysis.

The [receipt](validation/auto-answer-native.json) separates source-only and
genuine-original checks. Each executes all65536 saved pacing WORDs, with the
send service observing exactly50 and exact restoration afterward; varied saved
duplex words cover the whole WORD range. All65536 sound-enable words verify the
actual recovered zero/nonzero switch. Another3072 composed command/echo/pacing/
pause/sound inputs and three direct sender entries check exact call/event order,
notice-before-send, no echo from FF/pause, input/settings preservation and
DS=SS/stack/BP/SI/DI. The composition contains44 new bytes,30 existing sound
switch bytes,104 sender bytes and87 expander bytes:265 total. Its11-byte error
sound entry is byte-verified but not traversed by Auto Answer.

Tone, notice rendering, UART and calibrated/BIOS delays are modeled service
boundaries. The sender remains the original blocking routine, with no intrinsic
timeout or cancellation and pacing restoration only on normal return. These
checks do not establish actual DOS/BBS/SIP/analog or physical behavior.

## Live integration required

A [typed bounded sender component](AUTO_ANSWER_OWNER.md) now implements the
answer-on identity, captured duplex and acceptance-qualified native echo with
renderer reentrancy protection. Its flag has no Alt-Y/configured command/UI
binding; the remaining integration and application gates below still apply.

Reuse the maintained send owner only with an explicit command identity and
answer-on plan. Preserve the sound setting and show the notice through a serviced
foreground UI. Retain the original echo distinction without lending mutable
echo/pacing settings to concurrent owners. If bounded UART retries require echo
after physical acceptance instead of the original before-write sequence, record
that maintained difference and check no duplicates on stalls/cancel/retry.

Use the existing parser/view/byte-owner admission and exclusive ordinary-output
scheduling, keep incoming replies/ANSI/CPR/flow/carrier on their normal routes,
and retain bounded timeout/cancel/loss/exit and partial-line retry semantics.
Do not reuse startup initialization/dial as an answer operation, fabricate a
modem acknowledgement, toggle a setting or retire the call merely to finish it.
Direct Alt-Y, reference and browser routes, notice/view restoration, local echo,
stalls, cancellation, active-call safety and subsequent dialing need live checks,
then DOS/BBS/source/package gates before making this entry available.

Alt-Y remains one of14 unavailable reference entries. The application/package
candidate8f76cc4f, archivece1a3265, active selection93a9db94 and installed9f2a37e7
are unchanged. The full parity inventory and physical acceptance remain open.

```sh
./tools/dev --command python standalone/check_auto_answer_native.py \
  --output build/NEW-answer-source
./tools/dev --command python standalone/check_auto_answer_native.py \
  --output build/NEW-answer-original \
  --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```
