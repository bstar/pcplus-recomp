# Gateway private file handles

The optional `--gateway-handles` parent adds a retained private-JFT bracket and
read-only queries for the four binary file owners and printer owner. It implies
the direct COMSPEC resolver and path-control prerequisite. Alt-F4 remains
unbound: this checkpoint does not integrate the foreground Gateway transaction.

## Lifetime contract

The banked `process_handles_begin/end/recover` API uses far cdecl, DS=SS and
IF1/DF0. Its initialized 36-byte lease lives in FILE_CODE, outside DGROUP, and
supports one to seven distinct open descriptors. BEGIN validates the near input,
PSP signature, table capacity/address, closed/duplicate entries and overlap with
its own storage before masking any JFT entry. It saves all selected entries
before publishing the lease and masks them with FF without closing their SFT
references. The parent retains the same underlying files and positions.

No parent stream IO may occur between BEGIN and END/RECOVER. The intended child
path uses raw DOS EXEC. END must run after failed EXEC as well as success and
before parent IO resumes. It restores the saved entries even when current PSP,
table metadata or selected entries changed, reporting a nonzero result that the
future caller must quarantine. RECOVER additionally accepts the original saved
entry during interrupted mask/unmask operations. Structurally invalid saved
state is refused without writing through it; the active lease remains visible.
This is not an arbitrary-memory corruption repair mechanism or a DOS security
sandbox. A child can still explicitly open files by name.

`capture_file_child_handle(index)` selects capture, snapshot, monitor or history
(indices 0..3). `printer_device_child_handle()` selects PRN. These return a
borrowed descriptor, FFFF for no open owner, or FFFE for uncertain/inconsistent
ownership. They perform no DOS calls, mutate no owner state, and transfer no
ownership. Capture reservation activity also refuses the query. Existing
initialization cookies allow an unused owner to report no handle without
interpreting dirty snapshot BSS. An open failed owner is refused. These queries
are prerequisites for collecting and protecting descriptors, not a substitute
for flushing/draining the application adapters or guarding their transactions.

## Evidence

The receipt is [gateway-handles.json](validation/gateway-handles.json).

- 56 linked CPU cases execute the actual parent functions. They cover one to
  seven handles, reentry, invalid spans/tables/descriptors, changed metadata,
  partial restoration, corrupt saved-state refusal, IF/DF/DS guards, and the
  five actual sink-owner implementations. DOS/filesystem endpoints are modeled
  in these tests. Owner snapshots survive a five-handle lease unchanged and
  the same owners can write and close afterward.
- Five actual DOS8086 workflows with FPU disabled pass 35 external checks plus
  the host's internal assertions. A synthetic child attempts to write and
  close inherited descriptors and creates its own file using a freed descriptor
  number. Protected parent files retain their position and become exactly AB;
  the unprotected positive control becomes AX. Two-handle isolation, failed
  EXEC and interrupted-cleanup recovery pass. The host verifies its actual MCB
  size and returned retained-parent floor. This standalone probe does not run
  the application capture/printer/UART transaction.
- The new parent passes the existing 33 direct-COMSPEC cases and ordinary HOOK
  resolver's 28 cases plus 14 boundary/cancellation cases.
- A fresh Git-free tree reproduces the parent exactly from 584 declared public
  source inputs. The disabled parent reproduces the previous e2204a0f image;
  ordinary ASPECT reproduces 23caac93. No original executables are build inputs.

Parent: `build/gateway-handles-owners-20261104/TERMINAL.EXE`, SHA256
`a327e2a1cc5847fe0cc3f9390bdd719248ccecd9eaa44f77853b0d4619ca55f8`.
Near data/stack remains 65,488 bytes (48 spare), resident code 65,332 bytes,
FILE_CODE 5,423 bytes, and retained parent floor 28,735 paragraphs including PSP.
The queries add only 106 and 64 far-code bytes to capture and printer objects;
their existing near code and data segment sizes remain unchanged.

## Remaining integration

The optional [Gateway file transaction](GATEWAY_FILES.md) now composes these
queries and the lease with direct COMSPEC and capture flush, including actual
application-file DOS evidence. Foreground and serial integration remain open.

The launch owner still needs to gather the descriptors at a revalidated idle
boundary, preserve/drain capture and printer adapters, bracket actual COMSPEC
EXEC, restore on all return paths, and quarantine uncertain restoration before
resuming any owner. Do not reuse PROGRAM's stop-capture/close-printer behavior.

The distinct Gateway action, no-key-wait return, screen/mouse/trap lifecycle,
IF0 child-UART quiet admission for its new job kind, and sustained serial/flow/
DCD/FIFO/DTR behavior remain required. The original keeps its ISR live; current
PROGRAM detaches. These tests do not choose or prove the final Gateway serial
policy. BBS integration, physical modem acceptance and full parity stay open.
No deployment selection, physical machine, network, boot or ATA setting changed.
