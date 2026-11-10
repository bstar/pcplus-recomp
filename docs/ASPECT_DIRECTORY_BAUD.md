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

The new profile has not been cold-replayed, packaged, installed or physically
accepted. The previously prepared hardware-test package remains unchanged and unselected;
the installed selector is unchanged. New-byte BBS/package,
broader fault composition and full ASPECT/emulation/protocol parity remain open.
Host remains last. Development is paused.
