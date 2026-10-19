# ASPECT dispatcher and loader investigation

The recovered dispatcher builds from maintained assembly into a standalone DOS
executable through the pinned Nix toolchain. Its224 bytes match the original
PCPlus2.01 resident CS:4B1F..4BFE inclusive. The linked diagnostic supplies
source-owned callbacks for every dependency. **This is not yet a script VM:**
actual opcode handlers, loader, expression evaluation, files, UI and scheduling
are still required before the maintained terminal can execute ASPECT scripts.

## Build and verification

```sh
./tools/build aspect-dispatch
./tools/build test-aspect-dispatch
# Optional private original executable; never part of ordinary build/test:
./tools/build test-aspect-dispatch-compat
```

`build/aspect-dispatch/DISPATCH.EXE` has SHA256
`68288f66c17e188bbbae1813594639dd88eae5e050a483ae91af764f6aff7b4f`.
The flat loop has SHA256
`d2006fe5dd53b6416aec915c9bd58b4ae1a11fc003aafef090279fa2d37520a6`.
The source-only check exercises590 CPU scenarios and3,616 assertions in actual
8086 DOS under DOSBox-X. CPU scenarios cover all215 slots with both ownership
paths, pause/wait/seek thresholds, service abort, failed open, EOF versus invalid
opcode, cleanup and state999 script restart. The optional private comparison
matches all224 bytes and all590 paired CPU scenarios. These exercise the loop
against explicit callback models; they do not test real215 opcode handlers.

The entry consumes two stack words with RET4 and preserves BP/SI/DI. DS=SS is
required. Source comments and builder callbacks document callee-cleaned versus
caller-cleaned backend arguments. OMF builds relocate external symbols; the
flat build keeps original addresses for the optional exact-byte proof.

The fresh source-build proof includes this diagnostic among66 byte-identical
outputs. See `validation/application-components-source-build.json` and
`validation/aspect-dispatch.json`. The interactive terminal binary is unchanged.

## Established original behavior

`standalone/inventory_aspect_vm.py` validates the pinned private executable,
MZ coordinates, overlay manifest, table bytes and trampoline mapping. The
215-word table at DS:4B08 contains48 resident targets and167 overlay targets:
3 in overlay3,6 in12,30 in16,62 in17,65 in18 and1 in19. This is a location
inventory; table membership alone establishes neither semantics nor reachability.

The dispatcher accepts indices00..D6. Outside that range, the native FILE
flags at offset6 select unexpected EOF107 when bit10h is set, otherwise invalid
command106. This is the EOF flag, not the separate stream-error flag. State999
closes the current script and restarts with the next name. Keyboard/service and
wait callbacks retain application dependencies.

The loader consumes the first ASX byte **before** dispatch. Original overlay2
D850 uses it as the number of81-byte far global-string allocations. The compiler
oracle independently confirms that numeric globals and procedure locals do not
contribute. The original loader does not validate this byte against the
compiler's128-string limit; arbitrary malformed headers are not established safe.
The loader's open/compile path also invokes ASPCOMP.EXE when appropriate; it is
not an original-free maintained compiler.

Two owned DOS baseline sessions compile and execute source-owned scripts using
the original application/compiler. The first observes helper call/return,
IF1 true selection and WHILE0 skipping; the second observes IF0/ELSE selection.
Both return to terminal interaction, answer an ANSI status request, transmit a
keyboard character and exit to DOS. They preserve the original application and
source install. These are original-runtime observations, not maintained-VM tests.

The declaration oracle's114-case and supplemental6-case runs establish:

- Each user global type accepts128 variables;129 fails C017.128 strings plus128
  integers plus128 longs compile together, with header128.
- Locals have a total128-variable limit per procedure across types. Separate
  procedures can each declare128 locals. Local strings/integers/longs contribute
  81/2/4 bytes to the D2 frame-size word.
- Local/global name shadowing fails C005; the same local name in separate
  procedures is accepted. Header probes compile but do not execute their ASX.

Earlier probes using reserved identifier TEXT failed C028. Their private
artifacts are retained; the114-case run uses USERSTR. Historical harness hashes
are recorded separately because the final harness adds six supplemental cases.

`standalone/inventory_aspect_keywords.py` follows the native compiler initializer's
18 table pointers,20-byte record stride and zero-name/zero-pointer terminators.
It finds637 records, including217 command records.182 nonmarker command names
represent178 distinct command tokens;29 directives use00 and6 preprocessing
markers useFF.37 VM slots lack a nonmarker command name. Command AA is STRCAT;
operand AA introduces encoded literal payload. Token meanings depend on context.
This inventory is not a complete grammar or opcode implementation.

## Evidence and remaining work

All private raw probes, output ASX and REA exports remain under ignored analysis
paths. `standalone/record_aspect_dispatch.py` validates current source hashes and
freezes sanitized summaries and evidence hashes without copying installed data,
compiler diagnostics or original resources into the public repository.

Retained REA evidence includes:

| Question | Evidence ID | Coverage |
| --- | --- | --- |
| Loader open/compile | ev_d7b6d1b1b0cda4408eed7653c42dd6ec108171417055a031f680b4d6f171cee5 | Static overlay2 D4D0 |
| Script state initialization | ev_8ff21649bd3d277b6ca23c7d15e7906e380bcad2d87b3318ecb71c9c666c3e01 | Static D770 |
| Global string header | ev_dbc3bcf3bb931cbd0cf28570a05d5156f682cfe62da94105e834a75d5fe3e749 | Static D850 |
| String release | ev_a2d880c716be2a76af6e9fe26d4135d05a4ab84aafe2d8240d904763b09c7a53 | Static D88E |
| Native end wait | ev_905383bd77df48ac8e3cb20cc751e7b4261fed54f625a46cd51ddf1eb53f2adf | Static resident4BFF |
| Interpreter service | ev_e69f84be549695784279cff37c14945e6dd5305b2b78065b2478e91d010c0915 | Static resident4DE9 |
| Invalid-command routing | ev_7f7450e801eb4f31c5b1f8065e8611768ea774888c0cd310ecffba64dde3b6ea | Static resident4F88 |

The latest three records are in private
`analysis/aspect-vm/rea-loader-dispatch-01.json`. Earlier loader records remain
in the retained anchored overlay2 exports. Static evidence does not imply runtime
coverage of those routines. Real handlers, complete loader/resource/error
lifecycle, compiler grammar/passes, recorder, FLOAT.RTE and live terminal
invocations remain open. F13 and every whole-application gate remain open.

The subsequent [global-string recovery](ASPECT_GLOBAL_STRINGS.md) implements the
101 native D850/D88E bytes separately, with616 CPU scenarios and705,369 linked
DOS assertions. It advances the loader's primitive layer and extends the fresh
source build to67 outputs. Allocation, error handling and full script execution
remain unresolved application services.
