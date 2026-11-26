# Selected-directory baud expression

The opt-in `directory_baud=True` runtime now executes `$D_BAUD`, which both
maintained compilers already accepted as long selector0. It returns the configured
baud from word46 of the selected114-byte directory entry. The original table is
300,1200,2400,4800,9600,19200,38400,57600,115200. This expression does not measure
UART DTE speed or negotiated carrier.

REA evidence in [the provenance](../reconstruction/aspect_directory_baud/provenance.json)
identifies original overlay16 DA59..DA6A and the DS3270 DWORD table. The recovered
17-byte getter retains its native indexing and32-bit DX:AX result. The maintained
runtime bridge rejects indices above8 with operand error7 before reading beyond
the table or changing the destination. A cleared no-entry record returns300 from
index0; this follows the maintained reset policy, not proven original startup
behavior without a selected entry.

[Validation](validation/aspect-directory-baud.json) records297 native CPU cases
and optional original code/table comparisons;1145 actual DOS runtime cases with
27579 assertions; two full-parent source-compilation/GET cases with95 checks;
and63 nested-DOS/held-FILE/Help checks. The first integration trial had an
incorrect CONST frame and37 failed assertions; assigning the table to DGROUP
fixed the relocation, and the full suite then passed. The original getter bytes
and expected values were retained.

The disabled interpreter is byte-identical to the prepared668e9722 candidate.
Enabled interpreter0bd5ad1c has near code64596, DGROUP40496, unchanged8192-byte
stack and unchanged bank sizes. Its exact DOS minimum is125472 bytes. No buffer
or limit was reduced. Both compilers' source grammar remains unchanged.

On November17, a cold export of1063 source files reproduced the terminal,
interpreter, compiler and overlays, then repeated the two source/GET cases and
63 nested-DOS/held-FILE/Help checks. A separate complete1103-source export
reproduced all17 files in `build/directory-baud-connection-package-20261117`
and its ZIP byte for byte, without originals, prior objects or ancestor Git.
The archive SHA256 is
`38609dee876e476a8a2dff9690e7d80187b28482a8be3a6f9df6b57b2eae8bbe`.
All34 package controls and13 lab companion controls pass.

Eight packaged DOS8086 workflows pass with COM3/IRQ5 and the BIOS UART entry
absent: splash, SETUP, nested source compilation, compiled clock/alarm/emulation,
line/port, Meta, seven-profile keyboard mapping/Help and Chat/Help. These tests
check synthetic private-file preservation and hardware/environment restoration.
The selected-directory38400 expression is exercised in the separate full-parent
source/GET cases; the packaged launcher cases do not add directory-baud operands.

The new profile is staged, not installed or physically accepted. The installed
selector is unchanged. New-byte BBS qualification, broader fault composition and
full ASPECT/emulation/protocol parity remain open. Host remains last.

The later [protocol-operand profile](ASPECT_DIRECTORY_PROTO.md) includes this
baud getter and the directory integer getters in a separately identified package
with fresh Enigma/Synchronet checks. This baud-only artifact retains its own
recorded limits; neither profile has physical acceptance.
