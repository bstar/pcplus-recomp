# Automatic ZMODEM reception

The maintained terminal can start ZMODEM reception from a CRC-valid canonical
invitation when the saved Auto Download preference is enabled. It uses the
configured download directory and the existing checked exclusive receiver,
without the Alt-R/F2/filename prompt. Broader original compatibility and the
whole-application feature gates remain unfinished.

## Original behavior and maintained policy

The original Auto Download setting and terminal control handler are described in
[ZMODEM_AUTOSTART_NATIVE.md](ZMODEM_AUTOSTART_NATIVE.md). The recovered handler
checks the three bytes `B00` after ZDLE when the saved setting is enabled. It uses
blocking timed reads and reinserts mismatching lookahead by backing up the UART
ring. Those are original observations, not the implementation used here.

The maintained recognizer requires a complete canonical hex ZRQINIT invitation:
`**`, ZDLE, `B`, fourteen hex digits, CR and LF. The first decoded byte must be
zero, ZF0 must select data transfer, and the five header bytes must agree with
their CRC16. Uppercase hex and historical parity-marked LF are accepted. The optional trailing XON remains
unconsumed for the transfer owner. This deliberately requires stronger evidence
than the original three-byte trigger and has not been represented as identical
original behavior.

Binary headers, embedded flow controls, missing CR and other noncanonical forms
pass through unchanged. They do not currently start reception automatically.
These recognition limits must remain explicit during interoperability work;
manual reception continues to use the existing, more general wire decoder.
Command invitations pass through unchanged. The data/command distinction follows
section 11.1 of Forsberg's [primary protocol description](https://gallium.inria.fr/~doligez/zmodem/zmodem.txt).

## Ownership contract

`src/transfer/zmodem_autostart.c` owns no transport, screen or file resources.
Its DOS state occupies 22 bytes. It holds at most nineteen possible invitation
bytes between calls; feeding a byte releases at most twenty bytes, in order.
An invitation event can also release preceding ordinary bytes. The caller must
deliver those bytes before changing owners. A successful event consumes exactly
the invitation, never subsequent transfer or menu bytes.

A mismatch shifts the candidate one byte at a time, preserving overlapping star
prefixes. Invalid CRCs, ordinary text and canceled/incomplete candidates remain
byte-exact. `za_flush` releases the entire retained prefix and clears the state.
There is no implicit timeout or UART pushback. The terminal integration must
supply a serviced deadline and flush through the ordinary input path on expiry,
disable and ownership changes. Arguments are valid, disjoint near objects; the
output is at least twenty bytes. DS must equal SS under the DOS ABI.

## Verification

Run `./tools/build test-zmodem-autostart`. An independent Python CRC/regular
expression oracle produces 6,510 vectors. The same vectors execute against host
C and source-built 8086 DOS C, checking exact released bytes, trigger positions,
output guards and bounded state. They include every byte value substituted at
every position of a canonical invitation, every truncation, other CRC-valid
header types, data/command flags, uppercase/parity variants, overlapping prefixes, repeated headers,
long star runs and deterministic mixed binary/text streams. Invalid byte input
must leave state, output and the release count unchanged.

The DOS executable is byte-identical when rebuilt from a separate source-only
snapshot containing only the recognizer, header and test driver. Source, vector
and binary identities are recorded in
[validation/zmodem-autostart-recognizer.json](validation/zmodem-autostart-recognizer.json).
This proves the recognizer contract, not live terminal or BBS integration.

## Terminal integration

Startup reads the PRM once and stages serial, optional modem, directory context
and transfer preferences before committing any settings. The ten-word directory
entry has an explicit checked near/far bridge. Invalid paths leave the plans
unchanged. Without an explicit PRM the source-owned preference starts disabled
with current directory `.`. The recovered native three-byte trigger remains
inactive; this feature does not enable its unsafe UART lookahead path.

A successful settings child validates transfer preferences from the same bound
image as other settings. Change bit 8192 identifies an independent preference
edit. The foreground owner adopts the validated preference before acknowledging
the offer; failed children, invalid images and expired offers do not adopt it.
The existing 44-byte serial and 628-byte live-plan layouts remain unchanged.

Only acquired octets enter the recognizer; the main loop excludes the UART
empty-read sentinel. Ordinary main-loop bytes enter the recognizer after connection, monitor,
controller and transfer filtering and before translation/native parsing.
Rejected/released bytes return through that same translation/parser path. No
protocol bytes are prepended to the UART ring. The original emulation-mode
gates are retained. Detection is also disabled during local/dedicated owners,
queued macros/PROGRAM, transfer admission, break, non-eight-bit input or software
flow control. Native parser continuations keep their existing raw input owner.

A held candidate expires after 36 BIOS ticks without another candidate byte.
The foreground loop services the timeout. Before dispatching a local key it
flushes any held prefix, preserving its order before a view, PROGRAM, monitor,
manual transfer or configuration transition. Shutdown also releases the prefix.
A validated invitation queues the existing exclusive receive owner, selects
ZMODEM and copies the decoded directory. The normal transfer UI still saves and
restores its rows/cursor but skips filename input. Admission refusal replays the
complete invitation as ordinary bytes. The automatic flag is cleared on exit;
manual transfers continue through their existing prompt.

The first actual DOS prototype exposed PSP-register clobbering by the new early
initializer. The initializer now preserves AX before the existing PROGRAM/PSP
initialization. That failed attempt remains under
`build/terminal-zmodem-dos/auto-f8df-first`; it is not a passing workflow.

## Current validation and remaining work

Runtime `731418bd` passes the linked invitation/receiver tests, including four
file sizes, nineteen incomplete-header deadlines, midnight/low-word rollover, malformed/command headers and
fourteen ownership/format gates. Separate preference tests cover 60 inputs: one-read
startup, invalid-path atomicity, null/alias/wrap guards, ten-word directory
context and successful/failed live-child adoption. Its bridge checker rejects 384 damaged images.

Three actual DOS/lrzsz automatic-reception sessions pass: a small three-file
batch plus CRC16/CRC32 large batches with 8 KiB receive packets. They use only
post-transfer keyboard input, verify exact files/source/configuration, normal
exit, restored hardware/screen and resumed terminal replies. A fresh source-only
snapshot reproduces 64 current outputs. Stock Synchronet and ENiGMA download workflows also pass without local
transfer keys, including invitation/negotiation chronology, checked files, saved
configuration/directory integrity and post-transfer menu input. The full
80-command regression passes. Exact source, binary, report and retained-artifact
hashes are in [validation/zmodem-autostart.json](validation/zmodem-autostart.json).

Drive-relative current-directory forms now use the checked batch owner's
normalizer: `C:`/`C:.` inspect the drive current directory and produce `C:NAME`
file/stage paths, rather than introducing a dot component into the stricter
per-file grammar. Actual DOS tests change C's current directory to a separate
folder and verify the files land there. Absolute root-dot forms normalize to
the root. Existing stage/collision/close guards remain unchanged. Directory existence
and combined filename bounds are checked before file ownership. Short writes
and disk errors follow the existing checked close/cleanup policy. Binary/noncanonical invitations,
persisted receive resume, wider loss/line timing, physical modems, complete
original UI/emulations/protocols, ASPECT and Host remain required. All F01–F16
whole-application gates remain open.

The earlier `f0fdb62c` prototype passed its 80-command regression and its three DOS
and two BBS workflows, but a later linked midnight counterexample showed a
candidate flushing after one tick at BIOS midnight. The final elapsed-time
calculation normalizes that rollover and keeps the 36-tick deadline. The first
drive-path extension also exposed a mismatch with the stricter per-file grammar;
its failed actual DOS component artifacts are retained separately from passing
results. Neither earlier outcome is rewritten as a final passing test.

The final image uses 65,296 near bytes (240 spare), 63,630 resident code bytes
(1,906 spare) and 20,620 retained parent paragraphs including the PSP. These are
checked linker/MZ bounds, not a claim that the remaining application will fit
without further memory placement work. The complete schema/UI and physical
modem validation remain open.
