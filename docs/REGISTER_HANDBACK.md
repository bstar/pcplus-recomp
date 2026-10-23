# Experimental ASPECT register handback

The optional register build retains the native ten integer words and ten
81-byte string slots when an external ASPECT child returns. This is a maintained
ASIO extension, not the original PCPlus helper protocol. It prepares storage for
the pending guarded HOOK integration; directory KEY kind2 remains disabled.

## Ownership and initialization

ASIO version7 adds four words to the version6 descriptor: exchange offset,
segment, byte count and invocation token. All four participate in the existing
input guard. The descriptor is58 bytes and may reside outside parent DS.
`parent_ds` still addresses the ring, translation table and directory record.
Old builds continue to admit only versions1–6.

The terminal owns1,734 initialized bytes in HOOK_CODE: phase/token/epoch/seal,
descriptor, an838-byte exchange and the830-byte accepted bank. It adds no near
DGROUP storage. The exchange contains magic, token, returned and seal words,
followed by20 integer bytes and810 string bytes. Parent APIs require the actual
application DS=SS, IF set and DF clear. The seal detects accidental damage; it
provides neither authentication nor isolation from another DOS program.

Preparation copies the accepted bank, clears the integer words and the first
byte of each string slot, and preserves the remaining string bytes. This follows
the recovered per-invocation initialization described in
[HOOK exchange](HOOK_EXCHANGE.md). The child restores the preserved tails after
its ordinary runtime reset. Its integer and string banks have separate linked
addresses; publication gathers them explicitly.

The child validates the exchange against the parent's allocation and known
descriptor/ring/table/record/render spans before UART acquisition. It attaches
only after acquisition succeeds. After its IRQ is released, it publishes bounded
strings and integer bytes, the seal, then the register returned flag. Ordinary
ASIO status/count/flow and returned follow.

Parent extraction checks immutable descriptor fields, token, returned flags,
ring count, carrier policy and bounded/sealed register payload. Extraction
distinguishes a validated successful child from a validated failed child. Commit
requires prior extraction and rechecks the payload; preparation alone cannot
authorize commit. The existing terminal handback checks still run before commit.
Only a successful child can replace the accepted bank. A failed child may return
valid serial ownership and data while retaining the previously accepted registers
and epoch. A failed child that did not initialize its interpreter may omit
register publication; a successful child may not. A malformed helper or failed
EXEC does not become a successful register return.

This distinction fixes a DOS regression found by the multi-invocation tests:
ASPECT resets registers before trying to open a missing script, then publishes
that cleared bank on exit. Previously the terminal accepted it despite the
child's failed exit. It now retains the accepted bank and still permits a clean
retry with normal serial continuity. This failed-child retention is maintained
policy, not proof of the original executable's behavior for every error case.

## Build and validation

Use the pinned Nix toolchain:

```sh
./tools/dev --command python3 standalone/build_terminal.py \
  --external-render --mouse --notice-sound --notice-input --aspect-keys \
  --directory-keys --process-bank --session-capture --session-projection \
  --session-baseline --register-handoff
./tools/dev --command python3 standalone/build_aspect_process.py \
  --notice-bank --notice-sound --notice-input --notice-help --help-resource \
  --serial-bank --register-handoff
./tools/dev --command python3 standalone/check_register_handoff.py \
  --output build/register-handoff-linked-new
./tools/dev --command python3 standalone/test_directory_key_bindings_dos.py \
  --process-bank --session-projection --register-handoff \
  --label register-script-new --case script --port 2
```

Each test output/label must be fresh. The linked checker runs the actual parent
and child far APIs, verifies calling conventions, and prohibits interrupts and
port access. It covers all bank bytes, invocation reset, damaged descriptor and
payload rejection, commit ordering, missing publication, invalid CPU context,
child admission and unterminated strings. It does not model DOS EXEC or replace
product routines. The DOS smoke test uses the actual terminal, ASPECT child,
UART/renderer and a synthetic serial peer; it does not inspect every returned
bank byte.

The current checkpoint passes924 linked input cases, separate COM1/COM2 DOS
script smoke sessions and fourteen8086 DOS register workflows. Both older terminal and ASPECT products match their
previous executable hashes exactly. The new ABI declarations are feature-gated:
exposing otherwise unused types changed Watcom's static symbol order, so merely
disabling calls was insufficient to preserve the older executable.

The fourteen workflows cover normal return, a damaged exchange token, a missing
script, a temporarily absent ASPECT executable, divide-by-zero, instruction-budget
exhaustion and confirmed abort, each on COM1 and COM2. A
source-built nested DOS observer captures86 pairs of parent owner and child bank
images. Checks cover all830 bytes, accepted epoch/seal, native invocation reset,
80-character strings, shorter assignment replacing a complete slot, failure
retention and clean retry. The peer sends a DSR query only after the final script
transmits its marker; the real DOS UART/parser/TX path must answer it. Hardware
register/vector restoration and unchanged configuration/directory accounting
are checked separately by the connection harness.

Integer bank A is exercised through explicit native operand fixtures: ten unique
global integer destinations emitted by the compiler are changed from tag8D to
tag65. Patch offsets and both operand values are retained. S0–S9 use ordinary
compiler support. This does not claim a new compiler syntax for integer bank A.
Observers only read the bank; the malformed-return fixture deliberately damages
one token. Missing-executable tests rename only the isolated test package copy
and verify that its original bytes are restored.

Run one workflow with a fresh label:

```sh
./tools/dev --command python3 standalone/test_register_handoff_dos.py \
  --label register-next --case missing-helper --port 2
```

Supported cases are `normal`, `bad-token`, `missing-script`, `missing-helper`,
`divide`, `budget` and `abort`.

An empty temporary tree containing only691 declared source inputs reproduces
six products byte for byte: terminal, its projection probe, ASPECT, DOS compiler,
settings editor and help resource. Admission rejects non-source extensions,
symlinks, traversal and original/install/build/analysis paths. It uses the pinned
Nix toolchain; original executables, disk images, prior objects and REA databases
are absent from the copied inputs.

Four additional8086 virtual-modem cases exercise DCD loss during native script
confirmation: `TX-No`, `CALL-No`, `CALL-Yes` and `XOFF-error`. The peer closes its
socket and DOSBox's modem changes carrier state. Checks cover actual child exit,
parser progress under the prompt, OFF-LINE status, JFT/owner restoration, framed
CALL behavior and the exact peer stream. These cases use the current register
build but do not seed and inspect a nonzero register mutation during the drop.
The partial PRM fixture explicitly initializes mouse scales for this product;
the first attempt's pre-UART fixture rejection is retained under ignored build
storage and is not a passing carrier result.

Run the clean-source proof and carrier checks with fresh output labels:

```sh
./tools/dev --command python3 standalone/prove_directory_keys_source.py \
  --process-bank --session-capture --session-projection --session-baseline \
  --serial-bank --register-handoff --output build/register-source-next
./tools/dev --command python3 standalone/test_aspect_abort_carrier_dos.py \
  --label register-carrier-next --product-root build/register-carrier-products-01
```

The carrier product root is an isolated mapping of current source-built terminal
and ASPECT products to the test's conventional product names, with exact source
and product hashes checked before execution. Its input files are under ignored
build storage; the test does not replace the ordinary products.

The [current receipt](validation/register-recovery-source.json) binds current source
hashes, linked binaries/maps/manifests, all raw observer/DOS fixture/capture
hashes and the older product comparison. The
[initial receipt](validation/register-handback.json) retains the earlier923-case
checkpoint; the [next receipt](validation/register-handback-dos.json) retains its
eight-workflow extension. Recreate the current receipt from completed captures using:

```sh
./tools/dev --command python3 standalone/record_register_handoff.py \
  --linked build/register-handoff-linked-04 \
  --dos-label register-recovery-smoke-1 --dos-label register-recovery-smoke-2 \
  --register-label recovery-1-normal --register-label recovery-1-bad-token \
  --register-label recovery-1-missing-script --register-label recovery-1-missing-helper \
  --register-label recovery-1-divide --register-label recovery-1-budget --register-label recovery-1-abort \
  --register-label recovery-2-normal --register-label recovery-2-bad-token \
  --register-label recovery-2-missing-script --register-label recovery-2-missing-helper \
  --register-label recovery-2-divide --register-label recovery-2-budget --register-label recovery-2-abort \
  --source-proof build/register-source-proof-02 \
  --carrier build/aspect-abort-carrier-dos/register-carrier-03 \
  --output docs/validation/register-recovery-source.json
```

## Remaining acceptance

This checkpoint does not establish full register/HOOK acceptance. Still required:

- Combined register mutation/carrier-loss and further malformed-helper,
  partial-publication and pressure policies. Current runtime abort/error cases
  and separate carrier recovery do not prove every combined route. The linked
  admission tests cover allocation edges, known overlaps and segment wrapping.
- Current Synchronet/ENiGMA interaction coverage for this optional build.
- Guarded HOOK routing, remaining native PRM fields, returned-settings staging
  and application, and composition with the exit/trap owners.
- Physical Boca/SPA2102/SynthModem and complete application acceptance.

The workstation tests do not establish physical modem compatibility, hardware
handshake/audio, or a14.4 kbps connection.
