# Experimental GET compiler profile

Both maintained compilers now have an explicit opt-in for ordinary ASPECT GET.
The profile matches the frozen original ASPCOMP1.01 observations: writable
string, integer, long and float destinations, an optional atomic integer width,
and the observed optional comma syntax. The default host compiler still refuses
GET; the default DOS compiler remains byte-identical (`ac58a8a1…`). The selected
package and installed machine are unchanged. F13 remains open.

The compiler test reuses 81 original observations (28 accepted, 53 refused) and
adds 81 uppercase/CRLF/tab presentation variants. Both frontends match all 162
outcomes and every accepted complete ASX byte sequence. Actual DOS8086/FPU-off
execution covers 324 compilations: the experimental compiler plus default
refusal for each source. Failed compilations preserve existing output and leave
no publication temporary/backup files. This is compatibility with the recorded
corpus, not a claim about every original grammar production.

The [full interpreter](ASPECT_GET_VM.md) test now supports
`--get-compiler-dir`. Five cases use actual DOS-produced ASX, compared byte for
byte with host output: string, integer, long, cancellation and float refusal.
The malformed EOF case deliberately retains authored bytecode. The larger
capability22 keymap parent passes all six cases, including FOPEN across string
GET with exact `BEFORE|LoC42` file contents, restored terminal ownership and
continued serial interaction. The interpreter and parent binaries remain
`54590fd3…` and `b25fe6d2…` respectively.

The compiler accepts float destinations because the original compiler does;
the current interpreter explicitly refuses floating GET with error4. Runtime
width admission remains bounded at 0..80 even though the original compiler
accepts wider numeric constants. Positioned/sibling modes are not enabled.
Local, parameter and S0 destinations have compiler evidence; this checkpoint
does not establish their complete attached-runtime behavior.

The isolated public-source proof rebuilds both compilers, both interpreter
profiles and the full parent, then repeats grammar, compiled GET, ordinary
compiler/executor, UART, CLI, file and MZ checks. It uses no original application,
private configuration, prior objects or ancestor Git. Exact identities, report
hashes and limits are in the [receipt](validation/aspect-get-compiler.json).
Attached parent tests use DOS386/UMB and 640KB conventional memory with an owned
synthetic modem peer. They do not establish physical Boca/SPA2102/SynthModem/BBS
acceptance or ordinary8086 full-parent memory admission. GET scripts are compiled
before the parent starts in this matrix; simultaneous parent/interpreter/compiler
memory admission remains open.

```sh
python src/aspect/compiler.py --get SOURCE.ASP -o SOURCE.ASX
./tools/dev --command python standalone/build_aspect_compiler_dos.py \
  --get --output build/my-get-compiler
./tools/dev --command python standalone/test_aspect_get_compiler.py \
  --compiler-dir build/my-get-compiler \
  --default-compiler-dir build/my-default-compiler --output build/my-get-check
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/PARENT --child-dir build/GET_CHILD \
  --get-compiler-dir build/my-get-compiler --output build/my-get-vm \
  --stream-probe --allocation-probe
```

`--get` is a host CLI/build flag. The resulting DOS ASPCOMP uses its existing
source/output command line. Python callers select `compile_source(source,
enable_get=True)`. Do not pair compiler-produced GET with the default interpreter
or deploy the experimental child alone under the installed capability20 parent.
[Repeated GET and EXECUTE](ASPECT_GET_LIFETIME.md) now have two additional
full-parent scenarios. Remaining gates include broader lifetime/error coverage,
broader event/error coverage beyond the [WHEN action cases](ASPECT_GET_WHEN.md) and
[divide/cancel retirement](ASPECT_GET_WHEN_ERRORS.md),
field policies,
floating support, full feature/memory co-residency and package/hardware admission.
