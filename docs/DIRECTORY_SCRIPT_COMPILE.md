# Compile a directory source without executing it

The opt-in `--directory-compile` build adds **C** to the directory preview.
R remains the read-only resource check and preserves independent capture.
C uses PROGRAM kind 8 to stage KEY/KBD/XLT/script resources privately, compile a
SOURCE candidate through the sibling ASPCOMP.EXE, then publish the resulting
bundle. No script is executed, active settings adopted or target dialed.

```sh
./tools/dev --command python3 standalone/package_special_edition.py --build \
  --custom-irq --directory-compile --output build/compile-package
```

Already-compiled and blank selections need no compiler child. A source
candidate retains its canonical ASP identity and full-stream fingerprint.
The parent claims source, target ASX, helper and the sibling LPC?????.TMP/BAK
namespace before IO. A target that appeared since staging refuses before EXEC.
The source fingerprint must match before and after the child. Successful child
termination alone is insufficient: output must open, pass the loader header
check and close successfully. This is not complete bytecode validation.

Compilation uses direct process_run with an explicit bounded tail, not a shell
or ASPECT invocation. C follows the existing child capture-close policy; R does
not. Existing held storage/claim ownership still blocks child admission. The
actual PROGRAM owner keeps UART IRQ/IER/RTS/vector quiesced for parent IO and
regains the full allocation before checking output. Compiler diagnostics appear
on the normal child console. The existing popup ancestry closes before IO.

The output candidate uses frozen offsets 6700 through 8724. The accepted bundle
is unchanged on failure, including failures after successful compilation or a
late session/baseline comparison. Source/output recovery state occupies its own
256-byte far block immediately after the full 8192-byte erase shadow, outside
both history allocations and the temporary child memory loan. A held claim can
therefore outlive the candidate lease without pointing into reused UI memory.

An uncertain read close or claim release retains ownership and blocks further
EXEC. Unexpected output following a failed child, a changed source after the
child, or damaged owner state also refuses reuse. Initialize never resets active,
held or invalid state. Pure EXEC admission allows only the owner's explicit
child phase while active; no successful compile is simulated by those guards.

Scratch identity matching includes longer canonical names produced by a short
relative capture request. Native tests cover a 63-byte source and a conflicting
scratch identity longer than 63 bytes. Reservations protect this process's
owners; they do not lock an external writer, authenticate a helper or prevent
host namespace replacement. CRC32 is a damage fingerprint, not authentication.

The [receipt](validation/directory-script-compile.json) binds application tests,
component tests, linked guards and exact committed-source rebuilds. Component
acceptance uses the real source-built compiler; a separately identified DOS
fault child tests source mutation, missing output, nonzero exit with output,
and a bad compiled header. Its DOS spawning adapter is explicit. Separate
foreground application tests exercise the actual process_run memory, UART,
IRQ/vector and popup handoff. Authored scripts contain a file-write marker that
must remain absent after compilation.

Selection adoption/UART/resource publication and dialing remain open. The full
F01–F16 application, independent complete rendering oracle, physical Boca/
SPA2102 and card acceptance remain open. No live BBS, SynthModem or card is
modified by these tests; the ENiGMA fixture is isolated on loopback.
