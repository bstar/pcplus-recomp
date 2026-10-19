# Owned DOS backend for native script-file commands

The thirteen recovered handlers and three shared helpers now link to a maintained
six-slot DOS stdio backend in `SCRIPTIO.EXE`. Native FILE operands use a checked
eight-byte near prefix; only the backend owns the real CRT `FILE *`. Each owned
stream has a fixed 512-byte buffer. The native command bodies and their existing
572-byte flat baselines are unchanged.

This is a linked component diagnostic, not application integration. Its typed
operand readers, destination writeback, returning warning and lowercase helper
are explicit fixture boundaries. Real native slot lookup, command bodies,
comparison/EOF stores and CRLF/control-Z handling call actual DOS stdio. The
maintained interpreter and both compilers still need these commands wired in.
The packaged runtime remains at 76 supported opcode slots.

The original dispatcher initializes once, restarts after `EXECUTE` without
reinitializing file slots, and calls its outer resource cleanup after the final
script. REA confirms the loader cleanup closes all six slot entries. Therefore
the backend provides separate reset and finish operations: it rejects resetting
an active owner, retains slots between ordinary calls, and closes every live
stream at finish. A close failure does not prevent closing the remaining slots.
Finish keeps the script's comparison and existing runtime error; diagnostic
counters retain cleanup errors, matching the original cleanup's ignored close
return values. Actual VM `EXECUTE`/abort/cancellation lifetimes remain to be tested
when the backend is integrated.

The recovered initializer defaults `FGETS_CRLF` to on. Native `FCLEAR` edits the
prefix directly; the adapter reconciles those edits with `clearerr`. Separate
latched EOF/error bits preserve native state across CRT operations that clear
their own flags. A seek clears EOF even on failure and retains a prior error
until `FCLEAR`. The borrowed fallback prefix is never an owned stream; direct
backend close rejects it without closing process stderr. This admission rule
does not establish the original returning-warning or unchecked closed-slot policy.

The first real DOS run found a CRT difference: Watcom's `fseek` reported success
for an absolute negative position. The original `853A` seek wrapper calls its
`A22E` low-level helper, which rejects negative absolute/resulting positions
before issuing the DOS seek. Querying the DOS position alone was insufficient:
this DOSBox-X implementation left the position unchanged and cleared carry for
the raw negative DOS seek. The final adapter follows the recovered ordering:
compute a relative offset from logical `ftell`, discard the stdio buffer, reject
negative absolute positions, and restore the prior position after an invalid
negative end-relative seek. Its 32-bit additions use unsigned arithmetic to
preserve the original ADD/ADC wrap. This corrects the observed case without
depending on DOS accepting or rejecting the raw invalid seek.

The actual 8086 DOS diagnostic passes 7,976 assertions and independently checks
16 complete output files from a fresh mapped test drive. It covers:

- Every binary byte, raw NUL/control-Z, 0/80-byte block reads, guarded string
  destinations, 80-character lines and CRLF stripping/retention.
- Text newline conversion and control-Z EOF, append mode, invalid mode/path
  failures and closing the previous stream before a failed replacement.
- Positions beyond 64 KiB, signed relative/end seeks, negative target rejection,
  EOF clearing and error-bit retention across seeks.
- Read-only write errors and actual DOS handle-close faults before explicit
  `FCLOSE` and multi-slot cleanup, with continued cleanup of another valid stream.
- One hundred six-slot rounds with identical used near/far heap blocks and the
  inherited 20-entry DOS handle table after warmup; repeated finish is idempotent.

```sh
./tools/dev --command make test-aspect-script-file-backend
```

Checks never contact the live BBS or map the user's CF card. All writes target
new directories below `build/aspect-script-file-backend/tests`. Failed runs and
the negative-seek probe remain there. The
[backend record](validation/aspect-script-file-backend.json) binds the real DOS
capture, all output hashes, current native replay, source-only build and REA
lifetime/seek evidence.

Remaining work includes compiler grammar/destination integration, dispatch and
`FGETS_CRLF` SET/FETCH, real script cleanup across completion/abort/EXECUTE,
terminal-child handoffs and deeper original CRT equivalence. No whole-application
gate closes.
