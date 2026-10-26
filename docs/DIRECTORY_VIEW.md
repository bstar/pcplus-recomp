# Serviced Alt-D view — 2.01-LoC.4

The later [LoC.5 preview](DIRECTORY_PREVIEW.md) adds validated selected-entry
preview from the accepted baseline and actual session; adoption remains open.

The later [handle-inheritance correction](DIRECTORY_HANDLE_INHERITANCE.md)
protects active/uncertain directory handles from DOS children. Its package and
hash supersede this original view checkpoint's staging details.

The explicit `--directory-view` candidate connects the incremental reader to
the running terminal's command screen owner. Alt-D opens a path prompt, seeded
from the startup directory selector or PCPLUS.DIR. Enter opens the file
read-only. Arrows, PgUp/PgDn and Home/End browse ten-entry pages; F2 changes the
file and F5 reloads a completed page. Escape returns to the updated BBS display.
The reference's directory entry and Connection/L in the backtick browser reach
the same view, then return to their respective parent.

This is the browsing component, not the completed dialing chooser. It retains
the active target, serial/profile/translation settings, key/meta bindings,
directory selection/context and accounting identity. Dialing and adopting the
selected entry remain required. Ordinary, LoC.1, LoC.2 and LoC.3 builds retain
their previous executable hashes.

## Ownership and bounded work

The command view's frozen history length is zero. While it owns the screen,
the reader borrows the first 2,788 bytes of its existing far snapshot for two
complete pages. It borrows 512 bytes of the startup browser's existing near
page buffer for DOS IO. Bidirectional browser/editor/PROGRAM/view guards keep
these owners separate. The live history writer, live screen and visible view
remain distinct. No original executable or private directory is a build input.

Data reads happen only on foreground idle events, at most one DOS operation
and 512 requested input bytes per turn. Serial polling and parsing remain the
parent's responsibility between turns. Continuous receive traffic can delay
idle loading; a kernel/device call's duration is not bounded by this policy.
The complete file/probe/close transaction precedes page publication. Cancel
closes before the view releases; Alt-X/foreground stop also retire the reader.
An uncertain close prevents another directory load until the session ends.
Broader shared-file reservations and retained-handle/child-inheritance policy
remain required before general deployment.

Only entry numbers, bounded 24-byte names and 20-byte numbers are displayed.
Controls and DEL become dots; high CP437 bytes remain intact. Password,
script, keyboard, meta and note fields are not rendered or executed.

## DOS code and memory constraints

The new reader/view/filesystem code occupies 3,507 bytes in DIRECTORY_CODE.
The filesystem wrappers call the resident pinned DOS CRT through declared
adapters. DOS read has a mixed ABI: register arguments plus one output pointer
on the stack, consumed by RET2. Its adapter forwards that word explicitly and
removes the original only after returning to the bank. The memory validator
checks its instructions, target and MZ relocation. Three damaged controls
reject omitted cleanup, the wrong forwarded word and an omitted relocation.

The larger unshared parent passed browsing but failed the packaged nested
ASPECT source workflow with DOS error8. Its captured error screen remains at
`build/directory-view-start-diagnostic-20261025/drive/SCREEN.BIN`. That failure
was not waived. The candidate now shares full snapshots between the synchronous
browser and PROGRAM, and between the synchronous editor and serviced viewer.
All five roles retain their 4,000-byte capacity; only mutually exclusive roles
alias. Twelve ownership refusals and editor/viewer/PROGRAM restore cycles pass.

| Resource | LoC.3 | LoC.4 |
| --- | ---: | ---: |
| Near data and stacks | 64,096 | 64,272 |
| Resident code | 65,386 | 65,506 |
| Physical snapshot storage for five roles | 20,000 | 12,000 |
| Minimum retained parent bytes | 405,664 | 402,240 |
| History capacity | 63,000 | 63,000 |

No stack, queue, history or screen capacity was reduced. START's nested source
compilation now succeeds and produces the exact expected ASX and result. The
resident segment has only 30 bytes spare; further services need code banking
or existing callbacks rather than smaller feature limits.

## Accepted evidence

The [receipt](validation/directory-view.json) binds the frozen candidate:

- 31 linked inputs cover actual far-page/scratch leases, background UART
  parsing/replies, safe fields, navigation/reload, cancellation at open/read/
  probe/publication boundaries, missing/size/uncertain-close errors, screen
  ownership, foreground stop, Alt-X and both menu entry paths. Active configured
  planes, target, context, key/meta tables and transfer preferences stay exact.
- All 84 reference and 29 original-key inputs pass. Twelve shared-screen
  refusals and three PROGRAM, two editor and one viewer restore cycles pass.
- Real DOS8086 COM3/IRQ5 runs capture path/loading/first/last pages and the
  missing-file notice, receive a BBS cursor reply during loading, return to
  the updated live screen and ordinary keyboard, preserve the fixture and
  restore hardware. PNGs use the captured VGA ROM font.
- Stock ENiGMA login/editor semantics pass through the actual SynthModem
  proxy with 20ms input-byte spacing. The passive observer sees loading and
  both directory pages inside the editor before typing resumes; the final
  UNSAVED/OVR 01,08 check and no-saved-post audit pass.
- Packaged START/SETUP and reference-driven recording → DOS compilation →
  exact UART replay pass. The captured magenta splash identifies LoC.4.
- A clean 754-source export reproduces all ten package files exactly.
  The same ten files also reproduce from only committed sources at `cb2381a`,
  excluding pending worktree logger changes and ancestor Git metadata.
  Four older application controls and HEAD-source standalone browser/editor
  controls reproduce their unchanged executable hashes.

The earlier missing-file notice rendered incorrect bytes through a conditional
based-string expression. Explicit code-string branches fix it; the real DOS
error capture and linked missing/close-error cases validate the correction.
The development call-frame and memory failures remain distinct from accepted
evidence. These checks do not prove physical UART timing, arbitrary BBS
rendering, transfer integrity or complete F01–F16/application parity.

The staged package is `build/special-directory-view-05-20261025/PCPLUSSE`.
Its terminal SHA256 is
`d3eea16441617c80ca302a9985d8b01aea7a0590235a580d43865355e562f72f`.
No card was written and no live modem/BBS/network service was changed.

```sh
./tools/dev --command python3 standalone/package_special_edition.py \
  --build --custom-irq --directory-view --output build/NEW-directory-view
```

Next implement selection staging and the validated idle-line adoption/rollback
transaction, including canonical path identity, resource reservations, serial/
profile/translation, key/meta/script bindings, configuration baseline and call
accounting. Preserve browsing during an active call; do not silently drop it or
invoke the startup importer against a live session. Dedicated port/key-map UI,
other refused services, physical/card acceptance and the full plan remain open.
