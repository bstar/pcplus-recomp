# Keep accounting on the selected source directory

The opt-in resource-owner application now retains the canonical source filename
used for selected-directory startup. A later ASPECT child can change the DOS
working directory without redirecting exit-time accounting to another file.
The user-facing request spelling is retained separately.

The counterexample used a relative `/E:TEST.DIR`, a successful synthetic call,
and a real post-connect ASPECT child that changed to `D:\OTHER`. That folder
contained an identical `TEST.DIR`. The preceding application exited normally
and restored hardware but wrote the call statistics to the decoy. The source
directory was unchanged. The failed result is preserved alongside the fix.

## Source binding and accounting

After PRM/serial/transfer validation, selected-directory startup resolves the
requested directory into its staged context **before opening it**. The strict
reader receives that same absolute filename. Only a complete successful read,
decode and baseline acceptance publish the context. Canonicalization or path
validation failure leaves the active outputs unpublished and aborts startup
before UART installation.

The path helper accepts bounded, disjoint near source/destination objects,
normalizes canonical ASCII case and separators, and requires an absolute DOS83
filename fitting 63 bytes plus NUL. Invalid arguments make no DOS call; other
failures preserve the destination. It does not open or write files itself.

Before accounting, a banked read-only check requires a valid retained context,
a matching entry number in 1..200 and a valid absolute source filename. The
resident wrapper passes that checked pointer to the existing shared-storage
transaction. A refusal performs no file IO, preserves the pending count and
preserves an earlier exit error. Without an earlier error it uses the existing
accounting failure result. Installed/recovery handling remains with the shared
storage owner; this change does not retry an uncertain close or release claims.

Canonical names bind the DOS namespace, not an externally locked file generation
or physical medium. The existing expected-record and recovery checks remain
necessary. This is an application policy in the opt-in build; the generic
directory decoder continues to retain the spellings supplied by its caller.

## Evidence

The [receipt](validation/directory-account-identity.json) records the old
counterexample and current candidate. The actual DOS8086 COM3/IRQ5 test runs
the parent and its source-built ASPECT child, proves the child changed folders
by a host-visible directory witness, and verifies exact source-only accounting
updates, unchanged decoy/PRM/script and final UART/PIC/vector restoration.

A passive INT21 observer records the initial content-open path and mode. It
confirms that the fixed reader opens `D:\TEST.DIR` rather than re-resolving the
relative request later. The observer forwards DOS calls unchanged and verifies
restoration of its own vector before saving its trace. It does not change CWD,
keyboard input, UART state or application memory.

Twenty-six linked cases execute the canonicalizer, context/path checks, early
accounting refusals and ABI boundaries. Only DOS canonicalization replies are
modeled. Two damaged non-executable controls reject an incorrect callback and
path argument; they are inspected, never run. Native packaged START also
compiles an ASPECT source and reopens the frozen viewer after child return.

The build uses 64,976 near bytes, leaves 188 resident-CS bytes free and retains
410,688 module bytes. No capacities or stack sizes change. Ordinary, LoC.6 and
CLI-only control binaries remain byte-identical. All work uses the pinned Nix
toolchain and public source inputs.

## Remaining transition work

This fixes the accounting source identity; it does not enable selection adoption
or dialing from the preview. The next transaction must retire pending accounting
under UART handoff, reconcile the accounting and frozen logical records
(including selection of the same entry), stage translation/scripts, and publish
selected UART/profile/resources/target/transfer state with checked failure
handling. Full F01–F16, physical Boca/SPA2102 and card acceptance remain open.
