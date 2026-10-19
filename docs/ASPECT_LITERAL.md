# ASPECT compiler and literal recovery

The first source-built ASPECT component is a bounded nonempty literal payload
codec, built as an8086 DOS diagnostic. It reproduces 44 payloads from the original
compiler and matches 725 executions of the original emitter's instructions.
It does not yet compile a script or execute ASPECT in the terminal. F13 remains
open for the complete compiler, VM, recorder and application services.

The original local `ASPCOMP.EXE` identifies itself as compiler1.01; its SHA-256 is
`5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a`.
The original is retained privately. The public
[compiler probe](../standalone/aspect_compiler_probe.py) generates only
source-owned synthetic scripts and runs the original compiler in an owned DOS
directory. Generated ASX files are never executed by this probe.

## Evidence and implemented boundary

| Evidence | Covered behavior |
| --- | --- |
| 91 complete compiler probes | 73 accepted,18 rejected; DOS return class, diagnostic and ASX existence agree |
| 44 frozen literal vectors | Ordinary/repeated literals, comments/blank lines, changed positions, waitfor/conditional/procedure contexts, lengths through80, caret text, TAB and CP437 high bytes |
| REA/Ghidra12.1.2 | Verified DOS MZ import, source chunk reader, literal emitter, output wrappers and unsigned remainder |
| 725 native/C comparisons | 44 compiler vectors,169 DWORD boundary combinations and512 deterministic random contexts; original emitter/remainder instructions execute unchanged |
| 52 native first-pass cases | Count n+2 with no output or input transformation |
| 2,080 maintained host checks | Exact vectors, roundtrips, truncation, malformed length/stride/parity/NUL, alias/capacity guards and atomic failures |
| 1,403 DOS diagnostic checks | Actual DOSBox-X8086 execution, exact vectors/truncations, near-pointer wrap/alias checks and DWORD wrap |
| Fresh source-only rebuild | 65 outputs byte-identical, including the new diagnostic, with originals/install/REA/build outputs absent before compilation |

The native CPU test intercepts only CRT strlen, fputc and fwrite with buffer
semantics. It executes original functions22A9,2230,2413 and698E, checks their
entry counts, rejects unexpected code/interrupts, and verifies unchanged code,
stack/callee registers and DS=SS. This is isolated compiler-function evidence;
the 91 DOS runs supply separate complete-compiler observations. DOSBox-X's8086
model is experimental and is not physical hardware validation.

The frozen [ledger](validation/aspect-literal.json) binds source/tool identities,
native code fingerprints, private evidence hashes and per-case oracle outcomes.
The complete REA bundle remains private under
`analysis/aspect-compiler/rea-compiler-complete.json`.

## Literal payload format

The compiler's nonempty literal marker is AA. The codec operates on the payload
after that marker; `P` is the absolute ASX byte offset of its length byte.
`L` is the compiler's32-bit source-read counter. The reader calls fgets with a
256-byte buffer and increments after a successful read, so overlong source
lines can span multiple counted chunks. An arbitrary text editor's line count
is not a complete source-map contract; include/source-context handling still
needs full recovery.

For tested quoted literals, length80 is accepted and81 is rejected with C043.
The payload uses these recovered algorithm constants:

```text
T = B3 35 0B C7 47 29 1D FB 1F 7F 05 59 17
q = P & 1
s = 1 + (uint32(P + L) mod 12)
payload[0] = uint8(B3 + n)
payload[1] = (q << 7) | (n + s)
for j = 1..n:
    k = (j * s) mod 13
    d = -T[k] if (k + q) is odd, otherwise T[k]
    payload[j + 1] = uint8(text[j - 1] + d)
```

This explains why adding a comment or an earlier command changes the encoded
string. The decoder recovers n and s from the two payload bytes and uses P for
parity. It needs no source file, but this encoding is not an integrity check.
Ciphertext may contain NUL; decoded literal bytes may not. The output is raw,
length-delimited bytes, with no added terminator or caret/control expansion.

The [maintained C API](../src/aspect/literal.h) limits this contract to nonempty
1..80-byte payloads. It validates capacities, DOS near spans and disjoint input,
output and result objects. Failure leaves both outputs intact. An empty literal
uses the distinct observed token pair6E13, which this payload API does not parse.
Whole-ASX parsing, token semantics and runtime string-variable limits remain
separate work.

Relevant retained REA evidence:

| Finding | Evidence ID |
| --- | --- |
| Verified import:1536-byte header,67250-byte loaded module, no appended overlay | `ev_df860824f49b912af4c26a4c5c977691f2ab76032e56af89aeaa536f6179355f` |
| Literal emitter at1000:22A9 | `ev_ef491f3d04c017ef1a539ed89067257c450b956dc5e5d2c4c63d38d949713f23` |
| Emitter assembly | `ev_04d6a63f254594587ae6e32252d443bb8c5195eda2b16b13c44bc758623abd29` |
| Source reader at1000:2C2D | `ev_40174f7042c828df70350ab5decfea0766ba08809ddf260ecda16ea10382575b` |
| Unsigned DWORD remainder at1000:698E | `ev_a62c625dd8392116f6ce77b8f8bd455478630ae09316d7d9ce4829b33eb2e406` |

The table's original file offset is1057C, mapped through the measured compiler
image/data segment. Ghidra pseudocode is interpreted evidence; the assembly,
native instruction replay and compiler output independently corroborate this
specific reconstruction.

## Build and reproduce

```sh
./tools/build aspect-literal
./tools/build test-aspect-literal
```

These use maintained C, the pinned Nix toolchain and frozen outputs of our own
synthetic scripts. They do not read the original compiler, install or REA data.
`make all` includes `LITERAL.EXE`; the interactive terminal remains unchanged at
SHA-256 `731418bde8f3264d5f6c987195eb54b20c86a2981259ea1c721ba252e3c9a776`.
The component's executable is
`bcd47845d6bea3a692599323095f29460a8dbecd15d57ecbd47f5c1358c5c1f2`.

Optional original-dependent checks, kept separate from ordinary builds:

```sh
./tools/dev --command python3 standalone/aspect_compiler_probe.py \
  --output analysis/aspect-compiler/corpus-new
./tools/build test-aspect-compat
```

The compatibility target creates a new native evidence directory on each run.
The probe's original compiler is supplied locally and checked by SHA-256; it is
not downloaded or distributed. A first historical probe had failed-case return
files truncated by conditional redirection; those fields are excluded from
success evidence. The current probe explicitly checks return classification.
The earlier PROFILE.ASP fixture contains literal backslash-r/backslash-n text;
it must not silently be treated as these CRLF source files.

## Remaining application work

The corpus also establishes selected output patterns for serial settings,
numeric operands, procedure calls and control flow. Those observations do not
establish full instruction semantics. Next work must recover the application's
ASX loader and dispatch, operand/value formats, call/variable state and native
command bindings, then implement the full source grammar/compiler and serviced
VM. Startup/manual/directory/meta-key invocation, recorder, diagnostics,
cancellation, floating runtime and terminal scheduling remain required. No
F01–F16 whole-application gate closes with this component.
