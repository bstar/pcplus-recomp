# Experimental live width transaction

The newer [row/startup checkpoint](LIVE_RESET_ROWS.md) extends the explicit API
to valid row counts/margins and real startup geometry. The24-row hashes and
results below describe this earlier checkpoint.

The later [compiler admission fix](COMPILER_ARENA_ADMISSION.md) now passes the
four recorded nested source workflows beneath this unchanged parent. The failed
compiler observations below remain historical. General display/child/protected
field integration and normal peer dispatch are still open.

`--native-reset-bank --native-reset-transaction` links an explicit
`terminal_native_width` API. AX0 requests80 columns and AX1 requests132. It is
not wired to peer CSI requests: those still stop at2A6E. Entry currently admits
plain profiles4/6 with24 content rows, full margins, owned static planes/shadow,
80-column mode3/page0, BIOS cursor output and no active modal owner. Other rows,
protected fields and unsupported layouts refuse before mutating any cache/video.
This is an integration checkpoint, not complete width support.

## Ownership and failure behavior

The native bank receives an explicit scalar projection, private plane pointers,
copies of the attribute planes, line flags, tabs and logical shadow. The captured
RIS defaults, keyboard map, parser, serial queues, connection/flow state and file
owners are excluded. Native status UI is suppressed; the root status owner keeps
its physical row. Root near state and its owned shadow remain untouched while
native code runs.

The transaction saves the24 physical content rows into the inactive PROGRAM
screen buffer. It borrows no additional data storage. Reentry and existing modal
owners are refused, and reserved live-bank requests require the transaction's
active owner. A native error or invalid result restores those content rows and
the BIOS cursor/shape. It deliberately leaves the physical status row intact,
including updates arriving after admission.

Before committing, it validates the geometry, canonical left pane, private
pointers, cursor offsets and readonly projected fields. Only declared display
outputs, plane contents, tabs, line flags and the used shadow extent are copied
back. Root buffer pointers and RIS defaults retain ownership. A successful
transition clears the display and resets tabs according to the recovered width
routine. Native instructions remain separate from the maintained adapter.

## Evidence and remaining failure

The [receipt](validation/reset-live.json) binds four exact source-only terminal
builds and two kinds of execution:

- Each linked parent model passes22 commits, five fault-triggered rollbacks and
 58 refused calls. It covers both profiles, normal attributes7/1E, repeated widths,
 the right pane, parser output, pan/cursor/CPR consumers and RIS return. The actual
 UART ISR runs on the private stack with512 incoming binary bytes during both
 success and failure. Failed transactions preserve root near data and shadow,
 all received bytes and an independently updated status row. Faults deliberately
 alter a native allocation argument or output; real callback/validation/unwind
 and rollback instructions execute.
- Actual DOS8086 runs both base and guarded branded parents. A declared resident
 fixture normalizes the layout from25 to24 rows at a BIOS boundary and calls the
 real far API after the old BIOS operation returns. It observes the native blank
 screen before the parser redraws, then verifies the exact132x24 logical screen,
 both panes, column132 CPR, restored DS=SS and all42 hardware/vector bytes. The
 first pilot retained the helper's static-banner expectation even though reset
 intentionally cleared it; that failed report remains. The accepted witness
 explicitly observes the clear and then redraws through the actual parser,
 preserving every ordinary helper check.

Fresh declared sources reproduce the ordinary terminal at
`01f55dfbf5385136931c96700be3173cf8594be1c17677e9852fb0f1d025e447`
and the cold-only bank at
`999a9a329d88317f786ef2a22e7dd94c33bb2c994501b0a9d17cb2892ae74e52`.
The new base transaction is
`9f43589cba5ac2bbb3f822043cf29e197f169f0dcbff34fb23b52a4a67678965`;
the guarded branded transaction is
`64681b77eec3421a53647afdc1bde5c3fecc7025a1ed91f5376049cb4904997a`.

**The initial branded transaction failed nested source compilation.** Its resident
module is404,544 bytes,1,504 above the preceding cold-only parent. ASPCOMP starts,
but reports heap error3 at source line1; ASPECT propagates file/output error5.
No ASX is published. Parent parser recovery, PRM preservation, log cleanup and
hardware restoration still pass. This differs from the earlier EXEC admission
failure and must not be described as a failed compiler load. At that point the
first pass required a512-byte arena for its initial small allocation. That
observation led to the bounded-pool and borrowed-buffer fix linked above.

The preceding compact interpreter's passing memory receipt applied to its
cold-only parent. The newer compiler fix verifies admission for this larger
variant in the recorded ordinary-display trials. The transaction remains excluded
from the staged package and card. Conventional-memory admission, general row/
margin/protected-field operation, broader UI/child/scroll composition and a
width-changing BBS session must pass before normal peer requests can be enabled.
Physical modem compatibility remains unverified.

```sh
./tools/dev --command python3 standalone/build_terminal.py --native-reset-bank --native-reset-transaction
./tools/dev --command python3 standalone/check_reset_live.py --terminal build/terminal-native-bank-transaction/TERMINAL.EXE
./tools/dev --command python3 standalone/prove_reset_live_source.py --output build/UNIQUE_SOURCE_RUN
```

The source proof expects current product manifests for ordinary, cold-only, base
transaction and guarded branded transaction builds. Its accepted run is
`build/reset-live-source-01`; it repeats both models and both DOS commits in the
fresh tree. Its original nested-compilation failure remains recorded from
`build/reset-live-nested-02/explicit`; the later compiler proof supersedes that
gate without weakening its assertions.
