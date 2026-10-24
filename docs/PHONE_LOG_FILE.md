# Checked telephone-log appends

The maintained [append backend](../src/directory/phone_log_file.c) supplies the
failure handling missing from the [native controller](PHONE_LOG.md). It is a
separate source component; the terminal does not invoke it yet. The exact
native instructions and their unchecked-write behavior remain available as
the recovery baseline.

`phone_log_file_append(path, heading, heading_count, record, record_count)`
accepts explicit binary bytes. It includes the heading only when the same
opened file's physical EOF is zero. This also handles retry after exclusive
creation followed by a rolled-back write: the empty file remains in place,
and its next successful append gets exactly one heading. A nonempty
log never gets another heading. The formatter must supply CRLF explicitly;
this backend performs no text translation or date/field formatting.

Inputs use bounded ASCII DOS8.3 paths, no devices/wildcards/traversal, and
nonwrapping near byte spans disjoint from the owner. Record length is1..256;
heading+record must fit256 bytes. Input buffers may overlap each other because
they are copied before IO. DOS canonicalization selects one absolute drive
identity, which is used for the subsequent attribute/open/create operations.
Only writable regular files or exclusive creation are admitted.

## Commit and recovery

The backend opens one handle, captures its32-bit EOF, checks overflow, writes
the exact selected bytes, commits through DOS68h, and closes exactly once.
Only successful write/commit/close sets `committed`. There is no silent fallback
when commit is unavailable or fails.

| Outcome | File/owner behavior |
| --- | --- |
| Complete write, commit and close | Acknowledge this event; allow the next append. |
| Short write, write error or commit error; successful rollback and close | Seek/truncate/commit to the original EOF on the same still-owned handle; return the primary error. A deliberate retry can append the event once. |
| Rollback seek/truncate/commit fails | Retain the primary and rollback errors, close once, latch recovery and reject every later append/initialize. |
| Close fails, whether the OS consumed its handle or left it open | Retain the handle ambiguity and close error. Never reuse, reopen, retry or close it again automatically. |

The166-byte snapshot preserves primary, rollback and close errors separately,
the observed EOFs and accepted prefix, close/write counts, creation/heading
state, canonical identity and committed/recovery flags. A DATA cookie initializes
dirty assembly-host BSS once. Reentrant calls reject while any filesystem
boundary is active. Initialization preserves resolved history and cannot clear
an open or ambiguous owner.

These guarantees assume one foreground writer and a stable DOS namespace.
They are not an external-process lock, power-loss proof or crash-atomic FAT
transaction. Cross-application capture/editor reservations remain a production
integration requirement. Recovery requires explicit reconciliation or process
retirement; there is intentionally no public reset that discards ambiguity.

## Evidence

The [independent receipt](validation/phone-log-file.json) binds138 host model
cases/7239 assertions,18 actual8086 DOS workflows/499 native assertions, an
exact nine-source rebuild and100 artifacts. The model executes the actual
policy C with explicit filesystem boundaries. It covers every primary error,
all rollback stages, consumed/unconsumed close errors, nested entry, dirty BSS,
near-span/owner conflicts, DWORD overflow, overlapping sources and the maximum
256-byte payload.

The DOS diagnostic calls actual canonicalization, exclusive creation, seek,
write, zero-byte truncation, commit and close. Selected wrappers deliberately
inject failures around real three-byte prefix writes and kernel operations;
this is not a claim that a real disk failed. Cases prove exact files, restored
JFT entries except the intentionally unconsumed-close case, blocked retry,
independent166-byte snapshots and final42-byte UART/PIC/vector restoration.
DOS process exit owns cleanup of the deliberately retained handle. Tests
include rollback/retry past70001 bytes, a new empty log's heading retry, a full
binary256-byte append, readonly files and real missing-parent failure.

The initial missing-parent oracle expected an inspection failure. DOSBox
instead reports missing at attributes, then error3 at exclusive creation;
the final witness requires that actual OPEN/error3 result. Early object
rebuilds exposed absolute filenames and timestamps in Watcom metadata, while
the executables already matched. The builder now omits volatile dependency
records with documented `-zld`; source/header hashes are retained explicitly.
It validates all OMF checksums and rewrites only THEADR's absolute filename
to the logical source path. Raw objects are retained, and the independent
audit requires every later instruction/symbol/relocation record byte to match.
The executable remains identical across this metadata correction.

Current evidence is `build/phone-log-file-dos/20261024-191646-027511088` and
`build/phone-log-file-source-06`, repeated after exposing the pure path validator
for the event queue. The previous accepted checkpoint used
`build/phone-log-file-dos-06` and `build/phone-log-file-source-05`.
Earlier exploratory outputs remain local and
are excluded. The clean tree contains nine declared sources, no original,
private configuration, REA database or old object. It reproduces PHONEAPP.EXE
and all three production objects exactly, then repeats the host model.

```sh
./tools/build test-phone-log-file
./tools/build test-phone-log-file-source
```

`build/phone-log-file/PHONEAPP.EXE` is a diagnostic, not PCPlus. The ordinary
objects are `file.obj`, `capture.obj` and `rollback.obj`. No application,
interpreter or compiler binary changed at this checkpoint.

## Integration still required

The separate [event layer](PHONE_LOG_QUEUE.md) now supplies bounded formatting,
DOS date/clock reads, saved PRM flag decoding and retained events with explicit
retry/recovery states. It is not integrated into the terminal. Bind saved
settings at startup and avoid duplicate start/end records across MODEM/DIRECT,
redial, carrier loss, hangup and exit. Reserve
canonical file identities against other foreground writers. Place the code
with checked DOS/CRT bridges in the larger terminal: its resident code has only
76 bytes spare, and compiler/VM stacks and limits must remain intact. Then test
loaded UART traffic, real BBS sessions, physical modem and card deployment.
F07/F10 and all broader application requirements remain open.
