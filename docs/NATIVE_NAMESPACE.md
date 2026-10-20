# Native executable lookup and command-processor policy

The [namespace validation](validation/native-process-namespace.json) binds2,440
exact recovered bytes to55 actual DOS cases/2,053 assertions, including the20
core cases. A separate core executable still passes678 assertions. The additional
1,047 bytes supply spawnv, PATH search, SYSTEM, access/error handling and native
string/path-component helpers. Ordinary builds read no original artifacts.

`native_process_search` executes the recovered mode0 lookup path. It tries the
current directory first, then uppercase PATH after native errno2 only. A slash,
backslash or drive qualifier prevents PATH fallback. Missing extensions resolve
in `.COM`, `.EXE`, `.BAT` order; an existing extension remains unchanged. Native
batch comparison is case-insensitive. Controlled DOS children return distinct
exit values so the test distinguishes current directory, first PATH directory
and second PATH directory, rather than accepting any successful launch.

Semicolon parsing retains the recorded native policy. Repeated semicolons after
a nonempty component are skipped; an empty first component stops the search.
Missing, empty or lowercase `path` does not find a later directory. No modern
quoting or normalization is substituted. Explicit backslash, forward-slash and
drive-qualified examples run under actual DOS. An access-denied candidate stops
before a later PATH directory, with errno13/DOS5 retained.

`native_process_system` executes the native COMSPEC `/c` route. The original
string remains intact, unlike direct batch suffix removal. Missing COMSPEC or
native errno2/13 selects `command.com` in the current directory/PATH; other
errors stop. Real command output files verify valid COMSPEC, missing executable,
access-denied, absent variable and post-memory-exhaustion recovery. A deliberately
nonzero successful child returns17 without executing the fallback command.
An overlong tail and actual DOS memory exhaustion each select one target only:
neither triggers fallback. Uppercase COMSPEC/PATH lookup remains case-sensitive.

A null SYSTEM command queries COMSPEC availability without starting a child.
The maintained access boundary rejects a null filename instead of passing
unrelated DS:0000 data to DOS. The native access body still handles nonnull
filenames. Original overlay/load-and-go mode remains outside the admitted
P_WAIT owner; its unresolved service has an explicit errno22 rejection rather
than a successful stub. It is not exercised or exposed by these public APIs.

## Allocation and batch boundaries

PATH lookup can keep a260-byte PATH buffer, an extension candidate and an
environment allocation alive together. The maintained allocator now stores
each owned near allocation in a linked list with an inline header. Native free
removes the matching owner; unknown or remaining owners produce a typed state
failure. Final cleanup drains remaining allocations. The four zero padding
bytes and far-backed arena restoration from the [process foundation](NATIVE_PROCESS.md)
remain in use. Watcom allocation failure translates explicitly to native
errno12/DOS8, so lookup does not accidentally continue with a stale missing-file
error. Allocation headers, padding, admission and error translation are maintained
adapters and do not count as recovered bytes.

The actual DOS test observes three simultaneous near allocations, retires all
owners after each case, and fails each of the four allocation calls in turn.
The fourth call is the environment allocation after the initial current-directory
probe, PATH allocation and selected filename allocation. Forcing that call alone
to fail invokes the real far backup while two near owners remain live; the EXE
child verifies its environment/arguments and returns37. Forcing far allocation
to fail also returns safely. The complete interpreter arena, six open unbuffered
streams and live near/far guard allocations remain intact.

Every selected batch target passes a maintained size check before the native
prefix copy, including a batch found through PATH. That native copy precedes
the original argv checks and can otherwise overrun its stack for a long filename.
The component rejects an oversized synthetic batch target with errno7/DOS10
before allocation or execution. It preserves admitted native suffix-removal
behavior. Reentry through either new API returns BUSY before touching the result.

## Reproduce

```sh
./tools/build native-process
./tools/dev --command python3 standalone/test_native_process_dos.py --label CORE
./tools/dev --command python3 standalone/test_native_process_dos.py \
  --namespace --label NAMESPACE
./tools/dev --command python3 standalone/record_native_namespace.py \
  --label NAMESPACE --core-label CORE
```

Use fresh labels. `./tools/build test-native-process` builds and runs both
executables with generated unique labels. The namespace recorder verifies
binary/source/child identities, exact extension and directory choices, query
results, allocation failure outcomes and command output bytes. A successful
exit alone cannot satisfy command acceptance. Each run retains its executable,
manifests, children and authored DOS-source snapshot; timeout now writes a failed result even if an inner
batch process happened to write PASS to the outer result file.

The initial expanded attempt searched for `CHECK` while the harness itself was
`CHECK.BAT`, causing native lookup to select the harness recursively. It timed
out and remains an incomplete failed attempt, with its exact source and repeated
redirect log bound in the validation record. The corrected fixture uses ENVCHK
and PCPTEST.BAT, preserves unbuffered assertion output and runs in a fresh folder.

These are component APIs. Production shared CRT/environment/VM ownership,
display/font/cursor/WAIT/NOCLEAR, UART handoff, ASPECT continuation/leases,
invalid-executable-format cases and final runtime publication remain required.
RUN/DOS/SHELL are still unpublished; ENiGMA and other BBS acceptance does not
exercise them yet. Physical hardware/modem testing and all full application
gates remain open.
