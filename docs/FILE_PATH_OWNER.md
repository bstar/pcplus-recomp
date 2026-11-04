# Directory and drive change foundation

The original resident helper at CS:75AE..75E7 is now recovered as 58 exact
bytes in `reconstruction/file_path/change.asm`. It takes one near path pointer,
requires DS=SS, and removes its argument on return. It calls DOS CHDIR first.
On success, an explicit drive prefix also selects the default drive. A failed
CHDIR can still accept a two-character drive-only string. The helper returns
only a Boolean, discarding the CHDIR error and ignoring drive-select readback.

This is a shared low-level helper. Its recovery does **not** establish the
complete original Alt-F7 dialog, the caller's validation, or DOS Gateway policy.
In particular, a helper's false success is not proof that the original UI
exposes the same behavior without an earlier check.

REA/Ghidra 12.1.2 examined a private, entry-anchored derivative of the original
2.01 executable. Only its header CS/IP changed; code bytes stayed identical.
The accepted body has 58 bytes and a callee-clean RET2. Evidence
`ev_418f78f341cf374fa5856ee502614a4c9e6e101ff06b567d57c25d24988056f7`
also identifies a resident caller at 0x335C. That caller and its caller at 0x3250
have unresolved application roles; they are not labeled Gateway from this
observation. The first anchor landed on the preceding RET and was corrected;
its one-instruction result is excluded. The decompiler's stack guesses are not
treated as source; instructions and the explicit DS=SS/stack tests establish
the helper interface. No analysis executable was run.

The recovered helper matches the original file region SHA256
`f622d114ce594d1b179e1fbb705f1d14a6d6de8fab747a47c778b7d32857ca0b`.
An explicit original-input CPU comparison executes the unmodified original
region and the linked helper at independent code/data placements. All 3,104
paired cases match DOS-call sequences, registers/FLAGS and stack cleanup,
including every leading byte, signed comparisons, drive-only and path forms,
and modeled CHDIR success/failure. Those kernel models do not establish real
DOS mutation semantics by themselves.

## Maintained guarded owner

`src/filesystem/path_owner.c` adds a bounded synchronous component around the
recovered helper. It is deliberately separate from recovery:

- Validate a disjoint near input/result, length 1..63, ASCII drive syntax and
  absence of controls, wildcards and UNC forms.
- Copy the request into owned padded storage because the native failure branch
  looks ahead three bytes, even for a short string.
- Query the target drive's saved directory before mutation, refusing a missing
  drive rather than trusting the native drive-only Boolean.
- Verify the selected default drive and returned directory after mutation.
- On verification failure, restore and recheck the target directory and prior
  default drive. Report `PATH_ROLLBACK`/`rollback_failed` if restoration fails.

The caller must honor failed rollback before dependent operations. This component
does not yet install a persistent application quarantine or any menu action.
It does not change PRM defaults, upload/download paths or existing open handles.
CHDIR failure has generic `PATH_CHANGE`; the original helper does not expose
the underlying DOS error. Drive-query/verification errors are reported separately.
The raw assembly kernel entries are internal boundaries, not validated public
path APIs. They assume the documented DS=SS and buffer contracts.

The source-only diagnostic passes 61 assertions under DOSBox-X's built-in DOS
on an 8086 CPU: independent drive/path observations, relative and drive-relative
changes, per-drive preservation, missing directory/drive, native false success,
bounded arguments/aliasing and two explicit verification/rollback faults.
The last fault leaves the changed context observable and reports failed rollback;
it does not silently claim restoration. Tests use disposable C/D directories
and an unavailable Y drive. Microsoft DOS 6.22, absent-media critical errors,
network redirectors and the physical machine remain separate gates.

The diagnostic reproduces byte for byte from eight public inputs in a fresh
Git-free tree without original executables or analysis databases. See
[validation/file-path-owner.json](validation/file-path-owner.json) for identities.

```sh
./tools/dev --command python standalone/build_path_owner.py \
  --output build/NEW-path-owner
./tools/dev --command python standalone/test_path_owner_dos.py \
  --program build/NEW-path-owner/PATH.EXE --output build/NEW-path-DOS
./tools/dev --command python standalone/prove_path_owner.py \
  --program build/NEW-path-owner/PATH.EXE --output build/NEW-path-source
```

Before enabling Alt-F7, recover its actual input/cancel/default-path contract,
connect foreground/file-claim admission and typed code-bank entries, retain
startup/configuration resource identities across directory changes, and test
online UART service/modal return. Gateway also requires original shell/EXIT
semantics and the existing PROGRAM ownership handoff. This component changes
neither the application package nor the installed machine; F15 stays open.
