# Configuration C in a separate DOS code segment

The normal terminal links the directory transaction and pure624-byte settings
candidate decoder in `CONFIG_CODE`, with a distinct CS and `CONFIG_GROUP`.
Their data, constants and pointers remain in DGROUP with DS=SS. Both C modules
still use Open Watcom's small model and ordinary near calls; only their code
placement and named external imports change. This frees resident code space for
the settings workflow without changing the public near-cdecl API.

Five resident entry stubs preserve the original public names. They copy only
their declared5,7,8 or9 word arguments into a far call. The far wrapper copies
those arguments into an ordinary near-C frame and calls the renamed local
implementation. Both frames use LEA/POP to release copies, retaining the
actual target's return registers and FLAGS; original caller argument slots
remain owned by the caller. These are not variadic, RET-N or callback adapters.

The C implementations call each other directly within CONFIG_CODE. Four
explicit register-ABI imports (`memcpy`, `memset`, `memcmp`, `strchr`) use named
near thunks to far-call their resident CRT counterparts. Five more callbacks
copy1..4 cdecl words to the resident terminal/modem decoders, PRM/directory
readers and bounded number expander. Register imports retain the compiler's
trailing underscore symbol convention; they cannot use the cdecl adapters.
The modem callback family's existing1..4-word contract is unchanged.

`config_abi.inc` declares all14 bridge pairs. `terminal_memory.py` validates
their exact instructions, argument offsets/counts, near/far targets, return
forms and required MZ relocations. It also checks an end marker linked after
both C objects, ensuring the extent covers the implementations rather than just
the assembly wrappers. All code must fit its own64KiB segment, be present in
the loaded MZ, be disjoint from other code/data owners and remain covered by
PROGRAM's retained parent allocation. Together with PRINT/MODEM this validates
58 bridge pairs.

`check_config_far_live.py` rejects55 intentionally damaged frames, relocations
and layouts. The independent311 directory and507 context cases execute normal
terminal entry points across the bridge. `check_live_configuration.py --terminal`
replays the same389 independently specified candidate cases against the normal
terminal binary. Caller fixtures occupy3514 bytes at the bottom of the actual
8KiB stack; every executed instruction is checked for stack collision. No
product scratch globals or memory beyond the real stack are borrowed. The
standalone near-C diagnostic remains available for independent comparison.

The current terminal candidate replay uses at most3042 bytes of call stack,
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
The candidate API being linked does not yet make a live settings commit safe;
that owner must still bind the current namespace/selection, snapshot effective
settings including autobaud, and apply/reset or defer changes with explicit
transport/profile policy.

The checkpoint's50-command terminal regression,60-output isolated source
rebuild,389 terminal candidate inputs,311 directory inputs,507 retained-context
inputs and actual DOS child retention are bound together in
[validation/configuration-far-code.json](validation/configuration-far-code.json).
