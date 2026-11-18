# Remaining recovered ASPECT builtin tables

After the terminal-integer checkpoint, nine services in the recovered integer,
long and string callback tables still lack compiler/runtime bindings. This is
an inventory of those tables, not the remaining work for the whole language.
The maintained compiler maps and `runtime_bridge.asm` remain authoritative for
implemented dispatch. Reserved procedure keywords alone do not implement an
expression operand.

| Kind/selector | Operand | Overlay16 getter | Observed read or operation |
| --- | --- | --- | --- |
| Integer11 | `$H_LEVEL` | D9E3 | Sign-extends the byte at DS5B38. |
| Integer24 | `FROMDDIR` | DA18 | Reads the full WORD at DS4AFE. |
| Integer25 | `HITKEY` | DA1C | Calls resident651A non-consuming peek and normalizer77D2. |
| Integer26 | `MONO` | DA24 | Reads physical display flag WORD DS7A86. |
| Long2 | `$H_BAUD` | DA72 | Uses WORD index DSE458 in DWORD baud table DS3270; returns DX:AX. |
| String15 | `$H_ELAPSED` | DAEB | Returns shared pointer DS5B1A. |
| String16 | `$H_NAME` | DAEF | Returns shared pointer DS5AE2. |
| String17 | `$H_OFFLINE` | DAF3 | Returns shared pointer DS5B0E. |
| String18 | `$H_ONLINE` | DAF7 | Returns shared pointer DS5B02. |

The four integer getters have retained REA observations:

- `$H_LEVEL`: `ev_62c3781124117a26634c7eac6b586776b3f0c131ef8349c5a0ce4310b161db9f`.
- `FROMDDIR`: `ev_96a50639e4f0c4935b6840338745f63fdf6291ee495118fc722560e35e3d7e1e`.
- `HITKEY`: `ev_172f3e6ad25ed8638f5eb8f48e91838efeef253cd2edb73b1d08d430616d3c22`.
- `MONO`: `ev_0a3f743642ba0d7946d987ba75937b67d1d5cdbc1c7ce217c88f7ff417c17809`.

These refer to the anchored overlay16 analysis image SHA256
`e14871502dba5f55646eb6184cf488c216381e6eda2ca47227a06934592b8302`,
derived from original SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Static table/thunk inspection confirms the selector bindings; it does not
establish application lifecycles. Original/analysis files stay outside normal
application builds, and synthetic analysis executables are never executed.

Thirty actual DOS8086 original-compiler probes confirm the three bare names
`HITKEY`, `FROMDDIR` and `MONO`:18 accepted,12 rejected. Assignment, case folding,
long arithmetic, conditions, locals and integer parameters are accepted;
string use, assignment targets, declarations and function-call syntax reject.
Declarations produce C028, "Invalid use of reserved word", rather than the C025
identifier error of the `$`-prefixed terminal operands. The retained private
draft/report is SHA256
`e9f8e64d04e688561602be1a364bf6e1dd1c45aef511d6c5b9b4d2e2c577ff10`,
under `analysis/aspect-nonhost-builtins-20261118/`. The maintained compilers do
not yet implement these operands; this oracle is not counted as a passing
maintained compiler regression.

`HITKEY` has recovered dependencies in `reconstruction/keyboard/core.asm` and
the caller-cleanup adapter in `src/keyboard/api.asm`. Peek evidence is
`ev_9bc44de1285653267fe1e2c64a2f8d8f3fffa0fb3fcccfe61137d4b9fbc4fcd5`;
normalizer evidence is
`ev_cb670ed8c108fd2f8a4d03d1d83765074271c3cae5e31f2e0ac94f3c59873699`.
Recovery must preserve repeated non-consuming reads, empty input, enhanced E0
words and mouse-peek behavior. `runtime_when_key_ready()` adds modal suppression
and returns availability, so substituting it would change the operand.
The normalizer can retain full BIOS words. The getter performs one peek and
normalizes that one result; a future parent service must preserve this single
observation when a hardware key arrives asynchronously. Two independently
peeked byte responses could combine different key states and are not equivalent
to the existing terminal-state query contract.

`FROMDDIR` needs the launch-origin lifecycle. The original directory producer
clears DS4AFE on directory entry and sets it for a nonblank automatic script
(`ev_186cf7e819989310ab103a002a93c6fd62517af38d1568ce7d4d0885a258baa9`).
The current `script_directory_policy` also exports retained selection for manual
launches. Neither `$D_ENTRY` nor an unconditional Boolean alias recovers this
word's behavior.

`MONO` must use DS7A86, not `attributes_monochrome` at original DS8FF6. Its
producer examines the BDA CRT-controller port's low byteB4
(`ev_f023afd9e2ef7182dbaf48f2f4693299a3627322109a691056e99c4ce4e7eb6c`).
The current renderer admits color mode3; supporting the getter must distinguish
that admitted scope from original monochrome display support.

The six Host operands stay with the final Host stage. Their getter mechanics
do not prove session initialization, refresh timing, buffer validity or baud
index admission. The retained long observation is
`ev_da517cc1aca115a930ca4470f904cb838714523846db7b8f6991b13ed54c8e24`;
the four string observations, in table order, are
`ev_eb5612a9b2e27c965d27ce7c8793a6575e14d5b85dc1d72caf155d4a9a9dd825`,
`ev_75c91807f46a2ef51ef220d471e2dc609f38d200fd7405800e531d39797c665e`,
`ev_991c28407f4029c11504cd0a9fd9a86d5c5d2c8841c1a349928a7ba147cfa670`
and `ev_1585fdcceeb45fb8fde1227bd76ec20a5234724048c794c7a34122381a84a56a`.
