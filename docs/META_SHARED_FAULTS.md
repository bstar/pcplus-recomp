# Shared-runtime fault and arena checks

The shared Meta application passes two additional arena/history cases, twelve
malformed-header/fixup cases and four uncertain-close cases in DOS8086. No
application changes were required. A fresh 728-file isolated source export
reproduces the parent and both overlays and repeats three Meta/four Alt-P cases.
[The receipt](validation/meta-shared-faults.json) binds the results and sources.

The prior-allocation fixture writes cookie-like bytes only inside its own DOS
allocation before the application starts. A passive observer sees those bytes
before module loading; the normal Meta editor subsequently opens and adopts a
key whose output reaches the UART peer. This does not establish that the cookie
survives loading or that there was a stale-cookie bug. The history case separately
observes an actual nonempty Redisplay frame, exits it and opens the working editor.

The malformed cases cover out-of-range, duplicate, overlapping, descending and
invalid-segment fixups, plus magic, version, size, count, data-base and arena
header bounds. These execute owned diagnostic copies with changed expected
metadata. Fixup cases update the expected CRC so rejection reaches fixup checks.
Each refuses twice and resumes ordinary input/parser replies. Their copied-parent
hashes are distinct from the source product hash; they are not release binaries.

The close injector matches the module pathname, handle and opening PSP. For both
Line/Port and Meta it reports failure either before or after the real DOS close.
The unchanged application records fatal held state, performs no fixups and exits
with code14. There is one loader close attempt, identified by its caller code
segment. Two later closes occur outside that segment during process shutdown;
the report records these separately rather than attributing them to the loader.
The hook is restored and configuration/hardware restoration checks pass.

These are emulator and synthetic-peer checks. The earlier BBS/capacity receipt
remains a historical checkpoint. Exact-product connection, reconnect, binary
transfer, cancellation and carrier-loss gates are next. Wider arbitration,
other display geometries, resource-cache adoption and physical acceptance remain
open. The installed package has not changed.
