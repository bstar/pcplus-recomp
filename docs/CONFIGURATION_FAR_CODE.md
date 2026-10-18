# Configuration C in a separate DOS code segment

The normal terminal links the directory transaction, pure626-byte settings
candidate decoder, live setup owner, checked XLT reader, default-table owner and
bounded environment-directory helper, live table stager and maintained redisplay and PROGRAM command policy in `CONFIG_CODE`, with a distinct CS and `CONFIG_GROUP`.
Their data, constants and pointers remain in DGROUP with DS=SS. All nine C modules
still use Open Watcom's small model and ordinary near calls; only their code
placement and named external imports change. This frees resident code space for
the settings workflow without changing the public near-cdecl API.

Eighteen resident entry stubs preserve the public names. They copy only
their declared1,2,3,5,7,8 or9 word arguments into a far call. The far wrapper copies
those arguments into an ordinary near-C frame and calls the renamed local
implementation. Both frames use LEA/POP to release copies, retaining the
actual target's return registers and FLAGS; original caller argument slots
remain owned by the caller. These are not variadic, RET-N or callback adapters.

The C implementations call each other directly within CONFIG_CODE. Five
explicit register-ABI imports (`memcpy`, `memset`, `memcmp`, `strchr` and the DOS
canonicalizer) use named near thunks to far-call their resident counterparts.
Eleven more callbacks
copy1..4 cdecl words to the resident terminal/modem decoders, PRM/directory
readers, bounded number expander, native command-expansion status adapter and the checked XLT open/read/close adapters, plus the DOS EXEC process boundary and the history file event owner. Register imports retain the compiler's
trailing underscore symbol convention; they cannot use the cdecl adapters.
The modem callback family's existing1..4-word contract is unchanged.

The XLT adapter uses explicit near-cdecl3/4/1-word open/read/close services.
Resident `xlt_dos_fs.c` owns the DOS CRT far-pointer/register ABI conversions.
Direct register-only thunks are insufficient for this DOS read interface: its
stack arguments must survive the additional far frames. Actual linked reads,
EOF probes and failed reads exercise these adapters; all256 input bytes and
caller state are checked. See [live translation](LIVE_TRANSLATION.md).

`config_abi.inc` declares all34 bridge pairs. `terminal_memory.py` validates
their exact instructions, argument offsets/counts, near/far targets, return
forms and required MZ relocations. It also checks an end marker linked after
all nine C objects, ensuring the extent covers the implementations rather than just
the assembly wrappers. All code must fit its own64KiB segment, be present in
the loaded MZ, be disjoint from other code/data owners and remain covered by
PROGRAM's retained parent allocation. Together with PRINT/MODEM this validates
82 bridge pairs including four viewer register entries.

`check_config_far_live.py` rejects167 intentionally damaged frames, relocations
and layouts. The independent311 directory and507 context cases execute normal
terminal entry points across the bridge. `check_live_configuration.py --terminal`
replays the same389 independently specified candidate cases against the normal
terminal binary. Caller fixtures occupy3520 bytes at the bottom of the actual
8KiB stack; every executed instruction is checked for stack collision. No
product scratch globals or memory beyond the real stack are borrowed. The
standalone near-C diagnostic remains available for independent comparison.

The current terminal candidate replay uses at most3046 bytes of call stack,
leaving the caller fixture and execution stack disjoint. It observes each
actual implementation RET to require full FLAGS preservation through both
entry wrappers, separately from the API's semantic return-value checks.

The actual DOS PROGRAM retention child additionally samples every relocated
CONFIG_CODE byte before and after allocating/filling a separate16KiB DOS block.
Its64-byte result includes the segment, full C extent and both byte sums,
alongside existing PRINT/MODEM sums and far data/UI canaries. This establishes
allocation/retention behavior, not cryptographic integrity or physical UART
timing. The full terminal regression also exercises ordinary configuration
startup and the direct settings child.

All builds use the pinned Nix NASM/Open Watcom toolchain. No original executable,
generated analysis executable, private PRM or REA database is a build input.
The integrated live setup owner now binds the startup namespace/selection,
snapshots effective transport including autobaud, validates native commands,
selectively applies independent settings and offers confirmed same-port serial
changes, confirmed idle COM ownership transfer and supported4/6 profile resets.
See [SETUP_LIVE.md](SETUP_LIVE.md). Full transport/profile ownership changes and
the complete application remain open.

The checkpoint's70-command terminal regression,63-output isolated source
rebuild,389 terminal candidate inputs,311 directory inputs,507 retained-context
inputs and actual DOS child retention are bound together in
[validation/configuration-far-code.json](validation/configuration-far-code.json).

## PROGRAM command policy placement

The maintained `program.c` implementation now executes in CONFIG_CODE. Its
public two-word `program_execute` entry retains the near-cdecl API; a separate
three-word `config_process_run` callback copies the pathname, command-tail and
result pointers to the existing resident DOS EXEC backend. DS=SS keeps the
local environment/path buffers and child result valid across both bridges.
The DOS backend and its CS-relative saved execution context remain resident.
No command parsing, COMSPEC/PATH order, child lifecycle or serial ownership
policy changes. This moves 1,114 net bytes out of the resident segment, leaving
1,248 bytes available for further application services; resident code is
64,288 bytes and near data/stack remains61,712 bytes. PROGRAM retention continues
to cover the complete CONFIG_CODE extent during child allocation. Total retained
parent allocation is297,184 bytes including PSP; bridge/alignment overhead adds
48 bytes relative to the preceding checkpoint.

[PROGRAM placement validation](validation/program-far-code.json) binds60 linked
inputs and four actual DOS command workflows to the current binary. Four new
observations compare FLAGS at the actual C implementation RET and the public
entry RET after normal execution, fallback, EXEC failure and resize failure.
The tests do not replace product instructions or callbacks.

The serviced history writer adds a three-word resident callback for the fourth
checked file owner. The current executable uses64,516 resident code bytes,
62,848 near data/stack bytes and299,232 retained parent bytes including PSP.
Its DOS export tests exercise all three callback operations with actual files;
see [history export](HISTORY_EXPORT.md). Earlier PROGRAM-only memory values
above describe that migration checkpoint.
