# Bounded internal viewer paging controller

The [controller](../src/filesystem/viewer_session.c) now composes the recovered
[decoder](FILE_VIEWER_DECODER.md) and [read-only file owner](FILE_VIEWER_OWNER.md).
The [receipt](validation/viewer-session.json) binds its DOS, linked-error,
original-content and public-source reproduction proofs for that component
checkpoint. The subsequent [serviced UI](FILE_VIEWER_UI.md) integrates it into
an opt-in terminal candidate; the installed DOS release is unchanged.

## State and scheduling

The controller retains596 bytes in FILE_CODE, including a26-byte decoder,
256-byte input buffer and64 cached32-bit page offsets. Its object occupies3137
bytes in that bank and emits zero bytes in other object segments. The existing
read-only owner retains90 more banked bytes. The caller lends a valid disjoint
far character page and stable opaque token until cleanup resolves. There is no
heap allocation or new persistent DGROUP storage in the controller.

Begin validates geometry/allocation/path, checks that the file owner is free,
then opens and claims the file once. Initial canonicalization/open metadata is
the file owner's bounded synchronous operation; it is not a guarantee against
DOS/device latency. After begin, each foreground step does one bounded action:
one read of at most256 bytes, one absolute seek, one decode of the retained
bytes, or EOF completion. There is no read/seek loop hidden inside a step.

Forward navigation retains bytes read past a page boundary. The observable
loading invariant, outside a pending seek, is:

```text
physical read position - next decoded offset = buffered bytes - consumed bytes
```

Home and cached Page Up schedule a seek, then discard old read-ahead. Page
numbers and offsets are32-bit. Only64 consecutive page-start offsets are cached.
If Page Up leaves that range, the controller seeks to zero and reconstructs the
requested page over successive bounded steps, building a fresh cache. Loading
can be cancelled throughout. The future foreground dispatcher must call these
steps while continuing its normal serial/parser/input work.

This maintained policy explicitly allows navigation beyond the original's
statically inferred100-page cap. It does not claim identical native behavior
at that cap, which remains untested in the original. The accepted DOS workflow
reaches page101 (zero-based), then backs out of the64-entry cache and verifies
the requested old page after a rescan. Memory use stays fixed; an old-page
rescan can take longer, rather than silently refusing navigation.

Full-page completion does not imply EOF. An exact-boundary file can advance
to the original blank final page; a confirmed partial/empty EOF refuses further
Page Down without modifying the page. Page Up at the first page, invalid
arguments, and commands while loading preserve storage. Home re-reads from
zero. Raw control/CP437 bytes and133-byte chunking remain the decoder contract.

## Errors and cancellation

Failed reads are never fed to the decoder. Read/seek failures enter a failed
phase with the file still owned for cleanup. Stop closes only a file opened by
this controller; it does not close a preexisting owner's handle. A successful
close releases the claim and borrowed page lifetime. Close/release uncertainty
retains ownership and enters a quarantine phase; repeated commands do not retry
the ambiguous boundary or clear its history. The file snapshot still carries
primary DOS and secondary close/release errors.

Shared-buffer admission, terminal child/exit admission and a user-facing
recovery policy must be integrated before enabling this controller in the
application. Caller-owned page storage must not alias another application's
persistent owner/allocation. This internal API cannot establish allocation
ownership from an arbitrary address.

## Verification

The actual DOS diagnostic passes21,727 checks in11 scenarios with8086/FPU-off
execution: literal binary text, clipped long lines across short pages, exact
and partial EOF, empty input, wide/no-LF input, Home/Previous/Next, a396,000-byte
fixture past page100, checkpoint eviction/rescan, cancellation before/after a
read and missing-file cleanup. Complete expected page bytes and raw offsets
are checked alongside the read-ahead invariant, cache bounds, far page guards,
closed owner/claim, unchanged inputs and original C: CWD. The longest rescan in
this suite takes1001 foreground steps; the diagnostic supplies no UART service.

Another26 cases execute the actual linked controller, decoder, file owner,
admission and DOS assembly with modeled errors. All158 observed loading steps
permit at most one DOS read or seek. These cases verify cleanup/quarantine,
failed-read rejection, foreign-owner protection, busy guard, pointer aliases,
argument preservation, current/target agreement, and the far cdecl/DS=SS ABI.
Injected errors do not establish real media or SHARE behavior.

Four prior original captures match the corresponding content expectations
(7680 bytes). The long-line comparison concatenates four2-row controller pages
in order and pads to the original24-row content area. These comparisons exclude
attributes/footer/cursor, which remain UI obligations. A fresh18-file public
source export reproduces `VIEWPAGE.EXE` without original binaries/configuration,
REA databases or previous objects.

### Compiler recovery

The first nonvolatile banked build failed the current/target invariant. Owned
object disassembly confirms it loaded current at state+22h/+24h, stored those
old words into target+26h/+28h, then incremented current. Actual DOS observed
page1/target0 and correctly stopped, rather than silently skipping a page.
The accepted volatile state forces the increment before the target reload/
store. Decoder byte processing still uses its separate nonvolatile bounded
view. Both object disassemblies and the rejected runtime remain locally bound
in the receipt; the accepted run retains all original expectations.

Reproduce with fresh outputs in the pinned environment:

```sh
./tools/dev --command python standalone/build_viewer_session.py \
  --output build/viewer-session-new
./tools/dev --command python standalone/test_viewer_session_dos.py \
  --program build/viewer-session-new/VIEWPAGE.EXE --output build/viewer-pages-new
./tools/dev --command python standalone/check_viewer_session_linked.py \
  --program build/viewer-session-new/VIEWPAGE.EXE --output build/viewer-faults-new
```

## Remaining application work

Integrate the serviced viewer UI, original frame/footer/cursor restoration,
shared-buffer and uncertain-owner admission, direct Alt-V and menu dispatch.
Then validate real UART/parser service, capture/HOLD/printing, Enigma/Synchronet
editor return, carrier-loss/reconnect, transfer/cancel and DOS fault composition.
Configured external viewer, physical DOS6.22/SHARE/Boca/SPA2102/SynthModem and all
remaining ASPECT/emulation/protocol/Host parity requirements remain open.
