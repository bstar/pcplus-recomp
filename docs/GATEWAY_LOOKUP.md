# Direct COMSPEC execution prerequisite

The optional `--gateway-lookup` parent links a bounded direct-interpreter
policy above the existing raw DOS EXEC boundary. This is an implementation
prerequisite. Alt-F4 remains unavailable until the foreground, file and serial
ownership work below is integrated and tested.

The resolver reads uppercase COMSPEC from the parent's bounded DOS environment,
uses an empty command tail, and preserves nonzero child exit status as a
successful EXEC. Bare names use the recovered extension/PATH policy; qualified
names do not search PATH. There is no PCPLUS resource-prefix lookup or SYSTEM
fallback to COMMAND.COM. Missing, empty, malformed and oversized settings fail
explicitly. Environment parsing, cancellation, pointer extents and ABI checks
reuse the existing HOOK_CODE boundary without changing ordinary HOOK policy.

The policy expects a directly executable interpreter. Native CRT batch coercion
for a COMSPEC ending in BAT is deliberately excluded: the maintained resolver
rejects a BAT interpreter before EXEC, rather than executing batch text as code
or constructing another `/c` invocation. Invalid COMSPEC handling is a maintained
validation policy; it is not a claim of complete original error-path parity.

## Evidence

The receipt is [gateway-lookup.json](validation/gateway-lookup.json).

- 33 linked CPU cases check direct/PATH/extension selection, empty tails,
  errors, cancellation, malformed environments and argument/context guards.
- 15 paired genuine-native CPU cases match selected executable paths, command
  tails and success/failure, with modeled filesystem/EXEC boundaries. Missing
  settings and native CRT batch coercion are explicitly outside those pairs.
- The existing HOOK resolver passes 28 policy cases and 14 boundary/cancellation
  cases with the new component linked.
- Nine actual DOS8086 probe workflows pass 93 checks for qualified and PATH selection,
  extension resolution, child exit 37, missing/invalid/BAT settings, directory
  changes and real COMMAND.COM MD/CD/EXIT. They validate the exact retained
  parent floor, empty `00 0D` tail, startup-directory restoration and final
  hardware/vector snapshots.
- Both the normal and diagnostic parents reproduce exactly in fresh Git-free
  source trees. Disabling the feature reproduces the preceding 4ed1a003 image.

The diagnostic `--gateway-probe` calls the resolver before UART startup, records
the result/current path and exits through ordinary application cleanup. Its
real shell test queues only the shell commands and EXIT; no extra return-key
acknowledgement is supplied. It does not validate the future Gateway screen or
serial return transaction. Two preliminary interactive test schedules timed
out because of invalid ADDKEY tokens and scheduling ADDKEY after removing it
from PATH; those failed fixtures are excluded from acceptance.

## Product identities

Normal component parent:
`build/gateway-lookup-final-20261104/TERMINAL.EXE`, SHA256
`e2204a0f3035e9b4a01df99ee32bf1ea13b45bfb777dc1b8924c95b84c67d9ef`.

Diagnostic parent:
`build/gateway-probe-final-20261104/TERMINAL.EXE`, SHA256
`193965c24253d17eb9134d76717ee2756b924720a88577fb791582bf693b3d18`.

Near data/stack remains 65,488 bytes with 48 spare. The normal resident segment
remains 65,332 bytes; the diagnostic is 65,344. HOOK_CODE is 28,100 bytes. The
normal/probe builds declare 583/584 public inputs and contain no original
executable inputs. No deployment selection or physical machine file changed.

## Remaining foreground integration

The ownership audit establishes concrete requirements beyond this resolver:

1. Add a distinct Gateway job/action, launch revalidation and a normal return
   branch without PROGRAM's key prompt. Preserve shell CWD until final exit.
2. Include the new job kind in the critical IF0 UART-quiet boundary, which
   currently admits only kinds up to 5. A child ISR must be quiet before trap
   resume, interrupt enable or released child memory can become relevant.
3. Choose and test serial ownership across an interactive shell. The original
   keeps its ISR live; maintained PROGRAM pauses/detaches. Neither recovery nor
   this startup probe establishes sustained RX/flow/DCD/FIFO or transient-DTR
   behavior for the new Gateway lifetime.
4. Preserve active capture/printer state and private file positions through an
   explicit child-handle boundary. Existing PROGRAM stops capture and closes
   printer output; its raw EXEC path does not use ASPECT's JFT isolation.
   The optional [private-handle prerequisite](GATEWAY_HANDLES.md) now supplies
   retained JFT isolation and read-only owner queries; application adapter and
   foreground integration remain open.
5. Revalidate parser, transfers, recording, views, directory/resource transactions,
   log recovery and path quarantine. A generic raw-EXEC permission is not proof
   that the foreground is idle. Keep display/mouse/trap restoration and the
   retained-memory floor explicit.

The original contract and its limitations remain in
[Gateway recovery](GATEWAY_RECOVERY.md). Physical DOS/modem acceptance, broader
child mutations and full application parity remain open.
