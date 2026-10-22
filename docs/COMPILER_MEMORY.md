# DOS compiler conventional-memory ownership

The initialization policy increased retained terminal code enough to expose
ASPCOMP heap exhaustion during attached PROGRAM compilation. The first full
suite passed five simple cases but failed all eight larger variants. The
existing compiler corpus alone did not reproduce that tighter parent context.

The compiler now pools small first-pass allocations in aligned 512-byte arenas,
stores ordinary source lines separately from larger initializer records and
reuses completed control-flow blocks after branch/exit patching. Logical
allocation fault counters still count each requested object. Disposal releases
all owned arenas; phase changes clear reusable-block references. The serialized
AUN1 format, language limits and 24 KiB compiler stack remain unchanged.

Arena-only and compact-record intermediate builds still failed the attached
case. Completed-block reuse resolved it. Those failed cohorts remain under
ignored `build/aspect-parent-process/init-result-*` storage; they are not passing
evidence. The final suite passes all thirteen attached PROGRAM workflows while
retaining 10,278 parent bytes and restoring serial ownership.

The [initialization receipt](validation/modem-init-policy.json) binds the compiler
identity to 2,025 complete compiler cases, 2,015 first-pass/ownership cases and
2,043 checked-stack cases including eighteen deep-expression inputs. The stack
campaign keeps a 16 KiB checked API stack and a deliberate 2 KiB overflow control.
A fresh source-only build reproduces the compiler executable byte-for-byte.
These results cover the measured workloads, not every low-memory DOS machine.
