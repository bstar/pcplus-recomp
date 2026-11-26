# Scripted connection compiler and native component

Both maintained compilers now emit the original DIAL, MDIAL, REDIAL and HANGUP
bytecode grammars. This is a development component, not an enabled application
connection service. The existing runtime still explicitly refuses these opcode
slots. The qualified [capability27 package](ASPECT_SCREEN_CONNECTION.md) remains
frozen at its recorded source base and three product hashes; do not substitute
the development compiler into that payload and retain its old qualification.

| Command | Source operands | Emission |
| --- | --- | --- |
| DIAL | String selection, optional writable string result |22, input, presence, optional destination|
| MDIAL | String number, optional string display name |70, input, presence, optional input|
| REDIAL | Optional writable string result |92, presence, optional destination|
| HANGUP | None |55|

The four names also reject as global/local/parameter variable declarations,
matching original C028 observations. Inputs support the existing atomic string
codec, locals/parameters, S0 and read-only string builtins. Result destinations
reject literals/read-only builtins and numeric storage. Whitespace-separated
commas retain the observed original acceptance, while adjacent commas,
parenthesized/concatenated operands, missing separators and excess operands
reject. Original runtime index publication, ordinary FAILURE and resource
adoption are separate [native contracts](ASPECT_SCRIPT_CONNECTION_RECOVERY.md).

The public [fixture](../standalone/fixtures/aspect_connection_compiler_vectors.json)
freezes311 unique sources from320 actual original DOS8086 observations. Both
maintained compilers match82 accepted ASX outputs and229 refusals exactly at
`build/connection-compiler-oracles-v1-20261118/result.json`. The normal checker
executes only the source-built compiler; original binaries are optional oracle
provenance and never normal compiler/application inputs.

The GET-enabled development compiler is
`build/connection-compiler-v1-20261118/ASPCOMP.EXE`, SHA256
`ce833af2eb8bf56acb61ee89b7a5f659d668882e5530cfe65fe8c2a901e2f459`.
The ordinary DOS compiler regression passes4981 cases,1693 API checks, all26
program/29 inventory fault points,100 ownership cycles and CLI rollback tests.
The checked-stack run passes4999 cases including18 maximum-line expression
stress cases, with a checked16KiB API stack and24KiB CLI; deliberate2KiB guard
overflows are observed. No grammar, buffer or stack capacity was reduced.

The larger development compiler also passes all five existing full-parent
DOS8086 screen/source/operand-error workflows,254 checks, including source
startup and EXECUTE. This verifies its compilation memory budget beneath the
current complete parent/interpreter. Those scripts exercise established screen
behavior; they do not dial or hang up.

The [native component](ASPECT_SCRIPT_CONNECTION_RECOVERY.md) adds11 exact units,
1527 bytes, and reuses the576-byte attempt. Source-only and optional-original
runs each pass241 cases/4330 checks, executing22 native/helper units. Symbolic
OMF objects assemble. UI, actual UART/PIC/ISR ownership, reset, KEY/META loading,
persistence and other imported services remain controlled boundaries. A subsequent compact symbolic link passes40 CPU cases/657 checks, verifying
all71 DATA aliases and856 controlled FAR callbacks with private/parent DS=SS
and stack restoration. It allocates10880 bytes (3890 code,2840 initialized/BSS
data,4096 stack,32 guards,22 alignment). It fits16KiB, exceeds8KiB, and retains
all buffers. Keeping its288-byte MZ header gives11168 bytes. The measured private
stack high-water is214 bytes; the allocated4096-byte stack is retained. Real
parent services/resources and persistence across unloads remain outside this
component; CPU reads are not instrumented. Production placement and the
[parent/child owner contract](ASPECT_SCRIPT_CONNECTION_OWNER_AUDIT.md) remain
integration gates.

The [component ledger](validation/aspect-script-connection-components.json)
binds these receipts. The next step must cover the entire four-command
lifecycle: retained selection/manual record, output/FAILURE ordering, one UART
owner, accepted line/port changes, dual directory-cache refresh, independent
FROMDDIR, resource/accounting behavior, raw CONNECT+banner preservation and
continued script execution. This component does not close F13, physical
acceptance or complete PCPlus; Host remains last.
