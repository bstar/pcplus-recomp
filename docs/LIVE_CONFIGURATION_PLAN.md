# Live configuration candidate transaction

The maintained DOS candidate decoder validates an in-memory PRM and optional
retained directory selection, then produces one624-byte candidate. It does not
modify active settings, launch setup or acquire/reconfigure the UART. This is
the staging boundary needed before the running terminal can apply setup edits;
that UI/hardware handoff is still open.

Build and check with the pinned Nix DOS8086 toolchain:

```sh
./tools/build test-live-configuration
```

`build/live-configuration/LIVE.EXE` is a source-only diagnostic, not the user
settings editor. Existing `PRMEDIT` and `TERMINAL /S @PCPLUS.PRM` remain the
supported offline and setup-before-connect workflows. [Alt-F10](SETUP_LIVE.md)
now opens the editor from the running terminal; saves currently affect the next
startup. The candidate decoder is also linked in the normal terminal's separate
[configuration code segment](CONFIGURATION_FAR_CODE.md).

## Shared directory semantics

`directory_live_decode()` now separates the existing directory interpretation
from DOS reads. Its inputs are a caller-owned1264-byte PRM and366-byte selected
entry/header/record. It retains the original maintained read policy: validate
global serial fields first, apply the record's port/baud/line/profile overrides,
then validate the effective serial settings. Unsupported bindings, HALF mode,
malformed strings and unsafe targets retain their prior statuses. DIRECT still
skips modem commands/responses and number expansion while retaining BREAK.

`directory_live_read()` keeps its original PRM-before-directory read order and
I/O error details, then calls the same pure decoder. Failed decoding never
commits any of the serial, modem or directory output plans. Inputs/results and
all output plans require disjoint nonwrapping near extents. No original parser
or private configuration is needed by either build.

A future live caller can retain the already-selected header/record instead of
silently rereading a changed directory or reentering the browser while connected.
The caller still owns that selection's lifetime and identity. The terminal now
[retains the complete header and logical request context](DIRECTORY_CONTEXT.md).
The candidate API is now linked in the terminal; a live owner must bind that context
and coordinate namespace and hardware ownership before committing edits.

## Candidate and change classification

`live_configuration_decode()` combines a40-byte serial plan,368-byte modem plan,
214-byte directory plan and16-bit change mask. With no active plan and no CLI
overrides it creates an initial validated candidate. With an active plan it
compares the new effective settings after applying the four CLI categories.
Invalid raw/global settings cannot be hidden by CLI or directory overrides.

The CLI mask is exactly the low four bits of the terminal option mask. Selected
categories retain the active effective port/base/IRQ, complete32-bit baud, line
format and/or flow flags. The caller must supply current effective settings,
including any autobaud change, rather than assuming startup values remain live.
All active serial fields are validated before they can enter a candidate.

| Change bit | Meaning |
| --- | --- |
|0001|Port, standard I/O base or IRQ|
|0002|Baud, including high word|
|0004|Parity/data/stop format|
|0008|Software/hardware flow|
|0010|Terminal profile|
|0020|Five configured attributes, wrap or scroll|
|0040|Mapping pause character or character delay|
|0080|Modem numeric fields, commands or expanded responses|
|0100|Directory selection/record metadata|
|0200|Raw BREAK delay|
|0400|Dialing mode or expanded target|

Mapping delay/pause changes also set the modem bit because both consumers use
those values. BREAK is separate. Modem strings compare only through their first
NUL; changed unused tails do not request a semantic runtime update. Unknown PRM
bytes are not applied or rewritten. Raw directory metadata differences remain
classified, including passwords as private metadata; no transmission occurs.

A candidate is not a commit or permission to change a connected transport.
Future policy must distinguish transport/profile/target changes, coordinate
flow and IRQ ownership, preserve active screen/parser modes and update the
intended reset baseline. This component deliberately makes no successful live
reconfiguration claim. Full F02/F06 and the application plan remain open.

## Evidence

The actualDOS16 C/ASM replay forbids all interrupts and IN/OUT. It checks exact
candidate bytes, every CLI-category combination with and without a directory,
all200 selected entry numbers, semantic change flags, DIRECT and legacy target
behavior, malformed source/active inputs and independent guards on the newly
public directory API. Rejected candidates and all inputs remain byte-identical.
A code hook measures stack use and requires it below the terminal's8KiB budget;
this measures API calls, not a future parent/UI/ISR composition.

A separate DOS C-runtime test compares the real file-reading owner with the pure
candidate decoder on generated PRM/DIR files and verifies that both fixtures
remain unchanged. Existing311 linked directory checks retain their independent
expected bytes, file-read ordering, failure statuses and atomicity assertions.
Full terminal regression and source-only rebuild reports are recorded separately
from this new diagnostic. No original executable, private file, live UART or
physical modem is an input to the candidate replay.


The original staging checkpoint passes389 candidate/API inputs in10 groups and311
existing directory inputs. Maximum observed candidate-call stack use is2992
bytes. All43 terminal regression commands pass on terminal12bdea77, and the
isolated checkout reproduces59 byte-identical outputs, including the separate
candidate diagnostic065c93ba. Hash-bound combined evidence is recorded in
`validation/live-configuration-plan.json`. Those hashes describe that historical
checkpoint. The newer configuration-segment tests execute the candidate API
inside the normal terminal as well; see [CONFIGURATION_FAR_CODE.md](CONFIGURATION_FAR_CODE.md).
