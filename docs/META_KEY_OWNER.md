# Checked Meta Keys file owner

The KEY-file components now have an owner which coordinates namespace claims,
disk baselines, load/default creation, save and uncertainty quarantine. It uses
the actual capture reservation library. It is not yet connected to Alt-M in the
interactive parent or installed application.

## Lease and storage

`meta_key_owner.c/.h` uses 1,518 bytes of explicit caller-owned far storage.
Storage is inspect-only while leased; callers must not mutate its fields. A
four-byte process registration lives in writable code storage, with no new
DGROUP globals or constants. The owner and callback code must remain alive until
End succeeds, or until the application returns to DOS after quarantine.

Begin acquires the existing dynamic capture reservation. An incompatible dynamic
owner refuses it without stealing that lease. The selected target and same-parent
`KEYSTG.$$$`/`KEYBAK.$$$` are protected. During a switch, the pending candidate's
three identities are protected as well. Refresh checks existing open/uncertain
binary sinks and fixed claims before reading KEY contents. Normal failed loads
release only the pending candidate; the old selection remains protected.

These are in-process reservations, not external filesystem locks. They cover
the capture library's binary sinks and fixed claims. Other application backends
must honor their own admission/claim coordination; this owner is not a universal
DOS file lock. The caller must still obtain terminal file/EXEC admission before
calling its synchronous DOS operations.

## Bind, Load and Save

Bind captures the initial selected identity and disk baseline without replacing
the live table. This preserves unsaved in-memory edits when reopening Alt-M.
Binding a missing file records an absence baseline without creating it. A later
explicit Save creates that file from the supplied edited records, using checked
exclusive creation. Bind reads the current disk baseline; it does not establish
freshness back to application startup or protect against external writers.

Explicit Load is different: after checked read and close it commits the loaded
records and new selection. Only DOS file-not-found error 2 initializes defaults
and attempts creation. Defaults set each kind WORD to TEXT/3 and the first text
byte to NUL, preserving the other 51 bytes in each slot. This matches the recovered
initializer `e24a..e261`, whose provenance and original-instruction tests are
recorded in [native Meta components](META_EDITOR_RECOVERY.md). No new original
instruction replay is claimed here.

Creation uses the checked staging backend, and publishes destination records
only after successful installation. A competing creation is preserved, and the
old table/selection stay active. Missing directories, malformed existing files
and other read errors do not trigger destructive replacement. The original's
broader failure/default behavior is intentionally distinguished from this checked
policy; no whole native error-path parity claim follows.

Save uses the retained absolute identity and expected disk baseline, never a new
resource lookup. Successful installation advances the baseline. A stale file or
an ordinary, fully resolved failure leaves the prior baseline intact. Save and
End do not adopt or undo the application's live action table. End releases a
resolved lease without implicit saving.

## Recovery

An uncertain close, failed rollback, or retained owned stage/backup/cleanup
outcome latches HELD. A failed lease release does likewise. The owner retains all
claims and refuses Bind, Load, Save, End and reinitialization; its EXEC predicate
stays false. When installation succeeded but backup cleanup failed, the result
still reports installation and advances the disk baseline, while HELD preserves
the backup and blocks further work.

There is no reset or blind-retry API. The application must quarantine the
operation and return to DOS while retaining callback code/state. A future
verified recovery mechanism is separate. Existing recovery files which merely
cause a preflight conflict are not silently deleted or claimed as newly created
files. External namespace replacement, drive remapping and power loss remain
outside the in-process lease guarantee.

## Verification

```sh
./tools/dev --command python standalone/build_meta_owner.py \
  --output build/NEW-meta-owner
./tools/dev --command python standalone/prove_meta_owner_source.py \
  --build build/NEW-meta-owner --output build/NEW-meta-owner-source
```

Twenty-one source-built DOS8086 process cases pass. The normal workflow has 597
assertions covering existing-owner refusal, open-sink and fixed-claim conflicts,
all four binary sinks, initial binding without discarding edits, checked load
and save, failed candidate preservation/release, default creation and all opaque
tails, selection switching, absence binding followed by explicit Save, argument
guards, repeated Begin refusal and normal lease release.

Other cases exercise real DOS IO with declared open/read/create/write/short-write,
close, move/install/rollback, cleanup and competing-write faults. Fragmented reads
succeed. Successful rollback restores the original; unresolved outcomes retain
recovery bytes. An uncertain load in another directory keeps both namespaces
protected. Every HELD case verifies no more KEY IO or release/reinitialization,
unchanged live records and a blocked EXEC predicate. A failed lease-release mode
returns an error without releasing the underlying reservation.

Each fault case runs as a fresh process. The harness resets its owned scratch
files for the next case; that is not application recovery. For the injected
close-before-close case, test-only handle knowledge closes the deliberately
retained handle immediately before process exit, without clearing HELD. No
product capability is inferred from that cleanup.

Object inspection verifies zero new DGROUP data/constant bytes in the owner;
its code storage includes the registration. DS=SS and far state are checked.
An isolated 28-file export reproduces the executable and all 21 results without
original executables, private files, prior objects or ancestor Git. The outer
pinned Nix environment supplies tools. The
[receipt](validation/meta-key-owner.json) binds source/product identities and the
retained default-initializer authority.

## Remaining integration

The editor controller must coordinate modal lifetime, selection/proposals, live
action adoption, global file/EXEC admission and the owner's EXEC predicate. A
transient module must keep the lease callback resident, including on HELD, and
pass application memory/capacity and foreground/UART scheduling gates. Full
screen/cursor restoration, BBS regressions and physical acceptance remain open.
No parent/package, remote service or installed RCE81708 file changed; no complete
feature-parity gate is closed by this component checkpoint.
