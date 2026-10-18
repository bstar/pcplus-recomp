# Configuration C in a separate DOS code segment

The normal terminal links the directory transaction, pure628-byte settings
candidate decoder, live setup owner, checked XLT reader, default-table owner and
bounded environment-directory helper, live table stager and maintained redisplay, filename clipboard core/UI, command menu/help and PROGRAM command policy in `CONFIG_CODE`, with a distinct CS and `CONFIG_GROUP`.
Mutable data and ordinary pointers remain in DGROUP with DS=SS. The command menu
explicitly places its read-only text/table in the code segment. All twelve C modules
still use Open Watcom's small model and ordinary near calls; only their code
placement and named external imports change. This frees resident code space for
the settings workflow without changing the public near-cdecl API.

Eighteen resident entry stubs preserve the public names. They copy only
their declared1,2,3,5,7,8 or9 word arguments into a far call. The far wrapper copies
those arguments into an ordinary near-C frame and calls the renamed local
implementation. Both frames use LEA/POP to release copies, retaining the
actual target's return registers and FLAGS; original caller argument slots
remain owned by the caller. These are not variadic, RET-N or callback adapters.

The C implementations call each other directly within CONFIG_CODE. Six
explicit register-ABI imports (`memcpy`, `memset`, `memcmp`, `strchr`, `strcmp` and the DOS
canonicalizer) use named near thunks to far-call their resident counterparts.
Twelve more callbacks
copy1..4 cdecl words to the resident terminal/modem decoders, PRM/directory
readers, bounded number expander, native command-expansion status adapter and the checked XLT open/read/close adapters, plus the DOS EXEC process boundary and the history file event owner plus clipboard transport. Register imports retain the compiler's
trailing underscore symbol convention; they cannot use the cdecl adapters.
The modem callback family's existing1..4-word contract is unchanged.

The XLT adapter uses explicit near-cdecl3/4/1-word open/read/close services.
Resident `xlt_dos_fs.c` owns the DOS CRT far-pointer/register ABI conversions.
Direct register-only thunks are insufficient for this DOS read interface: its
stack arguments must survive the additional far frames. Actual linked reads,
EOF probes and failed reads exercise these adapters; all256 input bytes and
caller state are checked. See [live translation](LIVE_TRANSLATION.md).

`config_abi.inc` declares all36 bridge pairs. `terminal_memory.py` validates
their exact instructions, argument offsets/counts, near/far targets, return
forms and required MZ relocations. It also checks an end marker linked after
all twelve C objects, ensuring the extent covers the implementations rather than just
the assembly wrappers. All code must fit its own64KiB segment, be present in
the loaded MZ, be disjoint from other code/data owners and remain covered by
PROGRAM's retained parent allocation. Together with PRINT/MODEM this validates
85 bridge pairs including four viewer register entries.

`check_config_far_live.py` rejects173 intentionally damaged frames, relocations
and layouts. The independent311 directory and507 context cases execute normal
terminal entry points across the bridge. `check_live_configuration.py --terminal`
replays the same389 independently specified candidate cases against the normal
terminal binary. Caller fixtures occupy3526 bytes at the bottom of the actual
8KiB stack; every executed instruction is checked for stack collision. No
product scratch globals or memory beyond the real stack are borrowed. The
standalone near-C diagnostic remains available for independent comparison.

The current terminal candidate replay uses at most3050 bytes of call stack,
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
checked file owner. That history checkpoint used64,516 resident code bytes,
62,848 near data/stack bytes and299,232 retained parent bytes including PSP.
Its DOS export tests exercise all three callback operations with actual files;
see [history export](HISTORY_EXPORT.md). Earlier PROGRAM-only memory values
above describe that migration checkpoint.


The filename clipboard adds a compiler-register strcmp import, a three-word
resident transport callback and a named MODEM_CODE abort service. The latter is
required when connection owners discard TX: a near cross-segment call is invalid
and the actual DOS development run caught that mistake. That clipboard checkpoint checked
36 configuration,23 modem,22 printer and4 redisplay bridge pairs. That
clipboard checkpoint used64,796 resident code bytes,64,128 near data/stack bytes and304,992
retained parent bytes including PSP. Clipboard core/UI code shares CONFIG_CODE;
no extra full-screen frame is allocated. See [clipboard](FILENAME_CLIPBOARD.md).

The saved separator explicitly extends the serial plan to44 bytes and the
candidate to628 without changing bridge argument counts. Live setup tracks its
saved baseline separately from session R; see [clipboard settings](CLIPBOARD_SETTINGS.md).

The maintained [command menu/help](COMMAND_MENU.md) adds a twelfth C module,
with code-based names/prose/table and48 bytes of near state/query storage.
At that menu checkpoint near data/stack is64,176 bytes and the retained parent including PSP is
312,640 bytes. Resident code remains64,796 bytes and the same85 bridge pairs are
checked. The linker verifier separately requires the menu entry in CONFIG_CODE
and its mutable state in DGROUP. No additional full-screen frame is allocated.

Parser-safe [pending menu entry](MENU_PENDING.md) adds a two-byte flag and reuses
the32-word foreground typeahead. At that checkpoint near data/stack was64,192
bytes, resident code64,932 bytes and retained parent312,848 bytes. The85 bridges and their
argument counts remain unchanged; a distinct resident service dispatches the
retained request through the existing key entry. Real AX0 BIOS keys retain their
ordinary meaning. No new buffer or far callback is added.

[Explicit table reload](TRANSLATION_RELOAD.md) adds startup-selection and reload
entry frames of five and three words. Current checks cover38 configuration
pairs,87 total, and187 damaged frames/layouts. The same twelve C modules remain
in CONFIG_CODE; the reload state machine extends the existing translation owner.
Current near data/stack is64,480 bytes, resident code65,298 bytes and retained
parent314,736 bytes including PSP. All static code/data extents remain covered.
