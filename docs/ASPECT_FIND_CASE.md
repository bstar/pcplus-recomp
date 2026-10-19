# Native FINDCASE and SWITCHCASE consumers

FINDCASE and SWITCHCASE have real native consumers, distinct from WAITCASE and
WHENCASE. The new source modules recover those consumers; this checkpoint does
not add them to ASPECT.EXE or complete their source-language grammar.

| Setting | Native state | Consumer | Meaning |
| --- | --- | --- | --- |
| FINDCASE | E392 word | resident FIND4FB4..4FF6, opcode3B | Zero selects insensitive substring search; any nonzero word selects sensitive search. |
| SWITCHCASE | E394 word | overlay16 CASED39F..D3F2, opcode0F | Zero selects ASCII-insensitive string comparison; any nonzero word selects sensitive comparison. Numeric CASE ignores the setting. |

The recovered generic setters store a byte as a word without boolean
normalization. The component executes all256 raw byte values through the actual
SET wrappers and then the consumers. The source compiler's ON/OFF spelling does
not establish a broader native boolean-validation rule.

## Defaults and lifetime

Overlay02D6EA..D770 initializes both settings to zero: D6F3 writes E394 and D6F6
writes E392. The original resident C1D7 overlay stub identifies overlay02D6EA.
The recovered dispatcher calls C1D7 at4B27, before its4B30 restart point. Its
CHAIN999 branch at4BF1 returns to4B30, not the initializer. The per-file cleanup
C2EB targets D88E, the recovered global-string release routine; it does not reset
these settings. Thus fresh dispatcher invocation initializes insensitive
matching, while ordinary procedure calls and CHAIN retain the global settings
unless executed code changes them. These are script-owner settings, not parent
terminal configuration.

The CPU lifecycle probe executes the actual recovered dispatcher and verifies
one initializer call across two file opens/CHAIN, followed by another initializer
call on a fresh invocation. Loader initialization/open/cleanup, application UI
and opcode handler boundaries are declared models. The zero values and native
call placement are independently retained REA observations; this probe does not
pretend to execute the entire original loader.

The observed initializer does not establish a reset of FOUND or the SWITCH
snapshot. No default or restoration rule for those fields is inferred from the
two case-setting writes.

## FIND behavior and ownership

[src/aspect/find_commands.asm](../src/aspect/find_commands.asm) contains:

| Unit | Native range | Bytes |
| --- | --- | --- |
| FIND command | resident4FB4..4FF6 | 66 |
| Sensitive strstr | resident9146..91A6 | 96 |
| Insensitive search | overlay04DCDB..DD28 | 77 |
| strdup | resident9764..9786 | 34 |

FIND reads two near NUL-terminated operands: haystack then needle. Sensitive
search uses the recovered CRT strstr; an empty needle returns the haystack
pointer. Insensitive search duplicates both operands with the near allocator,
uppercases those copies using the actual ASCII-only native helper, searches,
remaps a successful pointer into the original haystack and frees both copies.
Input strings are unchanged. High bytes are preserved by the case folding.

An optional integer destination receives matched-pointer minus haystack-pointer.
When no match exists, the native code still stores zero minus haystack-pointer,
wrapped to16bits. It does not store a universal -1. The component proves, for
example, a missing match with haystack offsetFF20 produces index00E0. Shared
FOUND at E39C becomes0 or1; original integer builtin23 reads that word at
 overlay16DA14.

Native strdup can return zero. The insensitive helper does not check either
allocation before passing it to uppercase. The checker separately tests a
return-NULL allocator and an explicit stop-at-allocation model. In the first
case it observes native control reaching uppercase(NULL), then stops before the
unchecked dereference; in the second it stops at the declared allocator boundary.
Neither model invents rollback, an ASPECT error number or safe native failure.

OMF exports are `aspect_find_command`, `aspect_find_sensitive`,
`aspect_find_insensitive` and `aspect_find_duplicate`. It reads
`aspect_set_findcase_value` and writes `aspect_find_found`. The application must
provide **near**, same-DS `aspect_find_alloc(size)` and
`aspect_find_free(pointer)` ownership. A far heap pointer is incompatible.
`aspect_find_upper` must select the actual native9128 string uppercase helper.
Existing string/option/integer-destination readers, strlen and program_strcpy
supply the other interfaces. Valid ASPECT strings fit81bytes; that does not make
the native CRT or malformed pointers generally bounded.

## SWITCH and CASE behavior

[src/aspect/case_commands.asm](../src/aspect/case_commands.asm) recovers
SWITCHD372..D39F (45bytes) and CASED39F..D3F2 (83bytes). Original dispatcher
opcodeB8 reaches SWITCH through resident C0B7; opcode0F reaches CASE through
CBA3. These mappings are derived from the pinned215-word handler table and
original overlay stubs.

SWITCH reads the operand token, stores shared E38C lookahead, computes its signed
remainder modulo10 and stores the low type byte at E376. Zero chooses a string:
the near reader and actual strcpy fill the81-byte E322 snapshot. Other remainders
choose the integer reader and store a word at E374. It then executes the native
DWORD jump. These are shared globals, not a nested-switch stack. A later SWITCH
overwrites the snapshot; complete original compiler treatment of nested SWITCH
is outside this component.

CASE first reads its DWORD mismatch target. String cases compare E322 with the
next string, using native93DE strcmpi when SWITCHCASE is zero and9476 strcmp
otherwise. Integer cases compare words and ignore SWITCHCASE. A mismatch seeks
the saved32-bit target; a match continues after the operand. Native malformed
token behavior, unchecked strcpy/near pointers and failed-seek handling remain
visible. The controlled failed-seek callback returnsFFFF; CASE does not invent a
local recovery or new error check.

OMF exports `aspect_case_switch` and `aspect_case_compare`. The application must
bind `aspect_case_type` (byte), `aspect_case_string` (81bytes),
`aspect_case_integer` (word), `aspect_set_switchcase_value` and the existing
`aspect_operand_lookahead`. Existing native operand/string readers, flow DWORD
reader/jump/seek, program_strcpy, program_strcmpi and aspect_string_strcmp provide
the called services. Integration must bind the SET setters to these same words;
unused parallel flags would not implement the settings.

## Evidence and checks

The public [hash/range ledger](../standalone/fixtures/aspect_find_case_native_units.json)
contains six units totaling401bytes, original coordinates, hashes and REA IDs.
All units match pinned PCPlus2.01 SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Normal builds read only public source and that ledger; original comparison is a
separate optional operation.

```sh
./tools/dev --command python standalone/build_aspect_find_case.py
./tools/dev --command python standalone/check_aspect_find_case.py
# Optional static comparison with an ignored, locally retained original:
./tools/dev --command python standalone/check_aspect_find_case.py --original PATH
```

The source-only check passes2,642 CPU cases, executes all199 instructions in the
six recovered units and visits390 instruction addresses including the real
source CRT, SET, flow and dispatcher helpers. It checks DS=SS, near/cdecl stack
balance, preserved BP/SI/DI and IF/DF. Allocator/free, operand/FILE and loader/UI
boundaries remain explicit. The component builds relocatable OMF objects as well
as exact flat units; it does not claim an actual linked DOS application run.

Key fresh REA observations are FIND
`ev_a8e6f63aa7559b03f5f26fa46b77410207bd2a79f0894e44b77adb78d8ece4aa`,
insensitive search
`ev_1d1b0693dbd5f3d63692385c2e48c78594874e352426a5b6f585328dcc12bd64`,
SWITCH
`ev_5da52d37cfc90f6d0817abfa8954c91290e806efc2384a3c70527cd9a6857d22`,
CASE
`ev_40a376dd122d0a0899897fad9b455bb17ac04ea98f9db09e043bf78aa589a3bb`
and defaults
`ev_7f2a37333c76fe8f326ecc36a6ef20a640284f710c20b9e47a19c3288aa55d92`.
Private cumulative bundles remain under `analysis/aspect-findcase/`. An initial
static seed lacked the load-segment adjustment and failed to identify FIND;
that attempt is retained. Corrected static-only seeds were analyzed, never
executed. No REA session remains open. These observations do not establish an
exhaustive absence of indirect consumers or close any full-application gate.
