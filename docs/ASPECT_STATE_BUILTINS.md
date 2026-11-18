# ASPECT FROMDDIR and MONO

The opt-in `aspect_state_builtins=True` interpreter implements the original bare,
read-only integer operands `FROMDDIR` (selector24) and `MONO` (selector26).
Both source compilers accept their original syntax and reject declarations,
writable targets, string use and function-call syntax. The
[native provenance](../reconstruction/aspect_state_builtins/provenance.json)
binds the four-byte getters, original callback slots and overlay16 thunks.
Normal application builds use source only; original byte comparison is a
separate optional check.

`FROMDDIR` is the full retained directory-origin WORD, not a Boolean or an alias
for `$D_ENTRY`. Opening the directory clears it, including a canceled browse.
A nonblank automatic directory script assigns the entry before invoking the
loader, including when loading subsequently fails. Manual Alt-F5 clears it
before the filename prompt, even when canceled. A KEY-kind0 macro and script
`EXECUTE` retain it. Child return, disconnect and renderer lifecycle do not
clear it. The original direct writes and their bounded search limitations are
recorded in the [builtin audit](ASPECT_BUILTIN_REMAINDER.md).

The maintained parent has a separate initially-zero `_aspect_fromddir` WORD.
The startup directory selection, interactive directory entry and both manual
prompt paths clear it. Both legacy-record and adopted automatic-script paths
assign the current context's full entry. Shared `terminal_script_start` does
not reset it. `_script_directory_entry` still describes selected metadata and
has a different lifetime.

`MONO` reads `_display_rows_mono`, the existing physical display cache populated
by the recovered geometry service. The original clears it and increments it
when the low byte of BDA CRT-controller port0040:0063 equalsB4. It does not read
the emulation profile's `attributes_monochrome` flag or reprobe hardware on
each operand read. The current parent renderer admits color mode3; this getter
does not add monochrome terminal rendering.

The attached profile requires the complete HITKEY/terminal-query profile and
uses renderer capability26. Read-only op29 indexes9/10 return the origin and
physical-display WORDs through the existing tagged-byte protocol. The client
publishes its cache only after both bytes and client checks succeed. Existing
ownership/authentication gates remain required. A standalone runner without a
parent or diagnostic fixture returns explicit unsupported status before
changing an assignment target. Disabled builds retain nine cache words and
their previous operand routing.

Validation covers the following distinct boundaries:

- Exact getter bytes, original slots/thunks and131,072 CPU cases, exhausting
  both WORDs with preserved registers, flags, DS=SS, stack and independent
  origin/display/profile/entry canaries.
- Twenty frozen original compiler cases:12 accepted,8 rejected. The full
  source-built DOS compiler suite passes3276 cases (1325 accepted/1951 rejected).
- Actual DOS8086 VM diagnostics:1424 cases/35718 checks with all composed
  features; the state-only profile passes1145/27598 and disabled control1137/27339.
  Positive fixtures cover raw values and signed long promotion, cache canaries,
  and unavailable-backend failure before destination mutation.
- Actual DOS8086 C-client checks pass467 cases/3132 checks for indexes0..10,
  including both new words, refusals at either byte, client/owner faults,
  unchanged destinations and retry. The previous profile remains435/2766.
- The linked parent passes156 CPU cases and11 child handshakes. These execute
  the actual startup, automatic-script, manual-prompt and macro bodies, full
  state replies, authentication and source canaries. Five actual geometry
  producer cases feed the getter, including ports12B4/FFB4, then change the BDA
  and profile flag without changing the cache. External BIOS, admission,
  chooser, recording-inspection and loader boundaries remain explicit models.
- Supplemental DOS8086 tests pass47 cases/21432 checks for the optional
  directory view and adopted-script hook. Actual rendering, incremental reader
  and the unchanged first automatic-script ASM function execute; filesystem,
  adopted-name and loader boundaries are controlled. Production optional bank
  linkage and live adopted-resource routing remain unproven.
- Full-parent source compilation, GET, held allocations and source `EXECUTE`
  pass two DOS8086 workflows/105 checks, including five paired state guards.
  Nested Help, held FILE/handle, frame, cursor and allocation checks pass63.
- A cold export of1075 source files, without originals, old objects or ancestor
  Git, reproduces the parent, child, compiler, modules and Help bytes and
  repeats those source/GET and Help workflows.

The first parent attempt published26 from assembly but compiled its C client
for25. The actual DOS source-start failure and four linked C admission
comparisons are retained as a negative counterexample. Both C and assembler
feature flags now agree; the subsequent DOS and cold-rebuild checks pass.
Review also found that a refused direct Alt-F5 cleared origin before recording
ownership admission. It now clears only when the prompt is admitted, matching
the menu path. Both refused paths and allowed/canceled prompts have linked
regressions.
The harness's preliminary `FINAL FAIL` on a regenerated `NEXT.ASX` is replaced
by its explicit source-compilation checks; the final105-check receipt passes.

The new parent retains DGROUP65520 and its8192-byte stack, with334 resident
code bytes spare. The overlay child uses65380 near-code bytes (156 spare),
DGROUP40640 and its8192-byte stack. Disabling the feature reproduces the prior
HITKEY parent executable and all four modules byte for byte. The reviewed
command-menu optimization options remain unchanged.

Evidence paths and identities are recorded in
[the validation receipt](validation/aspect-state-builtins.json). A capability26
contract fixture is staged for validation; it is not a committed-source release
or a replacement for the prepared capability24 candidate. Fresh full-package,
BBS and hardware qualification remain separate gates. No installed selector,
physical DOS machine or private service/configuration is changed.

The six Host builtin services stay with the final Host stage. Complete ASPECT,
other emulations/protocols and the full F01–F16 application requirements remain
open; this checkpoint does not complete the reconstruction.
