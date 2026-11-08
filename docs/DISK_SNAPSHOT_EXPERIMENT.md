# Exact file-buffer snapshots and overlay feasibility

The optional disk-backed snapshot component passes its DOS checks, but the full
child **fails capacity admission**. Its extra resident code consumes memory
before PROGRAM preparation can release anything. It is not selected, packaged
or deployed. The [validation record](validation/disk-snapshot-experiment.json)
binds both the useful component result and the rejected application result.

This is a maintained memory-management experiment, not recovered vendor code.
It follows the [on-demand Help experiment](DEFERRED_HELP_STORAGE.md), which lets
the unchanged full parent open all six files but still runs out of memory while
preparing a nested program.

## Exact snapshots with bounded RAM

`disk_script_snapshots=True` in the experimental process builder selects the
new adapter. All six original512-byte stdio buffers remain allocated and owned
by their existing FILE objects. Instead of allocating six additional512-byte
copies, the adapter writes their complete contents to an exclusively created
DOS8.3 temporary file. Metadata snapshots still retain exact owner/FILE/prefix,
position, flags, mode and descriptor checks. No checksum replaces byte equality.

The file has a six-byte header and a slot tag plus512 bytes for every live slot.
After PROGRAM, comparison streams64 bytes at a time and checks every byte, tags,
header, short reads and final EOF. The backup is closed before launching a DOS
child and reopened only for verification. Empty snapshots create no file.

Temporary names are absolute paths in the captured current directory, using
`LPS00000.TMP` through a bounded exclusive-create search. Existing files are
preserved; there is no wildcard cleanup of preexisting names. Successful checks
and ordinary errors retire only the newly owned file. A failed unlink retains
ownership and refuses reuse until cleanup succeeds.

Close errors get one immediate retry before any descriptor allocation can
intervene. If both answers remain uncertain, the adapter retains the file,
refuses another snapshot and never later closes that numeric descriptor: another
owner could have reused it. The DOS process exit reclaims any remaining handle.
Two isolated fault runs verify both still-open and already-closed outcomes,
including safe use of a newly opened foreign file after quarantine. Their two
owned temporary files remain in ignored laboratory output for inspection.

## Results

- 642 low-level DOS8086 checks cover0..6 buffers, preexisting-file preservation,
  24 changed-byte positions across all six slots, changed owner data, bad header
  and tags, truncation/trailing bytes, create/write/read/close/unlink failures and
  cleanup retry. Sixteen additional checks cover uncertain-close quarantine.
- 8,108 integrated adapter checks preserve six guarded buffers, detect corruption,
  continue buffered reads and handle partial teardown with no duplicate buffer
  allocations or normal-path temporary residue. The original allocation-backed
  adapter passes8,819 checks, including its six snapshot-allocation refusals.
- The disabled full-child control remains exactly
  `9b1b5f98d6e2a4d64e4154a5d2f97240c1455787e5a7ab5d8d4c1cf37c473fe0`.

The final experimental child is
`70e385f722a5f44d9e58fa9a2689bf0f18bcab23fca2e1fd03517355d4984be4`.
Near CODE grows to64340 bytes, DGROUP40432 and DOS minimum135040, while the stack
remains8192. This adds1424 minimum bytes to the on-demand Help child. The heavy
unobserved8086 workload consequently fails earlier, at the fifth file's FPUTS:
error7, opcode41, step17, native4. It does not reach disk-snapshot creation or
the three nested graphics children. Component allocation savings therefore do
not establish a complete application memory saving.

## Next layout investigation: code overlays

A separate actual8086 DOS probe establishes a narrow prerequisite: a small-code
root with explicit far-cdecl bank entries can alternate A/B/A for100 iterations
through Watcom's standard overlay manager. All300 resident callbacks preserve
arguments and DS=SS; the same plain, non-overlay control passes. Early probes
incorrectly left the second declaration near. Disassembly identified that test
ABI error; the corrected plain and standard-manager controls pass. The
small-manager variant is not qualified for these far-entry banks.

Watcom documents separate standard and dynamic overlay managers; dynamic
overlays require special prologues and a big code model. The standard-manager
probe avoids assuming that the recovered assembly checkpoints satisfy the
dynamic manager's requirements. [Open Watcom Linker Guide](https://open-watcom.github.io/open-watcom-v2-wikidocs/lguide.html)

This is not an application overlay build or a memory-admission result. Next,
derive actual bank lifetimes and root callbacks, then qualify an opt-in layout
that shares space between inactive GET and PROGRAM/notice code. Keep interrupt,
UART, active return, checkpoint and recovery code resident. Verify every nested
callback and unwind path before allowing one bank to replace another. The loader
and shared-area overhead must yield an actual saving; the MZ/layout verifier
must account for overlay trailers explicitly. Passing gates must include the
same six-file/graphics/WAIT workload, full-parent Help, source compiler lending,
GET, cancellation, same-process recovery and later BBS/package checks.

The prepared package, installation, private settings/call history and Host-last
work order remain unchanged. Physical acceptance and full parity remain open.
