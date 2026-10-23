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

## PROGRAM notice help integration

The optional `--notice-help` ASPECT build now provides a maintained foreground
help view while a PROGRAM error notice owns the display. It uses the unchanged
capability16 terminal and lives in `build/aspect-notice-help-parent/ASPECT.EXE`;
the separate fault driver lives in `build/aspect-notice-help-fault`. Build with
`./tools/build notice-help`; run the integration suite with
`./tools/build test-notice-help` and the source proof with
`./tools/build test-notice-help-source`.

Alt-Z opens authored PROGRAM/error and serial-session topics. Left/Right,
Up/Down, PageUp/PageDown, Home/End and T navigate. Enter, Escape or Alt-Z closes
help; the next key still belongs to the notice. Input-only/default products
keep their preceding behavior. This replaces the original external-helper path
for this selected context; it does not invoke PCHELP or read a vendor HLP file.
The recovered HLP codec remains a separate foundation for broader help.

`src/help/view.c` owns a guarded4,032-byte DOS allocation containing the exact
4,000-byte video frame. It requires DS=SS, IF1 and fixed mode3/page0/80x25,
validates immutable bounded topic strings, and saves/restores the BIOS cursor.
Code resides in NOTICEINPUT_CODE, with content/private state in the child's
DGROUP. The full near code segment and unchanged parent near state gain no
code/data. The help child uses49,328 near bytes including its8KiB stack.

The input facade intercepts the local Alt-Z only for a configured live notice.
Each help input pass still validates its mouse/BIOS owner, and idle passes check
the view's guards/geometry. Key peeks consumed by help return pending without
publishing a notice key. Cleanup validates the underlying notice generation
and identity, retires help first, then restores the underlying notice. Failed
guard/geometry/free cleanup retains ownership for retry; successful screen
restoration followed by a failed free is never repeated over a newer frame.
The existing unresolved-input exit policy retains the owning DOS process.

Transport/flow, speaker and poll-budget work continue on the notice service
path. Both elapsed-tick deadline and the recovered controller's independent
three-second clock pause while help is live. A first integrated capture showed
that pausing only the service deadline still let the native counter dismiss
help after about three seconds; the fix accounts for both clocks. Other
builds retain the exact original clock binding.

The [integration receipt](validation/notice-help.json) accepts four ordinary
help workflows across COM1/2, standard/enhanced BIOS and present/absent INT33.
Each holds help90 ticks, navigates both topics, compares exact notice/cursor
restoration, receives508 queued text bytes and runs a subsequent real DOS child.
Three DIV/typed-abort/foreign-DS outer faults occur with help open; recovery
preserves private streams and executes the next child. Six native/no-driver
input regressions and36 view-owner checks also pass. View-owner checks include
IF0/foreign-DS rejection, damaged-guard and geometry repair, and failed-free
retry without stale repaint.

Fresh source-only647-file builds reproduce the four matching products. Separate
641/632-file proofs reproduce the preceding input and published baseline
products with unchanged executable hashes. Four current-build ENiGMA/Synchronet
record/compile/replay sessions pass; the BBS harness checks coexistence with
the help-enabled child and does not open help during those BBS sessions.
See [the BBS receipt](validation/bbs-notice-help.json).

The first full-terminal observation timeout, the partial clock-pause failure,
and the no-driver observer COM-size/menu-close failures remain excluded. The
observer now bounds its COM size and allocates its report buffer separately;
no-driver navigation closes the parent menu with Escape. All injected keys,
callback/vector exchanges and owned repair operations are test instrumentation.

## Remaining integration

The original helper's complete UI/content/search and18-byte cross-process
descriptor admission remain separate work. The new two-topic view covers
PROGRAM notices, not all original application contexts. It borrows no parent
window and adds no new parent RPC operation; general rendering/window RPCs
remain excluded while PROGRAM owns its lease.

Broader authored topic coverage, resource-backed text/search, application context
mapping, combined help/window/speaker corruption, reentry/arbitrary asynchronous
faults and real DOS-kernel comparisons remain open. DOSBox-X8086 and injected
BIOS/mouse events do not prove physical input/modem/acoustic acceptance. Full
PROGRAM and all whole-application gates remain unproven.
