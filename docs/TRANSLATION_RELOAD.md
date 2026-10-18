# Reloading the selected input table

Alt-F9, or **Alt-Z → Setup → Reload input table**, reloads the active translation
table without restarting the terminal. The command requires table mode 1 with
its normal FFh driver mask. It does not enable translation in modes 0/2.

The terminal stages exactly 256 bytes from the selected table file, checks EOF
and close, then asks for confirmation. Y applies that snapshot; other answers
keep the old table. A file or ownership error retains the table and asks for an
acknowledgement. Editing a file on disk never silently changes active mapping.
Queued raw input uses the newly accepted table after the foreground returns.
An early answer retained while output drains is read from the existing
foreground FIFO before BIOS. Following keys keep their order; a zero-valued
key is a valid answer rather than an empty-queue signal. Normal outgoing bytes,
parser continuations and terminal replies remain raw.

## Selection and ownership

Startup remembers the actual canonical source after a successful checked load.
This includes a default current-directory file, a PCPLUS-directory fallback or
an explicit `/X` file. Confirmed mode changes from PRMEDIT also remember their
chosen source. Reload uses that exact absolute path: subsequent DOS CWD,
environment, CLI-buffer or higher-priority-file changes cannot redirect it.
Removing that file produces an error; reload does not search for another file.
Selecting a different source still uses the existing startup/mode-change paths.

Canonical table paths must fit 63 bytes, including the resolved current directory.
This tightens the old startup check on relative names that fit 63 bytes before
resolution but exceed it afterward. Ordinary startup still opens the current
table before inspecting PCPLUS. A valid, damaged or inaccessible current file
does not inspect the environment; only file/path-not-found permits fallback.
Modes0/2 and explicit `/X` do not inspect PCPLUS.

The existing PROGRAM owner drains queued output and the physical transmitter,
pauses configured flow, preserves DTR and releases the UART interrupt before
the read/confirmation. Reload runs as its own local action; it launches no DOS
child, command processor or settings editor. The owner restores the live screen,
cursor, UART and receive flow afterward. Capture closes during this handoff,
following the existing PROGRAM policy. NONE flow cannot prevent an uncooperative
peer from sending while the foreground is paused.

The reload checks parser, macro, transfer, monitor, controller, snapshot and
ANSI-wait ownership before scheduling and again before acceptance. The PROGRAM
owner retains its BREAK, modem-state, video, drain/deadline and cancellation
checks. Decline cancels only the reload's stage. It cannot accept or cancel an
unrelated settings stage. No PRM field or mode/enabled/mask global is changed by
the reload operation itself. Alt-F9 is a maintained command; the original raw
classifier's Alt-F9 no-op remains unchanged in the recovery diagnostic.

## Validation

```sh
./tools/build test-translation-reload
```

[Validation report](validation/translation-reload.json) binds the frozen
executable to the following evidence. The 66 linked inputs execute the actual startup selector, new cdecl/far adapters,
menu/keyboard dispatch, checked reader, staged owner and UART/video handoff.
Hardware/DOS boundaries are modeled; product functions are not replaced.
Cases cover frozen default/fallback/explicit paths; four declines; size, read,
probe, close and access failures; snapshot acceptance after disk changes; late
ownership changes; invalid/wrapping/overlapping API arguments; independent
settings staging; connected state and queued input; TX/XOFF/TEMT/XON ordering;
canceled/timed-out requests and early queued confirmations/acknowledgements. Invalid initialization preserves an existing
active binding. Serialized unbound guards prevent use of uninitialized DOS BSS.

Eleven actual DOS workflows use production PROGRAM and DOS COPY or DEL to change
owned table files, then invoke Alt-F9 or the menu command. They verify accepted
and declined changes, missing/short files, explicit and environment-selected
sources and modes 0/2. Another DOS case changes CWD through actual COMMAND
actions, independently records the resulting directory and keeps using the
original source despite a conflicting table in the new directory. Exact resulting files and unchanged source/PRM files are
checked. Fresh peer text proves the effective mapping; actual cursor replies
and independent UART/vector/PIC/divisor samples verify service and restoration.
A controlled SOFT pause also retains an early Y during output drain. The
corrected prompt consumes it locally and the following ready text reaches the
peer intact. The earlier BIOS-only development build failed this identical DOS
recipe, consuming r and leaking y before eady; that failed run and its prior
isolated source identities are retained separately. The harness records
expected file mutations explicitly; other fixtures retain
their unchanged-file assertions. No test child or original executable is used.

The command adds two checked configuration entry pairs: 38 configuration pairs,
87 total. Independent damaged-frame/layout rejection now covers 187 mutations.
Near data/stack is 64,480 bytes; resident code is 65,298 bytes with 238 spare.
The parent retains 314,736 bytes including PSP. New owner logic remains in the
existing CONFIG_CODE module; the active path adds bounded near storage.

Opening XLTEDIT as a dedicated terminal command, full original settings/UI and
physical UART/Wi-Fi modem validation remain open. This component does not close
F05, F06 or any whole-application gate.
