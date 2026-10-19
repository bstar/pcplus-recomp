# Automatic ZMODEM reception: invitation recognition

Automatic reception remains unfinished. This checkpoint adds a source-owned,
separately tested invitation recognizer; it does not enable automatic transfers
in the terminal or change the current application executable.

## Original behavior and maintained policy

The original Auto Download setting and terminal control handler are described in
[ZMODEM_AUTOSTART_NATIVE.md](ZMODEM_AUTOSTART_NATIVE.md). The recovered handler
checks the three bytes `B00` after ZDLE when the saved setting is enabled. It uses
blocking timed reads and reinserts mismatching lookahead by backing up the UART
ring. Those are original observations, not the implementation used here.

The maintained recognizer requires a complete canonical hex ZRQINIT invitation:
`**`, ZDLE, `B`, fourteen hex digits, CR and LF. The first decoded byte must be
zero, ZF0 must select data transfer, and the five header bytes must agree with
their CRC16. Uppercase hex and
historical parity-marked LF are accepted. The optional trailing XON remains
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

## Work still required

The mapped editor and checked transfer-settings decoder now cover both fields;
see [TRANSFER_SETTINGS.md](TRANSFER_SETTINGS.md). Connect that decoder to startup
and live adoption, then reconcile the directory with the checked file owner,
including current-directory and drive-relative forms.
Connect recognition to serviced terminal input with
correct translation, capture, native parser continuation, printer/controller,
monitor, PROGRAM and pending-transfer boundaries. Start the existing exclusive
ZMODEM receiver without an Alt-R/F2 prompt and preserve its checked destination,
cancellation and restoration semantics. Exercise enabled/disabled settings,
fragmentation, partial-header expiry, ordinary text, owner changes and failure
paths in the linked application and actual DOS. Then verify automatic downloads
and post-transfer interaction on the owned Synchronet and ENiGMA fixtures.

All F01–F16 whole-application gates remain open.
