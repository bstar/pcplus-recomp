# ASPECT input translation and parent policy

The later [connected-session checkpoint](ASPECT_SCRIPT_SESSION.md) corrects
selected-port handoff and connected-success return behavior. This input-policy
record retains the products and results measured at its own checkpoint.

Scripts launched from the terminal now inherit its selected input translation
table or seven-bit policy. COMGETC, COMGETCD, RGET, WAITFOR and WAITQUIET apply
the policy once. Unread bytes remain raw when returned to the terminal, which
then applies its own current policy once. The standalone runner uses identity
mapping unless a validated parent supplies a policy.

## Native mapping and application boundary

`src/aspect/receive_policy.asm` composes the original resident 4C74 mapping
routine with its 4C3C displayed adapter: 83 exact bytes, comprising 64 bytes
already recovered in `reconstruction/translation/receive.asm` and 19 adapter
bytes. The component passes 8,824 paired CPU scenarios, 424,036 assertions in
actual 8086 DOS, and coverage of all 37 native instructions. Its optional
comparison matches the pinned original. Fresh static REA evidence is recorded
in `docs/validation/aspect-input-policy.json`; analysis carriers never execute.

Native 4C74 selects an immediate or delayed raw read, returns negative words
unchanged, translates a valid byte once, calls the pattern monitor if enabled,
and then calls the renderer if requested. Both callbacks receive the mapped
byte, including NUL. Their register clobbering does not change the returned
value. Pattern monitoring is distinct from capture/logging.

The production child now uses that exact mapping routine above its cooperative
UART read. Seven-bit masking occurs at UART dequeue, before mapping. Its
private table is a snapshot taken before IRQ admission. Raw IRQ storage and
ASIO return storage retain all eight bits. RGET's maintained max0 safety guard
runs after translation: an 81st mapped CR is safe; an 81st mapped non-CR stops
before writing beyond the owned buffer.

Full native terminal rendering and WHEN dispatch remain unfinished. Production
selects display0 and leaves the pattern count zero; activating those unavailable
callbacks fails explicitly. The displayed 4C3C adapter is component-tested but
is not selected by production reads. This does not reproduce native ANSI
renderer continuation consumption inside a script. The previously documented
cooperative cancellation, bounded polling and max0 overflow corrections remain
maintained differences from the original.

## ASIOv2 handoff

The maintained parent/child descriptor remains 28 bytes. Version2 uses its
previous two reserved words at offsets24/26 for a parent-DS translation-table
offset and mode: 0 identity, 1 table, or 2 seven-bit masking. Modes0/2 require a
zero table offset. The guard additionally XORs both words. This interface is
source-owned; it is not an original PCPlus data structure.

Admission checks the child's actual DOS parent, MCB ownership and extent,
descriptor size/version/status, near and physical bounds, and disjoint spans
for the descriptor, 4096-byte return ring and optional 256-byte table. Rejected
descriptors fail before port I/O or handback publication. A rejected reopen
cannot mutate an active owner's policy. Version1 parents remain supported
with identity mapping and zero reserved words. A version2 parent requires the
new runner; stage the terminal and sibling helper together.

The resident parent validates live mode/enabled/mask consistency and stages
the policy in the existing descriptor before crossing into CONFIG_CODE. Its
far C helper does not call resident near functions. No parent DATA storage was
added: DS/SS remains 65,408 bytes, leaving128 bytes below the segment limit.

## Current verification

The independent actual DOS script suite passes24 cases/192 assertions. It
fixes expectations before execution and checks non-idempotent A→B→C maps,
mapped NUL/CR/high bytes, stale-table identity/seven-bit modes, both delayed and
immediate input, WAITFOR literal matching, quiet-line drains, both mapped81st
RGET boundaries and eight malformed descriptor cases. Returned bytes traverse
the actual terminal translation and UART dequeue code in an independent parent,
rather than a duplicate mapper in the checker. Earlier failed test-parent link
layout artifacts are retained locally.

Additional current evidence includes:

- Four actual DOS handoff/snapshot tests, plus six existing backend DOS tests.
- Fourteen linked backend groups/59 inputs and14 parent launch groups/55 inputs.
- Seven actual terminal Script workflows, including a loaded XLT and seven-bit
  profile, with serial restoration and resumed terminal input.
- All28 existing serial-script cases,15 receive cases and two owned local
  Synchronet/ENiGMA greeting cases on the current runner.
- The complete current interpreter diagnostic:515 cases/9,091 assertions;
  production CLI:21 cases/105 assertions. Compiler coverage remains358 frozen
  outputs and358 presentation variants, with63 supported runtime slots and152
  explicit unsupported slots.
- Ninety byte-identical outputs rebuilt in a fresh source-only checkout,
  including POLICY.EXE and the full runtime CASES.DAT. The staged DOS package
  binds the current terminal and runner without originals or private profiles.

Reconcile the checkpoint with
`./tools/dev --command python3 standalone/record_aspect_input_policy.py` after
building and running its prerequisite checks. The public validation record binds
source, binaries, manifests, static evidence and local reports. Earlier serial
and receive records remain historical snapshots with their original identities.

This advances input-policy integration. It does not establish full logged-in
BBS interaction, physical UART/modem compatibility, complete ASPECT, or any
closed F01–F16 whole-application gate.
