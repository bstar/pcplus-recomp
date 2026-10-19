# ASPECT file commands in the maintained application

Both maintained compilers and the production `ASPECT.EXE` now support `EOF`,
`FCLEAR`, `FCLOSE`, `FFLUSH`, `FGETC`, `FGETS`, `FOPEN`, `FPUTC`, `FPUTS`,
`FREAD`, `FWRITE`, `FSEEK` and `FTELL`, plus `SET/FETCH FGETS_CRLF`.
The dispatcher supports 89 of 215 opcode slots; 126 remain unsupported.
Thirteen SET/FETCH selectors are implemented, with 243 explicitly unsupported.
This does not establish the complete ASPECT language or close an application gate.

The [native command/operand contract](ASPECT_SCRIPT_FILES.md) and
[owned DOS backend](ASPECT_SCRIPT_FILE_BACKEND.md) retain their distinct
comparison results: EOF writes 0/16 to an integer, stream errors yield 0/32,
open yields 0/1 and close/seek use the CRT result. `FGETS_CRLF` defaults to on.
Its recovered eight-byte SET/FETCH wrapper joins the original 572 command/helper
bytes, reusing the already recovered 34-byte generic boolean helper.

```text
integer count, at_end
long position
string contents
proc main
fopen 0 "WORK.DAT" "w+b"
if failure
exit
endif
fputs 0 "configuration"
ftell 0 position
fseek 0 0L 0
fread 0 contents 13 count
fgetc 0 at_end
eof 0 at_end
fclose 0
endproc
```

The file compiler grammar is checked independently against 245 authored original
compiler outcomes: 126 accepted ASX files match exactly and 119 rejected programs
remain rejected. This includes typed locals/parameters, strict integer handles
and counts, long seek offsets, destination types and optional separators.
`SET FGETS_CRLF ,OFF` is accepted by the original compiler and is preserved.
The full DOS compiler regression passes 1,480 cases against host output, including
these frozen sources, publication rollback and heap ownership.

File slots belong to the outer interpreter invocation. Initialization refuses
active owners and establishes the native default setting; the per-file ASX
cleanup does not close data streams. Therefore `EXECUTE` retains a numbered data
stream and its position. Final return, failed chained open, native operand/divide
error, budget exhaustion and cancellation run the common finish path, which
closes every owned data stream without replacing the script's comparison or
original error. The existing fatal native-error policy remains: the original
interactive returning-warning/unchecked closed-slot behavior is not implemented.

Validation now exercises the real application layers:

- The CPU component passes 6,090 cases, including every raw boolean byte and
  full-word FETCH, with a separate matching original-byte replay.
- The composed DOS runtime passes 1,127 cases/27,038 assertions, including all
  126 unsupported opcode slots and all 243 unsupported SET/FETCH selectors.
- DOS compiles thirteen authored ASP files, and their ASX matches host output.
  The actual interpreter runs 341 invocations in one process, passing 4,727
  assertions. Cases cover normal I/O, global string writeback, local/parameter
  file operands, retained slots through EXECUTE, failed EXECUTE, divide errors,
  invalid handles/counts, closed slots and budget aborts. Fifteen output files
  match independently fixed contents. Used near/far heap blocks and the inherited
  DOS handle table remain identical after warmup. An explicit ASP CLI child also
  invokes the DOS compiler and writes its expected file.
- The real terminal login child leaves a file open on normal completion,
  divide error and BIOS Escape during WAITFOR. All three exact files flush before
  working parent input resumes; the passive observer also checks JFT, sink,
  history, interrupt and device restoration.
- The isolated owned ENiGMA fixture passes all seventeen search/navigation checks
  after DOS-compiled ASPECT performs the login without keyboard credentials.
  A real slot-5 file survives deferred WHEN callbacks and finishes as the exact
  fourteen bytes `STARTAUTHREADY`. The normal custom search/index/DIZ/NFO route
  remains interactive after that script returns.

```sh
./tools/dev --command make test-aspect-script-file-compiler test-aspect-script-files
./tools/dev --command python3 standalone/test_aspect_script_files_dos.py --label unique-files-run
```

The [integration record](validation/aspect-script-file-runtime.json) binds the
current binaries, compiler/native/runtime/VM/parent/BBS results, refreshed DOS
package and fresh original-free source rebuild. The source-controlled VM harness's
first attempt counted a missing chained ASX as a failed data-file FOPEN; its
31 assertion failures are retained separately. Correcting that expectation did
not change product behavior.

The live ENiGMA decoder is still unchanged; the BBS result uses its staged patch,
exact selected owned modules/menus and generated files on loopback. It does not
claim live installation, actual-catalog or physical RS-232 Wi-Fi modem validation.
Broader original CRT equivalence, the remaining commands/recorder and all
whole-application requirements remain open.
