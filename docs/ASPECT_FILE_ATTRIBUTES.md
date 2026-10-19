# ASPECT file attributes

The maintained compilers and production DOS interpreter now support GETFATTR and
SETFATTR. The dispatcher implements 96 of 215 opcode slots and explicitly rejects
119. This advances the maintained language without closing F13 or any other
whole-application gate.

```text
string flags
proc main
getfattr "DOWNLOAD.ZIP" flags
if success
message flags
endif
endproc
```

GETFATTR takes an atomic path string and a writable string destination. SETFATTR
takes an atomic path and an attribute string. A single comma may separate the
arguments. The original compiler's 54 authored cases establish 19 byte-exact
accepted ASX outputs and 35 rejections, including string registers, locals,
parameters, read-only builtin inputs and the 80-character boundary. The full
8086 DOS compiler passes 1,664 cases: 918 exact accepted outputs and 746 rejected
sources. Expression operands, wrong destination types and malformed separators
remain rejected.

The GET helper uses DOS interrupt21h/AX4300h and substitutes FFFFh on kernel error.
The command formats the low attribute bits as R/H/S/A/D/V in that order. Its
comparison is 0 on success or 1 for the FFFFh sentinel. Consequently a missing
file writes `RHSADV` while reporting failure; check SUCCESS before treating the
output as metadata. The maintained version preserves this native result policy.

SET parses R, H, S and A, case-insensitively, then uses DOS AX4301h. Empty flags
clear those bits. Comparison is 0 or the raw DOS error word, including 2 for a
missing file in the actual DOS regression. Directory and volume bits are not
accepted by this setter's native parser mode. Invalid characters invoke native
error0; the maintained interpreter's fatal operand-error policy aborts before
any attribute update. The original interactive returning-warning policy remains
unimplemented; its returning branch is characterized separately in the component.

REA/Ghidra identifies 100 exact command/helper instruction bytes. The component
reuses the already recovered 127-byte attribute parser and 76-byte formatter
from file enumeration. Source-only builds verify those bytes against numerical
hashes/locations; they do not read an original executable or REA database. The
1,081 component cases and a separate matching original-byte replay cover all
8-bit attributes and errors, wide error/sentinel words, mask combinations,
returning warnings and nonstack-data/register/stack invariants. Kernel and string
operand boundaries are explicit models, not an actual filesystem claim.

The original GET wrapper calls the source-string reader for its destination and
never flushes a far-global writeback. A real8086 DOS control links that unmodified
source-built wrapper into the same actual interpreter: a far global stays
`BEFORE`, while local, parameter and string-register outputs become `RHS`.
The maintained handler selects a destination and calls the native flush helper.
Its extra three-byte call and changed reader target are explicit under
`ASPECT_FILE_ATTRIBUTES_RUNTIME`; the exact100-byte baseline remains unchanged.
All four destination classes then receive the same result.

Actual DOS testing passes279 invocations and2,403 assertions in one process.
It checks every RHSA mask, lowercase/duplicate letters, real missing-file statuses,
directory attributes, the four destination classes, six occupied script streams,
unchanged shared FOUND across GET/SET, EXECUTE continuation and invalid/truncated
operand aborts. Rejected updates leave the file's prior mask intact. Used near/far
heap blocks and the inherited DOS handle table remain identical after warmup;
INT0, FLAGS and the native ABI restore after each invocation. All file bytes stay
unchanged. The source-built native-wrapper control passes ten independent checks;
an explicit production ASP child also compiles and runs the global-writeback path.

A real terminal child gates its login on setting/getting `RHS`, clearing it, and
reading an empty global result, then returns to normal parent input. The optional
ENiGMA `--attribute-login` mode performs the same roundtrip on a generated file
before authentication and writes the exact `RHS|` trace. All20 checks pass, including the existing query/rename, enumeration, source-login
and custom search/index/DIZ/NFO route checks. This is the isolated patched owned board, with synthetic files and no
saved posts; the live board and physical RS-232 Wi-Fi modem remain separate work.

```sh
./tools/dev --command make test-aspect-file-attributes test-aspect-file-attributes-compiler
./tools/dev --command python3 standalone/test_aspect_file_attributes_dos.py --label unique-attrs-run
```

The first primitive fixture expected the raw DOS helpers to consume cdecl
arguments. Correcting that stack expectation changed no native instructions;
the complete source/original replay then passed. The original global-writeback
behavior is a successful characterization, kept separate from the maintained
application's corrected result.

The [validation record](validation/aspect-file-attributes.json) binds native,
compiler, native-control/VM, parent, ENiGMA, package and241-output clean source
rebuild identities. The310 enumeration/155 query/341 stream regressions remain
passing against these same binaries. File date/time commands, other remaining language families, recorder,
full application services/UI/protocols/emulations/Host and target hardware remain
required. The [enumeration checkpoint](ASPECT_ENUMERATION.md) retains its own
historical results and explicit DTA/volume normalization policies.
