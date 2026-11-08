# Recovered GET owner with the serviced field

The recovered GET owner now runs against the maintained field adapter,
keyboard/service lease and child renderer client in a DOS diagnostic. This moves
the command's typed readers, string writeback, integer/long conversion and cancel
policy onto the serviced editor. The application opcode table and both compilers
still refuse GET; full-runtime context aliases and real parent/serial execution
remain unconnected.

`get_native_field.asm` implements the owner's seven-word, callee-clean field
ABI. Its C adapter accepts only GET's known string/numeric filter identities.
Initial data is bounded and staged in a local buffer. Accepted text goes through
a separate82-byte commit buffer, then at most81 bytes including NUL reach the
native near slot. Existing bytes after the terminator remain intact. Cancellation
never copies edited text into that slot. Service failures enter the actual native
GET abort checkpoint rather than returning a false accept/cancel result.

Normal field end queries and caches the last presented physical cursor before
retiring the parent field. The native owner's subsequent cursor/adoption sequence
can use that scalar inside the same checkpoint generation. It does not query a
retired parent owner or hold a pointer into its display state. The final native
logical-cursor operation remains modeled in this diagnostic; the real parent
controller's own adoption was verified separately.

## Combined evidence

[The receipt](validation/aspect-get-native-field.json) records the source and
artifact identities. Actual DOS8086 with FPU disabled exercises142 frozen cases:

- 137 match the original observations, including final destination bytes and
  unchanged tails, FAILURE, cursor/field/bell/confirmation counts, conversion
  request text, operand consumption and consumed keys. They span S0 plus
  global/local/parameter string, integer, long and float destinations. Float
  conversion remains an opaque eight-byte service, not floating mathematics.
- Five intentionally refuse a field extending into the reserved status area of
  the modeled24-row parent view. Their destinations and queued keys remain
  untouched, with no cursor adoption. The original owner allowed those spans
  under its supplied25-row context, including an out-of-range final column.
  These are checked safety differences, not original-behavior matches.

The actual recovered owner, typed readers, far string copy/flush, integer CRT,
native field ABI, serviced field/session, WHEN C gates and renderer client run.
An observing C entry records the call and delegates to the same field C code
compiled under an alternate symbol. The production assembly field entry still
executes. Parent display, BIOS keys, serial, native WHEN action bodies and final
cursor/confirmation/abort decisions are controlled services. The operand stream
uses the existing synthetic buffered FILE. No actual full dispatcher, child EXE
handoff, parent parser, UART/BBS or physical acceptance is established here.

The34-input isolated public-source export reproduces the exact executable and
complete report without originals, private data, previous objects or ancestor
Git. The ordinary diagnostic remains byte-identical to its earlier142-case
binary; the separate checkpoint diagnostic still passes142 cases and12 injected
faults/retries. The existing editor lifecycle diagnostic now passes759 checks
with a real far-heap buffer retained across every scenario, and has its own exact
20-input source reproduction.

## Far heap layout correction

The combined test initially found editor state corrupted immediately after
`_fmalloc`. The diagnostic's class order placed the far record after STACK,
where Watcom's far allocator reused it. Excluding storage from DGROUP alone was
insufficient. Both builders now place FAR_DATA before DGROUP and assert that
ordering, its independent group and exact extent. The record is now202 bytes,
including the cached cursor. The lifecycle heap probe checks all82 sentinel bytes
survive. The native-owner diagnostic also keeps its real far string allocated
through all142 cases. Failed layouts are excluded from accepted evidence.

This layout condition must also be enforced when the module enters the full
application. The current application does not link it, and no selected package,
physical installation, modem, SIP or BBS service changed.

Remaining work is full-runtime geometry/position/attribute preparation before
the owner reads its operands, production typed/scratch/cursor aliases and final
native dispatcher abort propagation, real parent parser/receive composition,
FLOAT.RTE, both compiler grammars/opcode49, raw console behavior, application
memory/package admission, connected scripts and physical acceptance. Sibling
modes1/2/3 remain unnamed and unwired; these tests exercise GET's ordinary mode.

```sh
./tools/dev --command python standalone/build_aspect_get_owner.py \
  --checkpoint --serviced --output build/my-serviced-get
./tools/dev --command python standalone/prove_aspect_get_owner.py \
  --build build/my-serviced-get --output build/my-serviced-get-source
```
