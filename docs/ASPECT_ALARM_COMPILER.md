# ALARM compiler checkpoint

Both maintained compilers now emit the recovered ALARM wire format. All 39
saved original compiler outcomes match: 17 accepted sources produce exact ASX
bytes and 22 invalid sources reject. Another 39 presentation variants pass in
both the host compiler and actual DOS8086 CLI. This adds compiler support;
ALARM execution is still awaiting VM and parent-policy integration.

`ALARM` emits opcode01 and absent-operand byte00. `ALARM value` emits opcode01,
present byte01 and an atomic integer reference or compact constant. Global,
local and parameter integers and integer builtins are supported. `FOREVER`
remains an ordinary integer builtin; it is not WAITFOR's special marker.

Commas, parentheses, compound expressions, extra operands and wrong types
reject. Unsuffixed `-32768` uses the existing checked word-argument reader,
which admits that boundary even though its positive token is classified long.
Positive32768/65535 and long-suffixed or floating constants reject. Negative
signed values compile as in the original. Runtime0..32767 bounds must still
be checked when binding the native operand reader.

The [receipt](validation/aspect-alarm-compiler.json) binds current sources,
compiler identity, exact outputs, regressions and cold reproduction:

- All2225 maintained DOS compiler cases pass, with1693 API checks, owned
  allocation-failure cleanup, successful reuse and staged-publication rollback.
- The checked-stack suite passes2243 cases, including18 deep-expression cases.
  API checks use16KB stacks; the shipped CLI keeps24KB. Deliberate overflow
  controls establish that compiler stack guards are active.
- A24-file empty source export reproduces the exact compiler executable and
  repeats all78 ALARM cases. It includes authored frozen vectors, but no
  original executable, private configuration, previous object or Git metadata.
  It does not repeat the complete corpus or checked-stack suite.

Rejected DOS compilations preserve an existing destination and leave no
publication temporary/backup files. Case variants uppercase tokens, preserve
string literals and add whitespace without changing source line numbers.
The original oracle is an optional private provenance input to the freezer;
it is not read by ordinary builds or tests.

## Reproduction

Run through the pinned Nix environment. Each dedicated output must be new:

```sh
./tools/dev --command python standalone/check_aspect_compiler_dos.py
./tools/dev --command python standalone/test_aspect_alarm_compiler.py \
  --compiler-dir build/aspect-compiler-dos --output build/my-alarm-compiler
./tools/dev --command python standalone/check_aspect_compiler_stack.py \
  --output build/my-alarm-stack
./tools/dev --command python standalone/prove_aspect_alarm_compiler_source.py \
  --test build/my-alarm-compiler --output build/my-alarm-compiler-cold
./tools/dev --command python standalone/record_aspect_alarm_compiler.py \
  --test build/my-alarm-compiler --cold build/my-alarm-compiler-cold \
  --stack build/my-alarm-stack --output build/my-alarm-compiler-receipt.json
```

The [DOS platform component](ASPECT_ALARM_DOS.md) and recovered native alert
have separate evidence. The current interpreter does not yet execute ALARM;
no replacement package has been selected or installed for this checkpoint.
Next are operand/VM binding, current parent duration/sound settings, exclusive
key ownership during WHEN/receive rendering, code/memory funding and full
connection regressions. Physical acceptance and full parity remain open.
