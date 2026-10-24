# Fixed log identity alongside recorder reservations

The experimental telephone-log terminal now includes a second reservation
mechanism for one fixed canonical path. It coexists with the recorder's
existing dynamic target/scratch/backup probe. This supplies the shared file
service needed by the logger; the logger does **not acquire it yet**. Queue
lifetime and terminal event integration remain open.

`CAPTURE_FIXED_RESERVATION` enables the extension in `capture_file.c` and
`capture_reservation.c`. The standard terminal omits it and still rebuilds to
SHA256 `2978657cb75ac29067796c98d81ff253b91eee96b995924d266d05bdfbae471c`.
Its original eight-byte reservation descriptor and single external-probe
contract remain intact. The experimental descriptor is 74 initialized bytes:
the original prefix plus an opaque near owner token and 64-byte identity.
Both implementations keep DS=SS and the existing 96-byte sink snapshots.

## Contract

The caller resolves the DOS canonical identity before calling
`capture_file_claim(identity, owner)`. The service accepts an absolute
drive-qualified DOS 8.3 path of at most 63 bytes, normalizes case/separators,
and rejects devices, traversal, invalid spans and private-owner aliases.
It performs no DOS I/O. A non-null opaque token controls ownership; this is an
internal foreground contract, not authentication or an external process lock.

The candidate is checked against all active or ambiguous-close capture,
snapshot, monitor and history owners. It is also checked against the current
dynamic recorder probe. Failure publishes no new identity or token. The same
token can refresh its claim after the checks; another token cannot replace or
release it. Matching `capture_file_unclaim(owner)` clears the token and all
64 identity bytes.

Exclusion works in both directions. Every later sink begin checks the fixed
identity after DOS canonicalization and before file open/create. Every dynamic
recorder registration or refresh probes the fixed path as well as existing
sink identities. An unrelated recorder and unrelated captures remain usable.
Releasing the recorder does not release the fixed claim, and releasing the
fixed claim does not clear an ambiguous sink handle.

One shared busy guard protects callbacks. Nested claim/unclaim, recorder
registration/release and mutating sink operations reject while a probe runs.
No callback may perform DOS I/O or mutate the owners being examined. Caller
namespace stability remains required; this does not protect against external
writers, drive remapping or replacement outside the application.

## Evidence

The [bank validation receipt](validation/phone-log-bank.json) includes four
fixed-claim DOS cases with 446 assertions and six unchanged legacy reservation
runs with 302 assertions. The fixed cases compile from a copied ten-file
source tree, without originals or old objects. Two use actual DOS file
operations and two explicitly model ambiguous closes; each runs with near or
genuinely separate far reservation code.

The cases cover five DOS spellings of the same log against all four sinks,
fixed/dynamic registration in both orders, failed and successful refresh,
wrong-token release/replacement, reentry, private/wrapped pointer rejection,
unrelated writes, release clearing and preservation of ambiguous-close state.
Independent checks require exact `KEEPA` log bytes, exact `OTHER` capture bytes,
no recorder/reentry files, unchanged JFT entries in actual-DOS cases and equal
42-byte kernel/UART snapshots. The first snapshot attempt lacked the sampler's
D: mount; the corrected harness supplies it and preserves the strict check.

Accepted fixed evidence is `build/capture-fixed-reservation-04`; legacy
evidence is `build/capture-reservation-fixed-baseline-01`. Earlier exploratory
outputs remain local and excluded. The terminal memory inspector now verifies
all 74 initialized bytes, both new functions' CONFIG bank placement, and all
three resident/bank reservation boundary calls. Five new damaged-state/placement cases
raise the logger bank audit to 73 rejected mutations. Two actual8086 terminal
connect/redial runs pass on the changed experimental product.

```sh
./tools/build test-capture-fixed-reservation
```

Next, bind claim acquisition/refresh/release to logger configuration, retain it
while events are pending or a close is ambiguous, and exercise the queue and
recorder together. Then wire startup PRM/path selection and connection/poll
hooks. No whole-application gate or physical modem/card acceptance closes here.
