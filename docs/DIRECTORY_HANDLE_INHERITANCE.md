# Keep directory read handles out of DOS children

The incremental reader previously opened files with O_RDONLY alone. A DOS
child could inherit that handle while reading was active or after a close
failure left ownership uncertain. Closing the view normally retires the reader,
but an uncertain close must not expose its retained handle to later helpers.

The production filesystem wrapper now requests O_RDONLY | O_NOINHERIT. This
is a DOS3+ policy; earlier DOS versions are outside this acceptance checkpoint.
There is no retry using an inheritable handle. Page loading, cancellation,
uncertain-close ownership and the no-blind-close rule are otherwise unchanged.

The real DOS EXEC witness reads the supplied handle before opening any file:

- An active protected reader is unavailable in the child: error6, zero bytes.
- A separate plain O_RDONLY control is readable in the child, yielding the
  expected first byte. This checks that the witness detects inheritance.
- After an injected close failure that leaves the kernel handle open, the
  child still receives error6. The parent can still read its EOF and explicitly
  close it during diagnostic cleanup. The reader's recovery state is retained.

These three workflows run in both near and far-bank diagnostics. An isolated
13-source export rebuilds the two reader executables, identical EXEC witness
and eleven objects exactly, then repeats 50 actual DOS8086 workflows. The
independent audit checks child reports, complete pages, unchanged source files,
parent handle tables and hardware restoration. The [receipt](validation/directory-handle-inheritance.json)
also binds the application view and package checks.

This closes the reader's child-inheritance gap. Canonical path reservations,
selection/adoption/rollback, broader file-owner coordination and physical/card
acceptance remain required. It does not complete the dialing chooser or the
full application plan. No live service or card was modified.

The updated stage is `build/special-directory-private-handles-20261025/PCPLUSSE`;
its terminal SHA256 is
`6fb218345a2357441a49b24e472f1e0ef6b8b5d32767aa093fb7afa5038e226d`.
The EXEC witness is test-only and is not included in the application package.
