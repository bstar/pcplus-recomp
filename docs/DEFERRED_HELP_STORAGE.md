# On-demand Help workspace experiment

The optional full ASPECT child now allocates the resource-backed Help model only
when Help opens. This saves3424 fixed DGROUP bytes and2912 bytes of minimum DOS
memory after the additional ownership code. The experiment is **not eligible for
package promotion**: the largest parent still cannot open Help, and the combined
six-file/PROGRAM workload still has a memory failure.

The [validation record](validation/deferred-help-storage.json) binds measured
layout, component tests, full-parent source cases and an isolated cold rebuild.
The [preceding capacity investigation](ASPECT_CONNECTED.md#full-child-follow-up-capacity-gate-remains-open)
established that the previous child also fails the workload. This experiment
addresses that existing gap without removing application features.

## Ownership and retained sizes

`defer_help_resource=True` in `build_aspect_process.main` enables the optional
placement. The ordinary build retains its static model and reproduces the exact
preceding child SHA-256
`96ea98c9537f3d54b20d02fd8a5f5ec93849f2b01e0485b1a0b867ad199671ab`.
The new child is
`9b1b5f98d6e2a4d64e4154a5d2f97240c1455787e5a7ab5d8d4c1cf37c473fe0`.

The resource model remains near DS=SS storage. Explicit far-cdecl allocator
callbacks enter resident CODE before calling the near CRT; banked Help never
near-calls a CRT routine in another CS. The same two page buffers, titles,
scrolling/search cursors and query widths are retained. No file-slot, stream
buffer, native VM or stack limit changes.

The file/model and display have separate lifetimes. Closing the Help file does
not free the pages while the viewer borrows them. `help_resource_release` refuses
while either resource or view is active. The enclosing notice releases backing
only after successful view close/discard; failed restoration or release retains
it for retry. Missing files, model-allocation refusal and failed view admission
retire unused storage without publishing an active resource. Step/key calls
with no model return a typed state error.

| Full child | Previous | On demand |
| --- | ---: | ---: |
| Near CODE | 63023 | 63071 |
| DGROUP | 43712 | 40288 |
| Stack | 8192 | 8192 |
| GET code | 4079 | 4079 |
| GET editor | 1544 | 1544 |
| GET field state | 206 | 206 |
| Minimum DOS bytes including PSP | 136528 | 133616 |

## Results and remaining failures

Actual8086 DOS component checks pass:84 for the on-demand variant and49 for the
unchanged static variant. Both cover the26-topic authored resource, scrolling,
search/F3, CP437 wrapping, missing/damaged files, exact VGA restoration and PSP
JFT restoration. New checks cover model/view allocation refusal, repeated opens,
file retirement while the viewer holds borrowed pages, refused early release,
failed view release followed by successful retry, and no residual allocation.

Two full-parent386/UMB source cases pass with the new child and CONNECTED guards:
startup and EXECUTE compilation through the retained-parent lease, GET input,
password transmission, ordinary keyboard return and hardware/resource checks.
A clean1044-file source export reproduces the exact artifacts and replays both
cases. Original binaries, private configuration and prior build objects are not
inputs to that export. The source prover now carries the deferred-storage option
and CONNECTED guards into its rebuild/replay.

The unobserved8086 heavy test now creates and preserves all six held512-byte
files; previously it failed before the second file. It then stops during
PROGRAM preparation with heap error8 at opcode9B, step20. Three nested graphics
children, WAIT, profile-switch and complete workload checks therefore fail.
This is progress on allocation, not a passing capacity result.

A full-parent Help attempt reaches the notice but reports memory service4 before
Help opens. Its hardware and executable preservation checks pass; Help/search,
next EXEC and the complete workflow do not. Earlier attempts stopped in stale
test adapters or invalid partial-PRM/port fixtures and are excluded. The notice
harness now accepts selected artifacts and CPU, uses the current connection
adapter, distinguishes zero-based directory ports from numbered COM settings,
and initializes the proved fields that modern startup validates. The general
adapter now binds its CPU/high-observer defaults through the current run API and
adds receive stimulation at the current online-byte boundary.

Next: inspect the exact buffer-preservation and PROGRAM/Help allocations, recover
more resident memory while retaining ownership/corruption checks and all existing
capacities, then repeat these same full workloads. Full GET, BBS, package and
physical checks must follow on the eventual accepted bytes. The prepared
Chat-mode package, installation, deployment selection and private files are
unchanged. Host mode remains the final implementation stage.
