# Selected-directory protocol operand

The opt-in `directory_proto=True` interpreter executes the original read-only
integer operand `$D_PROTO`, selector7. Both maintained compilers accept it and
reserve its name. This completes runtime routing for the ten selected-directory
integer selectors1..10 when combined with `directory_fields=True`; the existing
baud and string operands retain their separate bindings. This is not complete
ASPECT or transfer-protocol parity.

The original overlay16 getter at D9C8..D9D5 is13 bytes. It multiplies the signed
byte at selected-record offset72 by6, then reads a word from DS:4DD8 plus that
offset. Its result is an ASPECT protocol constant, rather than the stored ID:

| Stored ID | ASPECT value | Protocol |
| --- | --- | --- |
|1 |5 |MODEM7 |
|2 |11 |1KXMODEM |
|3 |7 |TELINK |
|4 |17 |XMODEM |
|5 |8 |YMODEM |
|6 |4 |KERMIT |
|7 |13 |ASCII |
|8 |3 |CISB |
|9 |16 |WXMODEM |
|10 |12 |1KXMODEMG |
|11 |9 |YMODEMG |
|12 |14 |IMODEM |
|13 |6 |SEALINK |
|14 |0 |EXTPROTO1 |
|15 |1 |EXTPROTO2 |
|16 |2 |EXTPROTO3 |
|17 |10 |ZMODEM |
|18 |15 |RASCII |

[Provenance](../reconstruction/aspect_directory_proto/provenance.json) links
REA getter, bytes and table observations. Optional original checks independently
compare all13 code bytes, the resident selector7 stub and all18 consumed table
words. The maintained DGROUP table preserves the native six-byte stride; unused
pointer/descriptor words are zero. No original function addresses are embedded.

The native lookup has no bounds check. In the original initialized image,
index0 reads CB1F, part of preceding thunk data; signed negative indices and
values above18 can read other data. The maintained bridge rejects every value
outside1..18 with operand error7 before a table read or destination assignment.
A cleared no-entry record therefore refuses this operand. This is an explicit
maintained admission rule, not a claim about original no-selection startup.

[Validation](validation/aspect-directory-proto.json) binds8,448 native CPU cases:
all256 raw signed indices across33 independent
tables, exact memory-read addresses, stride, registers, near return, CF/OF and
IF/DF. Ten original DOS compiler probes establish six accepted and four rejected
sources; both maintained compilers match acceptance and every successful byte.
The complete DOS8086 compiler regression passes2,527 cases. The enabled runtime
passes1,411 cases and35,340 checks, including every raw protocol byte and prior
destination preservation on refusal. The disabled profile passes1,154 cases
and remains byte-identical to the preceding directory-fields runtime diagnostic.

Two full-parent source/GET workflows pass99 checks. They check stored protocol4
maps to XMODEM17 before/after GET and across source EXECUTE, alongside baud,
CONNECTED and the eight other directory field probes. The checked-overlay child
has near code64708 bytes,828 spare, DGROUP40608 and stack8192. Exact DOS minimum
is125696 bytes; its page-rounded minimum is125824. No buffers or VM limits were
reduced. The full application, remaining emulations/protocols and Host are still
required; Host stays last.

The matched17-file candidate is
`build/directory-proto-committed-package-20261117/PCPLUS`, targeting C:\PCPLUS.
Its source base is95abca1. Every one of the1105 files in the complete cold export
matches its Git blob at that commit; original executables, previous objects and
ancestor Git are absent from the export. The cold build reproduces all17 package
files and its ZIP byte for byte, passes34 package controls and13 lab companion
controls, and repeats the two source/GET workflows and63 nested-DOS/held-FILE/Help
checks. The archive is
`build/directory-proto-committed-archive-20261117/PCPLUSSE.ZIP`, SHA256
`3d0c7233875525c3a14d8777c36797809169ea920af11d3a5d05b92baeecf31a`.

Eight current-package DOS8086 workflows pass with COM3/IRQ5 and no BIOS UART
entry: splash, SETUP, nested source compilation, compiled clock/alarm/emulation,
line/port, Meta, seven-profile keyboard mapping/Help and Chat/Help. Synthetic
private-file preservation and hardware/environment restoration are checked.
These launcher regressions are separate from the selected-directory expression
probes in the source/GET tests.

Fresh current-byte Enigma checks pass carrier loss, two authenticated sessions,
cleanup, exact65539-byte retry, post-transfer input and normal exit (18 checks).
An independent wire audit passes; fifteen altered captures are rejected while
the unchanged control passes. Synchronet passes22 editor checks and independent
1920-cell/CPR/NAWS audits with zero differing cells. These use the actual loopback
SynthModem Telnet proxy and owned stock BBS fixtures. They do not observe the live
private board or the physical modem/SIP/audio path. The temporary lab servers
were stopped after testing.

This is a prepared hardware-test candidate. No installed selector, physical DOS
installation, private configuration/history, live SynthModem or ATA settings
changed. Physical Boca→SPA2102→SynthModem→Enigma acceptance and broader loader/Help
fault composition remain required, alongside all whole-application parity gates.

Run component checks through the pinned toolchain with fresh output directories:

```sh
./tools/dev --command python3 standalone/check_aspect_directory_proto.py \
  --output build/directory-proto-native-check
./tools/dev --command python3 standalone/test_aspect_directory_fields_compiler.py --protocol
./tools/dev --command python3 standalone/check_aspect_runtime.py \
  --directory-baud --directory-fields --directory-proto \
  --output build/directory-proto-runtime-check
```

`--original analysis/pcplus-originals/PCPLUS-main-2.01.EXE` adds the optional
private comparison to the native checker. Original executables and synthetic
analysis images are never application build inputs.
