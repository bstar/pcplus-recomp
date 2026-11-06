# Contextual Help parent admission

The source helper can now admit the legacy decimal DS:offset descriptor against
its actual DOS parent before copying its strings or opening a help file. This
closes the trusted-parent gap in the preceding
[native handoff probe](CONTEXT_HELP_HANDOFF.md). It is an opt-in helper build;
global terminal Help and the original PCHELP interface are still unintegrated.

## Admission and lifetime

`src/help/parent.c` validates the decimal pointer, obtains the parent PSP from
the child's PSP, checks both PSP signatures, and checks the parent main block's
MCB tag, owner and extent. The descriptor and strings must lie after the parent
PSP within that block, below the conventional-memory ceiling. Parent addresses
above or below the child are supported. The parent block cannot overlap the
child PSP. Other allocations, including separately allocated parent heap
blocks, are not admitted: the recovered producer's descriptor is on its
DS=SS stack and its strings are in that same main image.

The descriptor must fit18 bytes without offset wrap. Path and title copies are
bounded to81 and31 bytes including NUL, matching the native helper's copy
capacities. An empty path, zero descriptor offsets, unterminated strings,
segment wrap or an allocation boundary rejects admission. An empty title is
allowed. Context and all six UI words remain raw values; the reader does not
apply display attributes or change the topic fallback policy.

The reader rechecks the child PSP, parent MCB and descriptor before publishing
one local value containing copied strings and scalar state. Every failure
leaves the caller's output unchanged. No foreign pointer escapes. The DOS
backend issues only the get-current-PSP query and bounded conventional-memory
reads: no allocation, file, video, mouse or serial operation occurs here.

This assumes DOS's process metadata and the foreground EXEC lifetime. It does
not walk the complete DOS MCB chain, authenticate a caller cryptographically,
support arbitrary parent allocations or protect against a hostile TSR changing
memory between reads. Strings are copied once; the metadata recheck does not
make an atomic snapshot against asynchronous string changes. These are explicit
limits rather than guarantees inferred from a matching owner word.

The producer's own unbounded path copy is unchanged. Its66-byte stack slot
still requires a resolved path of at most65 characters before invocation.
Helper-side admission cannot repair a producer overflow which already occurred.

## Verification

[The receipt](validation/help-parent-admission.json) binds the sources, exact
products, checkers and retained results:

- 353 host cases test both parent/child address orders, raw context and all
  repeated-byte UI values, maximum strings, segment/allocation boundaries,
  malformed metadata and unchanged output on failure. Read errors are injected
  at every one of29 admission reads; separate cases change the PSP, MCB and
  descriptor during the final checks.
- The actual8086 DOS native-producer/child test passes231 checks across eight
  valid launches and ten invalid requests. Seven new requests alter only the
  test descriptor/arguments: zero path offset, path/title atFFFF, unterminated
  path/title, a pointer into the parent's PSP and descriptor offset wrap.
  No invalid request creates the child's output record. The real DOS MCB is
  never corrupted to manufacture these faults.
- The native producer still passes1728 paired source/original-slice cases.
  A fresh19-file source tree rebuilds identical EXEs/HLP, repeats1728 source
  instruction cases and231 actual DOS checks, and repeats all353 host cases.
- The disabled control passes its prior182 DOS checks. Its helper and authored
  HLP remain byte-identical to the earlier checkpoint. The test parent's28
  changed bytes are diagnostic `__LINE__` constants shifted by conditional
  fixture source; its length and other bytes are unchanged. No application
  executable was rebuilt or changed.

The first host test exposed an implicit16-bit unsigned cast in the new reader.
The descriptor offset now has an explicitFFFF mask, preserving DOS behavior
and making host behavior correct. A subsequent negative fixture had left its
otherwise-valid path empty after moving its modeled DS; that fixture now
populates both strings before testing the intended boundary. Failed attempts
remain in ignored build history; checks were not relaxed.

Reproduce in fresh directories through the pinned toolchain:

```sh
./tools/dev --command python standalone/build_context_help.py --parent-admission --output build/help-parent-new
./tools/dev --command python standalone/test_help_parent.py --output build/help-parent-new-host
./tools/dev --command python standalone/test_context_help_dos.py --build build/help-parent-new --output build/help-parent-new-dos
./tools/dev --command python standalone/test_context_help_cold.py --build build/help-parent-new --output /tmp/pcplus-help-parent-new
```

## Original interface findings for integration

Further REA analysis establishes that ordinary PCHELP uses `T` for its topic
selector, `S` for a new search and `C` to continue the previous search. `C`
does not return to the calling context. The main controller calls search06B6
with zero; the new-search dialog calls it with one. Zero resumes the saved
match/file position, while one initializes the search from the current topic.
Escape closes the help file and restores the helper's display state. The
main loop also handles Home, Up, PageUp, End, Down and PageDown.

The topic selector has its own Enter/Escape and navigation loop. Geometry00D6
adjusts its position/height and the search dialog when text height differs
from25. These are static findings; pixel/cell layout and complete search-wrap
interaction still need runtime comparison before claiming original UI parity.
The current PROGRAM notice resource browser is a separate maintained interface.

Evidence from original helper SHA256
`5d135afc5808ddec923ec027f385490c7ecd4fa5004d11cefe6ff4a3c468d0aa`:

| Finding | REA evidence |
| --- | --- |
| Main controller and key dispatch | `ev_9e39544b11ad7ac75757f4195d006b8739efe0a4a7e7280d42595463994c75e6` |
| Geometry initialization | `ev_b78ed4469ae3aeeb408c78484e237309d19077d36598cb67a6f096fea08f255b` |
| Topic selector | `ev_ea8e1cb68c1ceea5221f7a9348d63f30488d1dca84873ebd55146f11299a9604` |
| New-search dialog | `ev_ba0c2efe2ec4756766c17d34543e906ef52f1fdba17d209c1b9c0ae99072f498` |
| Search continuation, full pseudocode | `ev_53e67ad400113feaf0d4d4a5845f82722ff86d2dd041251817b807a7cb862a69` |
| Search first90 instructions, including argument branch | `ev_078353ff16cf2070f5568f739494720151e810763bc01da285aae1687498dad6` |

REA was closed with the selected records in ignored
`analysis/help-parent-ui-contract-20261106.rea.json`. No original or synthetic
analysis executable was run for these static findings. The admission checks
are a deliberate maintained safety boundary, not recovered native checks.

Next application work remains the source-built helper UI, correct context and
Alt-Z entry mapping, bounded producer resolver, PROGRAM owner integration,
screen/mouse return, live flow/carrier behavior and error cleanup. No physical
deployment, bridge change or package selection occurred. The full objective
and hardware/full-parity acceptance gates remain active.
