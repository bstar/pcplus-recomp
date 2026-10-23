# Contextual help and the PCHELP handoff

Alt-Z in the recovered keyboard poll is gated by a signed context word. When
enabled, it consumes the BIOS key and calls resident57AE. Fresh REA analysis
corrects the earlier description of that callback as a local diagnostic dialog:
it resolves `PCPLUS.HLP`, constructs a context descriptor, formats
` PCHELP %lu`, resolves `PCHELP.RTE`, and enters the ordinary external-program
controller433D. The helper is a separate DOS MZ program. The current local
script reference window is a maintained interface, not this original helper.

## Static evidence

| Artifact/procedure | Finding | REA Evidence |
| --- | --- | --- |
| Original2.01 resident57AE | Builds nine words and passes a decimal far pointer in the helper command tail | `ev_196b2bcacb2ea45f5941dab4956f5a949aefea43e33322b7ef2dd891e23c4ad0` |
| Resident76B0 | Returns DS, the high word of the far descriptor pointer | `ev_870f26707a2de83a34eabc8eb902bc00650c6f68dc102c47923f4a4709c77f42` |
| Resident433D | Full external-program controller, including native error notices | `ev_129d725582ddbe5d0e4f24faec04828139114ab26c3f1bf03a3cf96141096b19` |
| Startup-data overlay32 | `PCPLUS.HLP`, title, decimal-pointer format and `PCHELP.RTE` strings at data24AC onward | `ev_16c27461af94d70408b3de04206f341a35f5a64ba0ce47673bbb5ea0d953faea` |
| Helper0010 | Requires three argv entries, validates the marker, parses the decimal pointer, copies18 bytes from the parent segment | `ev_d979008430d84019d895cef13b660e2bf42f5ff9497db546c4993e3dda7b7ec4` |
| Helper0157 | Opens the help file, reads topic and total-line counts, handles topic/search/navigation keys | `ev_9e39544b11ad7ac75757f4195d006b8739efe0a4a7e7280d42595463994c75e6` |
| Helper02CC/032E | Signed context fallback to zero; records start at3+topic*38 | `ev_a6c48e97e9fc9e84d1c26bfd0979339d418a6c41d106208654c62e7c5715d293`, `ev_ce6c3f73a541a3316aa62be67712cde65a9d7ddf06669f2a2662fdfd04c961d0` |
| Helper02F8/0C40 | Record word32 is a line count, used to bound text navigation | `ev_799ce953953687447a1f74e04cdd9aab5be07eb1d2f20d9b9eb157a017c4f9b2`, `ev_bbdbb3f2a83a08d280340162d335c6b033c226be8dcafaa006db2ec1d55815e1` |

The original main SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`;
helper SHA256 is
`5d135afc5808ddec923ec027f385490c7ecd4fa5004d11cefe6ff4a3c468d0aa`.
The helper copy matches the installed card file. Complete selected REA records
remain in ignored `analysis/help-context-01.rea.json`. Strings were read in the
existing synthetic overlay01 analysis image, whose startup-data source range
maps original file153936 to relative load64368. That image was analyzed only,
never executed. Static evidence does not establish original runtime behavior.

## Source-owned formats

`src/help/format.c` implements bounded decoding for subsequent UI integration:

* The decimal far pointer contains parent DS in its high word and descriptor
  offset in its low word. The descriptor must fit18 bytes within that segment.
  The parser accepts1..10 decimal digits, rejects overflow/signs/whitespace and
  never dereferences the pointer. This is stricter than the original converter.
* Nine little-endian words hold path offset, title offset, signed topic and six
  UI words. The latter remain unnamed because their complete meanings have not
  been established. Decoding a copied descriptor does not validate the parent
  identity or strings; those require later admission and bounded copy services.
* HLP starts with an8-bit topic count and16-bit total-line count. Each38-byte
  record holds32 raw title bytes,16-bit line count and32-bit absolute text offset.
  Titles gain a separate terminating byte without losing a full32-byte title.
* Index validation checks the complete table, counts, offset ranges, ordering
  and minimum byte extents. The optional reader checks each declared line up to
  the next topic boundary. It preserves32-bit positions beyond64KiB.
* Contexts with the sign bit set or at/above the topic count select topic zero,
  matching the observed16-bit signed check. Resource parsing rejects an empty
  table; malformed headers/records leave decoder output unpublished.

The code contains no copied help text, original executable/resource dependency,
foreign-memory access, video work or DOS EXEC. Native compatibility inspection
is separate from the default source-only test.

## Validation

Run `./tools/build test-help-format`. A fresh source tree builds the8086 DOS
diagnostic and index reader.52 assertions exercise malformed inputs, far-pointer
bounds, negative/out-of-range topics, full-length titles and index bounds. Actual
DOS file creation/seek/read reaches offset65537 in a65,543-byte authored fixture.
The C89 host build produces the same output and exact file bytes. A repeated
fresh-source link reproduces the diagnostic executable.

An explicitly selected optional compatibility run uses the existing original
HLP only as reader input, after compilation. Both host and DOS independently
read all47 topics and463 declared lines from its23,558 bytes. The resource stays
private and unchanged; no original help text is printed or published. See
[the receipt](validation/context-help-format.json). This proves format reading,
not reproduction of the original helper's UI, search, BIOS or process behavior.

## Integration still required

The native keyboard gate remains disabled in ASPECT notices. Enabling it safely
requires a declared foreground help service, context selection, a separately
owned saved view, and cleanup tied to the notice and outer unwind. The existing
PROGRAM lease blocks general parent rendering/window RPCs, so the script-window
service cannot simply be called from this hook. The current child's near code
segment is full and the parent has16 bytes of near data spare; help code and
state must use explicit banks without breaking DS=SS or callback-stack guards.

The eventual maintained help content must be authored from source. Broader
topic navigation/search, application context mapping, failure/reentry behavior,
shared-screen restoration, queued serial input and native mouse/BIOS composition
need integrated DOS tests. No native nested EXEC or unvalidated cross-process
pointer will be enabled by this format checkpoint.
