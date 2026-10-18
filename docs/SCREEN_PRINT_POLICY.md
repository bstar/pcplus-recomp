# Screen-print policy and source evidence

CEAC is the transient CSI private-prefix flag, **not a saved printer policy**.
The analyst name `print_copy_policy` in the exact screen-printer module denotes
that same original address; live integration must alias it to `ansi_private`,
rather than allocating a separate setting. Its parameter4/5 branches inspect
that private-prefix flag.

This investigation reused retained REA exports and the SHA-verified original
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
No original application, private PRM file, BBS session, media write or new REA
session was used. Existing exact modules provide the executable evidence; this
document adds no new recovered-byte count.

## Prefix and media-copy behavior

The native escape entry EDB9..EDC4 clears CB5C(parameter count), CB3C(first
parameter), CEAC(private flag) and CEE2(secondary prefix) before reading a new
CSI command. Parameter reader12:E46E..E473 recognizes `?` and sets CEAC=1.
See `reconstruction/ansi/{escape,parameters}.asm` and retained
`analysis/pcplus-overlay-anchored-12/functions/0x1e3f2-asm.json`, Evidence
`ev_51d7b0bb004dd314aa1b32ea9d4b08135fbc599a9da23b2309fca78ff59fda92`.
The source was also exported in earlier retained sessions under the EvidenceID
in the maintained module's header; these are separate observations of the
same original instructions, not different semantics.

Recovered dispatcher12:E9D8 calls E084 for final byte69h, `i`. Its input is the
current parsed sequence, with this behavior:

| Sequence | Native result |
| --- | --- |
|`CSI i`, `CSI 0 i`, `CSI ? i`, `CSI ?0 i`|Selected screen print E3CA|
|`CSI 1 i`, `CSI ?1 i`|Print current row E2F8(mode3)|
|`CSI 4 i`|No action|
|`CSI ?4 i`|Force printer_enabled3988=1; call1A76 to disable and close shared8FF0|
|`CSI 5 i`|Enter dedicated-print controller12:D0D0|
|`CSI ?5 i`|Force3988=0; call1A76 to enable and open PRN|
|Other values|No action|

Multiple parameters execute consecutively. Repeated `?5i` opens again without
first closing the existing FILE; repeated `?4i` can pass its stale FILE to close.
These are native unchecked behaviors, not recommended idempotent ownership.
The exact365-byte screen-print diagnostic compares38 linked and38 original
instruction cases, including both CEAC values, ordered4/5 lists and ignored
parameters; see `build/print_screen/checks.json` when built locally.

## Runtime print flags, reset and configuration

| Address / canonical alias | Meaning | Full-reset value | Set/reset mode |
| --- | --- | --- | --- |
|3980 / modes_value_3980|Append formfeed after selected screen print|1|18h ->1;18l ->0|
|3982 / modes_value_3982|0=full terminal rows; nonzero=scroll region|0|19h ->0;19l ->1|
|CEAC / ansi_private|Current CSI `?` prefix|Cleared at each new CSI|Parameter reader sets1 for`?`|

The `h`/`l` suffix in the table means the CSI final byte, not hexadecimal.
Mode18/19 branches DF50/DF58 and E056/E05E are **not locally gated by CEAC**:
ordinary `CSI18h/l` and private `CSI?18h/l` both change formfeed, and likewise
mode19 changes full/region selection. Both mode handlers return before any
parameter processing when their existing DS904C gate is nonzero. Do not bypass
that gate by inventing separate live flags. Mode evidence is retained in
`reconstruction/modes/provenance.json`: set handler
`ev_8806c34ee3e415d806b020a85fb83f0d3fc246d8ecca9e69b8d946a8e9522f36`,
reset handler `ev_a1760badbd5de19b96d1f92d716efe7338c29f5dc3ae8f18acc2586c11627625`.

Resident20A4 full reset clears3982 at22CB while AX=0 and sets3980 at22E7 after
loading AX=1. Evidence `ev_e5cd72a52055be74334ffea1e1932bcb550cfad7418e7838b05732492d963404`
in `analysis/pcplus-main/functions/0x120a4-asm.json` and exact
`reconstruction/terminal_reset/reset.asm`. The reset routine has a smaller
partial-reset path: these defaults belong to the full reset slice and must not
be claimed for every invocation regardless of its argument/control path.

These addresses lie outside the proved1264-byte PRM image DS1B84..2073. The
examined source establishes reset/mode runtime state, not direct PRM offsets
for either flag. Loading unknown private PRM bytes into these aliases would be
unsupported. Live source-owned initial state can use full-reset defaults and
existing mode handlers. A separate user preference, if added, must be labelled
a maintained setting rather than a recovered PCPLUS.PRM field.

Full print is rows `[0,334C)`. Region print is `[CE0E,CE3A+1)`, using shared
scroll-top/bottom aliases. The screen writer emits every column0..3258, then
CR/LF and flushes per row; no trailing-space trimming. Native selection calls
36FC for optional FF **after** its screen writer closes8FF0. A checked live
owner should send FF before its own checked close and preserve the source
flags' meaning without reproducing the stale FILE use.

## Dedicated-print boundary is substantive

Retained12:D0D0, Evidence
`ev_e54a45172d907f37b39b7223686bad0d0a773def52c44fa869371b05450501dc`,
is a roughly416-byte modal controller, not a default toggle callback. It saves
cursor/display state, displays the verified `DEDICATED PRINT` resource at
DS2B6C, opens PRN, polls keyboard and RX, and forwards bytes through36FC.
It discards dequeued NUL and DEL; it interprets buffered escape sequences with
profile-dependent gates8FE8/9004 and a special terminal-ID1Fh (31 decimal) comparison.
With8FE8 enabled, its buffered sequence logic recognizes `[` and decimal4
before final`i` to leave controller mode. Other profiles have distinct exit
rules; two consecutive exact Escape keyboard words also exit, and ordinary
keys are transmitted throughAB0B. Exit restores cursor/display and closes the
shared FILE unchecked. Its escape buffer, blocking waits and unchecked CRT
ownership have not been recovered into a safe live service here.

Therefore unprefixed `CSI5i` cannot honestly be treated as equivalent to
private `CSI?5i`. A first live subset can support selected/current-row printing,
private4/5 stream ownership and modes18/19 while making unprefixed5i an explicit
unsupported boundary. Silently ignoring it or reporting dedicated printing
success would conceal missing behavior. A future maintained dedicated owner
needs an explicit exit grammar, bounded buffering, hardware servicing and
checked lifetime, while retaining the full-application feature gate.

## Local binding investigation

Alt-L(scan26h) is proved stream-toggle1A76. Alt-G(scan22h) is the separate
screen-file snapshot1310. **Alt-P(scan19h) is not proved screen printing.**
The recovered dispatch table maps19h to134C. SHA-verified resident134C is a
near jump toB9DF; the retained complete trampoline manifest mapsB9DF to
overlay20:EFDE. Its saved-window/menu routine is retained as
`ev_6017ca816dca0ac4acb05d54de7182870c4f5db9e3563e36118da69d1d338a19`
in `analysis/pcplus-overlay-anchored-20/functions/0x1efde-asm.json`.
It does not directly call E2F8/E3CA. No trampoline in that manifest targets
E2F8 or E3CA. Searches of retained exports found their direct calls inside
E084/E3CA only. This bounds the evidence; it does not prove that no indirect
menu/script/BIOS route exists anywhere in the original application. A new
local screen-print shortcut must be presented as a maintained binding until
its original caller path is established.
