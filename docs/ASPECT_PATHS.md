# ASPECT filesystem commands

The maintained host and DOS compilers and `ASPECT.EXE` now support `CHDIR`,
`MKDIR`, `RMDIR` and `DELETE`. Each takes one string literal, string variable,
local string or string parameter. Parentheses, commas, numeric operands and
string expressions are rejected, matching the original compiler's authored
56-case oracle: 24 accepted programs and 32 rejected programs.

```text
string workdir
proc main
workdir="WORK"
mkdir workdir
if failure
exit
endif
chdir workdir
mkdir "CACHE"
chdir ".."
rmdir "WORK\CACHE"
rmdir workdir
endproc
```

The command handlers and DOS services assemble to 210 exact native instruction
bytes, including the reused error mapping code. Ordinary builds use source,
recorded hashes and a 20-entry numeric DOS error map; no original executable or
REA database is a build input. The runtime now supports 76 of 215 opcode slots;
139 slots and the remaining language/UI work are still unfinished.

The comparison result named `failure` preserves the original distinctions:

| Command | Comparison result | Additional behavior |
| --- | --- | --- |
| `MKDIR` | 0 on success, -1 on failure | Updates the backend's native DOS error/errno fields on failure. |
| `DELETE` | 0 on success, -1 on failure | Same native error mapping; no wildcard expansion. |
| `RMDIR` | 0 on success, raw positive DOS error on failure | Leaves the native errno fields unchanged. |
| `CHDIR` | Unchanged, including on failure | Changes the current directory and, for a drive-qualified path, selects that drive. |

Do not use `failure` to determine whether `CHDIR` succeeded. Its recovered
service returns a separate result that the original command discards. The bare
drive fallback is also retained: some invalid two-character drive strings reach
DOS drive selection without a verified selection result. This is native
behavior, not validation added by the maintained compiler.

The backend owns its error fields independently of the compiler/runtime C
library. The supported production platform is DOS 3 or later; the native mapper's
older-DOS branch is characterized separately by component tests. Success leaves
previous error fields intact. DOS current-directory/default-drive changes survive
child exit: the actual test changes to `C:\ONC` and observes that directory after
`ASPECT.EXE` returns. Scripts must deliberately restore directories when needed.

Validation includes 1,578 CPU cases covering every 8-bit DOS error plus extended
errors, drive selection/fallback and complete non-stack data/ABI state. A separate
private-original replay matches all 1,578 cases. Four actual 8086 DOS scripts
compile with `ASPCOMP.EXE`, produce bytecode matching the host compiler and pass
19 status checks against fresh mapped drives. They verify relative hierarchy,
file deletion, preserved nonempty-directory contents, drive/CWD retention,
CP437 paths and global/local/parameter operands. The terminal login-child test
sends its password marker only after its relative directory hierarchy is removed,
then checks resumed parent input and retained JFT, sink, history and hardware
ownership through the existing passive observer.

```sh
./tools/dev --command make test-aspect-paths test-aspect-path-compiler
./tools/dev --command python3 standalone/test_aspect_paths_dos.py --label unique-path-run
```

The [validation record](validation/aspect-paths.json) binds the native/compiler
evidence, real DOS scripts, login handoff, full runtime/compiler regressions,
package and fresh source-only rebuild. The first filesystem attempt is retained:
its authored script used an unsupported global initializer and stopped at
compilation. Moving that assignment into `main` corrected the test; no product
change was needed for that failure. The first clean rebuild also identified
absolute source paths in six OMF object headers; using relative source names
corrected their reproducibility without changing the linked DOS executables.
Trusted scripts and ordinary DOS error paths
are covered here; arbitrary bytecode safety, filesystem crash recovery, physical
modem behavior and all whole-application gates remain open.
