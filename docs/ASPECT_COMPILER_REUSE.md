# Reusing PCPlus after a compiler-bridge error

Four emulator workflows now keep the same connected PCPlus parent running after
a source-startup error, then launch a different source through the actual
Alt-F5 Script Files prompt. The second interpreter compiles the new source,
receives fresh ANSI traffic, completes GET, sends its value/password and returns
to ordinary parent keyboard input. No application bytes changed.

The [validation record](validation/aspect-compiler-reuse.json) binds exact
artifacts and observations. This extends
[close-error handling](ASPECT_COMPILER_CLOSE.md) with actual use after an error.

## First failed interpreter

The first startup source would transmit BADFIRST if executed. An owned observer
supplies one of four precisely scoped failures already covered independently:

* A backup write error after one real 4096-byte write.
* A close error reported after DOS actually closes the complete backup, before
  any memory lending or compiler EXEC.
* The same closed-handle error after verified parent restoration.
* Backup unlink denied after the real close and verified restoration.

The first interpreter must exit with I/O5. Before rearming any observation, the
fixture records its completed EXEC header, child error/compiler count, parent
PSP/DS and byte equality of parent JFT, file owners and exit/return history.
The ordinary display-preservation and valid-memory cleanup checks still apply.
No instruction from the failed source may run.

## Actual second launch

After the failed interpreter returns and the parent is inactive with no pending
program action, the owned timer fixture supplies Alt-F5 through the BIOS keyboard
queue. It waits for the exact rendered Script DOS 8.3 path prompt before typing
GOOD.ASP and Enter. These are input events, not direct calls to the launcher or
writes to product state. The matching PCMETA and PCLINE modules are included
from the same parent build, so this also uses the real shared menu arena between
compiler leases.

The fixture preserves the first observation and rearms only its own counters.
It disarms its one-shot failure for the second launch; it does not reset product
memory, CurrentPDB, allocation metadata, kernel state or file handles.

GOOD.ASX is absent initially. The second real compiler EXEC must occur under the
same parent PSP/DS, a fresh kernel token2, its actual ASPECT child owner/DS and
the trusted parent keep/full extents. At that boundary the parent must genuinely
be lent: phase2, valid0, busy0. The published GOOD.ASX must match the independent
host compiler exactly, and the second child must exit successfully.

When the first error left LPM00000.TMP, the next lease must skip that name:
sequence2 is required. The original complete backup must remain with its exact
size and captured CRC after the successful second lease. When preparation
cleanup removed the first backup, the new reservation uses sequence1 and no
backing file remains. Compiler logs/staging files must retire in both cases.

The second source sends SECONDREADY; only then does the owned peer send a fresh
ANSI banner and login prompt. This requires actual renderer history progress,
query replies and GET admission rather than reusing old prompt data. The final
password, post-return cursor query and ordinary ready keyboard text are required.
There is one modem initialization/dial attempt throughout; no PCPlus restart or
new connection substitutes for same-parent reuse.

## Harness and limits

Run the pinned toolchain with matching experimental artifacts:

```sh
./tools/dev --command python standalone/test_aspect_get_vm_dos.py \
  --parent-dir build/compiler-bridge-parent-recovery-final-20261108 \
  --child-dir build/compiler-bridge-child-256-20261108 \
  --get-compiler-dir build/get-compiler-enabled-20261107 \
  --source-lease-reuse-cases --allocation-probe --watchdog \
  --output build/compiler-bridge-reuse-new
```

A clean 1042-file public source export rebuilds all six application artifacts
byte-for-byte and replays ten normal-return cases: these four reuse workflows,
two normal source controls and four close-error regressions. Four unexpected
termination cases replay separately as expected fatal stops. The prior broader
regression evidence remains scoped to the same unchanged artifacts.

Use a new output directory. A bounded diagnostic captures only observer-owned
sample bytes and VGA if the input sequence stalls. It is not acceptance evidence
without the final successful assertions. Initial experiments omitted the menu
module, then used an obsolete File/A sequence against the current command menu;
both timed out before the second launch and are excluded from acceptance.

This covers two separate ASPECT lifetimes under one PCPlus process, not recovery
inside one interpreter. It does not prove every error/retry composition, uncertain
close leaving an open handle, corrupt-backup repair, all shared-arena consumers
or all video modes. Physical Boca/SPA2102/SynthModem/LoC Enigma and Synchronet,
selected package acceptance and full language/application parity remain open.
The DOS installation, boot profiles, private configuration and call log are
unchanged.
