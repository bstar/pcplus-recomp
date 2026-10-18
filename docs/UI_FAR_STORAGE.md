# Far storage for private UI screens

Three independent screen copies now live outside DGROUP: the directory browser,
its nested record editor, and PROGRAM's terminal screen. Each owns a full4000
bytes in the uninitialized `UI_STORAGE` segment, grouped explicitly as `UI_GROUP`.
They are not aliases of one shared scratch frame. Opening the editor preserves
the browser's saved terminal screen, and a DOS child cannot acquire the parent’s
screen storage when PROGRAM releases surplus memory.

The8b38144e checkpoint reduces shared data/stack from64,368 to52,368 bytes,
leaving13,168 bytes below the64KB limit. The file shrinks from105,050 to93,290
bytes compared with bdeb347c; the loaded module shrinks by11,776 bytes. Total
static memory does not shrink: the frames moved to another segment, while the
additional helpers add224 code bytes. The resident code segment now uses62,828
bytes. Both code and shared data still have finite real-mode limits. The near
headroom is capacity for more definitions when relinking, not an allocated heap
beyond STACK: the far UI region immediately follows the current stack extent.

## Formats and calling conventions

The browser and editor retain the native packed-cell format: each character/
attribute pair is stored in the order returned by `ui_read_packed`. The new
`terminal_screen_save_far` and `terminal_screen_restore_far` helpers use those
recovered cell readers/writers, including the original CGA polling path. They
accept count in AX, video offset in DX, and an explicit ES:DI save destination or
ES:SI restore source. They preserve registers and return CF1 for an invalid
count or wrapping extent. Count zero performs no I/O; an extent ending exactly
at64KB is valid. The caller supplies allocated, nonoverlapping storage.

The shared stack convention remains DS=SS at each call boundary. Native cell
reads still borrow DS for video access internally and restore it before return.
The wrapper does not switch DS to the screen buffer, which would invalidate
near stack arguments in the recovered helpers. CGA waits retain native hardware
behavior; software tests do not establish physical timing or make a stuck
hardware status port bounded.

PROGRAM's private frame retains its existing raw character/attribute format.
Its save/restore copies use the far buffer's segment explicitly and restore DS
before returning to near C/assembly services. The original execution, UART and
screen-restoration policies remain in force.

## Allocation and retention

Three relocated segment words identify the private frames. The actual terminal
builder inspects the MZ and map to require4000-byte, nonwrapping, pairwise-disjoint
frames outside DGROUP, native shadow/history, frozen printing and executable
code. Every segment word must have a real MZ relocation. The frames are load-time
allocation, with no initialized screen bytes serialized into the file.

PROGRAM computes its retained parent extent from the near stack, native far
storage, frozen screen, and each of these three frame ends. It retains them all
rather than depending on one particular linker ordering. The DOS child test
checks the parent MCB, samples all three complete frames before/after allocating
and filling16KB elsewhere, and verifies disjoint allocation. It leaves the
PROGRAM frame untouched so the parent's normal screen can still be restored.
The samples are byte sums, not cryptographic hashes; the MCB extent and explicit
allocation checks independently establish ownership for this controlled test.

## Evidence

[The validation record](validation/terminal-ui-storage.json) binds the terminal,
standalone editor/browser, source manifests, linked tests, actual DOS results and
retained artifacts. The helper tests cover all2000 cells, NUL/SUB/high bytes,
nested restoration, monochrome and active pages, alternating CGA ports, exact
64KB ends and invalid bounds. Eight altered MZ/map fixtures must be rejected for
wrong/missing relocated pointers, owner aliasing and truncation; they are inspected
without being executed.

All37 terminal regression commands pass on this checkpoint, alongside six
standalone editor DOS cases, five browser DOS cases and14 dedicated-print DOS
cases. The independent helper test covers six groups/2031 inputs. A fresh
source-only build reproduces all57 workspace outputs.

The standalone browser/editor DOS tests and terminal regression exercise actual
BIOS keyboard/video and nested edit/save/cancel paths. PROGRAM tests cover child
success/failure, serial handoff and screen restoration. Hardware/kernel models,
actual DOS runs and the isolated source rebuild remain separate evidence types.
Latest BBS editor tests retain their own earlier executable hashes; this storage
change does not relabel those results as a new BBS run.

```sh
./tools/build terminal directory-editor directory-browser
./tools/dev --command python3 standalone/check_ui_screen_far.py
./tools/build test-directory-editor test-directory-browser
./tools/build test-terminal
./tools/dev --command python3 standalone/record_ui_storage.py
```

This migration supports further application reconstruction. Complete original UI,
help, settings, scripting, protocols, dynamic overlays and physical-machine
validation remain open in the full feature plan.
