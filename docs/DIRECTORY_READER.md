# Incremental directory reader for the live chooser

The strict startup reader scans all 23,050 bytes synchronously. The live Alt-D
view needs a foreground reader that returns between kernel calls so the parent
can service received bytes, flow control, replies and local cancellation.
`src/directory/directory_reader.c` supplies that component. It is not yet wired
into the terminal and does not complete the live chooser or directory adoption.

The caller owns a near state object, a 512-byte near scratch buffer and two
separate far pages of 1,394 bytes each. The reader allocates no heap or static
buffers. Existing startup scratch and the command owner's unused snapshot
storage are candidates for the later integration; no sharing is enabled here.

`initialize` requires initially zeroed storage. `begin` validates disjoint
nonwrapping extents, checks physical far-pointer aliases, and opens the explicit
path read-only. The open handle fixes subsequent reads to that file; the path
is not looked up again. As with the existing reader, length alone does not
identify a PCPLUS.DIR format, and external concurrent writes are not excluded.

Each `step` performs at most one DOS operation. Read turns request at most 512
bytes and copy only the header and selected records to private far staging.
Short successful reads resume at their actual byte count. A separate suffix
probe rejects extra bytes; a separate close turn must succeed before the
complete page is published. Unused final-page slots are zero. A step copies
at most 1,394 bytes; it contains no loop that retries a kernel operation.
This bounds the reader's work, not the time spent inside a DOS/device driver.

Cancellation marks the transaction for a later close turn and never publishes
the page. The first IO failure survives cancellation and any secondary close
error. Repeated terminal-state calls perform no IO. A failed close retains the
handle and a recovery phase, refusing new imports or reinitialization. It never
blindly closes again: the kernel may already have released that handle number.
Application-level recovery and exit policy remain part of the integration.

The optional banked build uses four explicit far cdecl entries in
DIRECTORY_CODE and three declared resident filesystem callbacks. DS=SS and near
DOS buffers are retained. The bank occupies 1,378 bytes in the current linked
diagnostic. The terminal executable, parent segment allocation and installed
package have not changed.

The [receipt](validation/directory-reader.json) binds the source export, exact
executables/objects and real DOS tests. Both near and banked forms pass these
22 workflows in fresh 8086 processes:

- First page, last full page, final single record and a second page after a
  completed transaction, with an independent complete-page byte comparison.
- Short reads of 17 and 511 bytes; truncated, overlong, empty and missing files;
  early zero reads and a rejected impossible returned byte count.
- Read failures, both kinds of uncertain close, and a read failure followed
  by a close failure. The released-handle case opens another file using the
  same handle number and verifies repeated reader calls leave it usable.
- Cancel immediately after open, during reads, before the suffix probe and
  immediately before publication; cancellation retains an earlier read error.
- Invalid selectors, unterminated paths, overlapping objects, equivalent far
  aliases, segment wrapping and addresses beyond the 8086 address space.

The diagnostics execute production DOS filesystem functions, with explicit
short-read/failure returns injected above them. They check per-step operation
counts and destination preservation, full final pages, unchanged source files,
process handle tables and an independent 42-byte hardware snapshot. The clean
12-source export rebuilds both executables and all nine objects exactly, then
repeats 44 workflows/13,022 native assertions outside all ancestor Git metadata.
These are component checks; no serial servicing, BBS rendering or physical
driver-time acceptance is claimed.

An earlier outer harness run omitted the sampler's D: mount. Its native cases
completed, but the Python audit failed for the missing BEFORE.BIN. That failed
run remains under `build/directory-reader-dos-20261025`; the corrected mount and
fresh source-export runs supply the accepted evidence.

```sh
./tools/dev --command python3 standalone/build_directory_reader.py
./tools/dev --command python3 standalone/build_directory_reader.py --bank
./tools/dev --command python3 standalone/prove_directory_reader.py \
  --output build/NEW-reader-source
```

Next integrate the reader into the serviced command foreground view. The UI
must poll between steps, retain its handle/staging owner until close resolves,
show bounded name/number fields, and restore updated live video after cancel.
Selection then needs a separate validated idle-line transaction for serial,
profile, translation, key/meta bindings, scripts, accounting and configuration
baseline ownership. The startup-only preference importer must not be called
against an active session: it mutates global baseline/mouse/sound staging.
