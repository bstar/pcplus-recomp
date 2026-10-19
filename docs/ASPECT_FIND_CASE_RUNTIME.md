# Native FIND and SWITCH/CASE in DOS

The production interpreter now links the401-byte recovered FIND/SWITCH/CASE
component and its actual CRT, string, integer-destination and DWORD FILE services.
FINDCASE and SWITCHCASE write the same words consumed by these handlers. FOUND
reads the actual native FIND result. The command table now exposes69 of215 slots;
the remaining146 still stop explicitly.

The [compiler conformance](ASPECT_FIND_CASE_COMPILER.md) freezes54 accepted and72
rejected original-compiler probes before implementation. The host compiler emits
their exact bytes and preserves prior outputs. ENDCASE exits the whole switch;
implicit fallthrough jumps over the following CASE comparison. BREAK is the
separate serial command0D, whose runtime service remains unfinished. Native
state/CRT behavior is documented in [ASPECT_FIND_CASE.md](ASPECT_FIND_CASE.md).

## Near temporary ownership

Insensitive FIND duplicates both strings in the near DS heap. The new
`find_runtime.c` owner tracks at most two1..81-byte copies, uses real `_nmalloc`
and `_nfree`, and releases a partial pair on interpreter termination. The global
string far allocator is a separate owner and is never substituted for these
near pointers. Sensitive FIND and CASE require no such copies.

The original insensitive helper passes unchecked NULL to uppercase if allocation
fails. The maintained assembly adapter deliberately aborts with typed heap8
before native execution can resume that path. The ordinary native dispatcher
then unwinds FILE/global-string ownership, and the final owner releases any
successful first copy. This is a checked failure policy, not recovered native
rollback. Other invalid owner operations fail typed without freeing foreign
memory. Actual memory exhaustion and electrical UART behavior are not inferred
from injected allocation failures.

FIND leaves its inputs unchanged. The optional integer destination receives the
native pointer difference; a missing match stores wrapped zero-minus-haystack,
not a universal−1. FOUND is the shared native0/1 word. SWITCH retains its shared
byte type,81-byte string and word integer snapshot. These are global snapshots,
not a newly invented nesting stack. FINDCASE/SWITCHCASE reset on fresh native
dispatcher initialization and remain shared across procedure calls. FOUND and
SWITCH snapshot fields are owned zero-initialized image data; this integration
adds no per-run reset unsupported by the recovered initializer. CHAIN runtime
integration and broader invocation/configuration lifetimes remain unfinished.

## Execution evidence

[validation/aspect-find-case-runtime.json](validation/aspect-find-case-runtime.json)
binds current sources, product identities and the separate reports:

- The full actual8086DOS runtime suite passes878 cases/20586 checks, including
  28 authored FIND/CASE vectors, actual near allocations and first/second-copy
  fault unwinding. Tests cover ASCII sensitivity, high CP437 bytes, empty/missing/
  overlapping matches,80-byte strings, local destinations, unchanged globals,
  repeated searches, procedure state, default ordering, explicit exits, implicit
  fallthrough and nested selection. Two ASX files of70034 and70041 bytes verify
  real SWITCH and CASE seeks beyond65535.
- The independent near-owner executable passes186089 checks across1787
  operations with the real DOS near heap. It checks near/far views, heap guards,
  invalid/foreign/interior/double frees, first/second injected failure, partial
  cleanup/reuse and DS=SS/SP/BP/SI/DI/IF preservation. It uses a typed-record error
  callback; the full runtime separately proves production nonlocal unwinding.
- Four actual full-terminal cases receive `SyNcHrOnEt` through the UART and
  RGET, then select the synthetic password using FIND/CASE with sensitivity ON
  and OFF. All152 checks pass, including actual DA/CPR replies, adopted history,
  parent owners, hardware state and ordinary keyboard resumption. No parser,
  query reply or peer ASX interpreter substitutes for product code.
- Existing WHEN, SET/status/UART, callback and local Synchronet/ENiGMA workflows
  remain separate regression evidence. ENiGMA still uses explicit30ms buffering;
  its immediate-forwarding editor issue remains unresolved.
- A fresh public-source tree reproduces125 checked outputs without original
  executables, installed configurations, REA databases or previous build outputs.

The empty-case expectation was corrected before DOS execution from original
compiler vector FD035: an explicit ENDCASE exits even when the body is empty.
That original-byte evidence is recorded in the authored runtime fixture. The
test does not turn a failed product result into its expected behavior.

Remaining ASPECT families, full compiler/recorder, native keyboard/UI, parent
session adoption, other emulations/protocols, Host and physical modem validation
remain open. This checkpoint closes no whole-application gate.
