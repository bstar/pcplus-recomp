# Checked screen-file snapshots

Press **Alt-G** in the maintained DOS terminal to append the current screen to
`PCPLUS.SCR` in the current directory. A successful action shows `Screen saved`.
It does not wait for another key. Repeated snapshots append another25 rows;
existing data is preserved. Text capture may remain open or held throughout.

This connects the actual recovered3446/64b8 row-selection and character-copy
instructions to a maintained checked file writer. The native3496 writer and
Alt-G wrapper are separately reconstructed and tested, with their original
unchecked FILE/UI boundaries retained. See
[native source, contracts and REA evidence](SCREEN_SNAPSHOT_NATIVE.md).

## File format and frozen view

Each of25 rows contains leading/interior spaces and character bytes, with
trailing spaces removed, followed by CRLF. Attributes and ANSI sequences are
omitted. NUL cells become spaces; CP437 bytes remain unchanged. Blank rows are
exactly CRLF. There are no timestamps, headers or separators between snapshots.

The native status-row special case is preserved: when the footer is present,
a final1Ah byte on row24 becomes a space before CRLF. With the footer hidden,
the native special ordinal is25 and no captured row gets that replacement.
The maintained caller guards empty rows instead of reading before the buffer.
It does not strip1Ah from other rows or from an existing file prefix.

Before reading, the existing transient connection/capture notice is restored.
The native helpers select physical video or the validated far shadow screen.
All rows are read into a private2000-byte far character image before any DOS
file IO or foreground serial polling. The UART ISR remains enabled. Subsequent
row writes use that frozen image while servicing UART transmit, flow and modem
state. Incoming bytes remain queued for the ordinary parser afterward, so later
display changes cannot mix rows from different views into one snapshot. This
is foreground consistency, not a hardware/DMA-wide atomicity guarantee.

The original8192-byte shadow and4096-byte history arrays retain their complete
sizes. The new image has its own static extent and segment relocation. PROGRAM
retains the maximum end of STACK, shadow/history and the frozen image; linked
and actual DOS child-allocation tests check all three far-buffer canaries.

## Independent checked owners

Text capture and snapshots use separate96-byte ownership/result records and
fixed private descriptors, sharing one implementation. Before opening, DOS
Truename resolves the normalized DOS83 path to an absolute identity. Both owners
compare identities, including relative/drive/absolute aliases, against open or
uncertain handles. An internal collision returns busy without resetting either
record or reopening/writing/closing either file. Opens use that admitted absolute
identity. DOS3 or newer is required for Truename and exclusive creation.

An existing writable regular snapshot file opens write-only and seeks END on
that handle. Only actual file-not-found permits exclusive NEW creation; a raced-in
file is never truncated. Both owners reject devices, traversal, unsafe near
spans and source ranges overlapping either owner's state. This excludes conflicts
between these two owners, not external writers, host mount/inode aliases or
concurrent namespace remapping. Append remains nontransactional.

Every row write must accept the exact length; positive short/error writes stop
further output and retain the accepted prefix. Acquired handles close once.
Ambiguous close cannot be retried/reset, and blocks a child PROGRAM launch.
Genuine write/close failures show `Screen error`, retain the partial file and
remain observable at normal shutdown through the existing storage-error level12,
unless an earlier terminal error has precedence. Rejected opens without a handle
show `Screen denied` and do not become shutdown failures. A complete snapshot
contains25 checked rows only after its checked close succeeds.

## Supported live geometry and remaining work

The current live path accepts mode3/page0,80 columns and25 rows, with checked
video/shadow pointers and stride. Native nonzero CGA retrace waits are unbounded,
so that setting is rejected before reading/writing. Even the native notice
renderer can wait for retrace: a CGA denial therefore returns quietly and records
`terminal_snapshot_last_action=2` rather than drawing through that renderer.
The action record is0 untouched,1 saved,2 denied or3 failed. Other supported
geometry denials and normal file errors use the transient notice window.

There is no parser or BIOS-key dispatch during the finite row-copy/write action;
Alt-X queued while it writes is handled afterward. Returned DOS errors and RX
overflow are checked, but DOS kernel IO itself is synchronous. Physical device
latency/critical errors, other video geometries, complete viewport/UI modes,
printer output, raw monitoring, ASPECT and the advertised DMP format remain
separate application work. This does not close F10 or the full rebuild plan.

## Verification

```sh
./tools/dev --command make test-snapshot test-capture-owners
./tools/dev --command python3 standalone/check_terminal_snapshot_live.py
./tools/dev --command python3 standalone/test_far_storage_dos.py
./tools/dev --command python3 standalone/test_terminal_snapshot_dos.py \
  --sha256 SHA256_OF_TERMINAL_EXE --label MY_FRESH_RUN
```

The native module has381 exact bytes,24 linked CPU cases,24 optional original
instruction comparisons and an actual8086 DOS self-check. Independent DOS file
tests cover both-owner aliases, private-state overlap, canonical failures and
kernel-kept/kernel-released ambiguous handles. The live linked suite executes
the actual row helpers, frozen-image/file/PROGRAM paths with only kernel and
hardware boundaries modeled. It includes NUL/SUB/shadow coverage, injected late
UART/video changes, partial writes and unsupported-CGA bounded return.

The separate11-case UART/DOS suite uses an independent25-row byte oracle,
actual Alt-G BIOS input, CPR/DSR, BIOS cursor/mode/page and UART/PIC/vector
snapshots. It confirms exact append output, CP437, exclusion of an earlier
notice, continuing/held capture after both successful and conflicting snapshots,
and readonly preservation. Its actual mode3 results do not establish physical
NUL injection, other video modes, host disk faults or physical hardware behavior.
Public validation retains each runtime identity and historical run separately.
