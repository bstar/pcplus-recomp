# Native ASPECT script-file commands

Thirteen original command handlers and their three shared helpers are now
recovered as readable assembly: 572 exact instruction bytes, sixteen source-built
flat command/helper files and two relocatable OMF objects.
The [application integration](ASPECT_SCRIPT_FILE_RUNTIME.md) now connects these
commands and the additional eight-byte FGETS_CRLF SET/FETCH wrapper to both
compilers and the maintained 89-slot runtime. The original 572-byte recovery
record remains a separate historical component checkpoint.

The native interface uses six numbered slots, 0 through 5. The recovered slot
reader delegates to the existing bounded integer reader. The original compiler
accepts integer variables and integer constants, including out-of-range constants;
the runtime range policy determines their outcome. The frozen authored compiler
corpus contains 229 programs: 119 accepted outputs and 110 rejections. It includes
local variables and parameters, commas, missing arguments, wrong types, expressions
and seek/count limits. This is original-compiler evidence, not maintained-compiler
conformance at that initial checkpoint. Current compiler conformance is recorded
by the linked application integration.

| Command operands | Native effects |
| --- | --- |
| `EOF slot integer` | Stores the raw FILE EOF bit, 0 or 16, in the integer. Preserves comparison status. |
| `FCLEAR slot` | Clears FILE EOF/error bits. Preserves comparison status. |
| `FCLOSE slot` | Stores the CRT close result as comparison status and clears the slot even on failure. |
| `FFLUSH slot` | Flushes, then stores the raw FILE error bit, 0 or 32, as comparison status. |
| `FGETC slot integer` | Stores the CRT character/EOF result in the integer, then updates the error-bit comparison. |
| `FGETS slot string` | Reads at most 80 bytes, applies the native CRLF/control-Z rules and commits the destination. Updates the error-bit comparison. |
| `FOPEN slot path mode` | Closes an occupied slot first, copies/lowercases the mode and opens the new path. Stores 1 if open failed, otherwise 0, as comparison status. |
| `FPUTC slot byte` | Writes one bounded byte, then updates the error-bit comparison. |
| `FPUTS slot string` | Calls the CRT string writer, then updates the error-bit comparison. |
| `FREAD slot string count integer` | Reads a bounded 0–80 byte count, inserts a NUL terminator, stores the actual byte count and commits the destination. Updates the error-bit comparison. |
| `FWRITE slot string count` | Writes the bounded count, then updates the error-bit comparison. The comparison is not the byte count. |
| `FSEEK slot long origin` | Uses bounded origin 0–2 and stores the CRT seek result as comparison status. |
| `FTELL slot long` | Stores the full DX:AX position in a long variable. Preserves comparison status. |

`FGETS` depends on the native FILE descriptor's text-mode flags, EOF flag and
the `FGETS_CRLF` setting. The recovered handler is tested on empty, short,
80-byte, LF, CRLF and control-Z inputs, including failed reads and both setting
values. The real CRT's translation still needs validation. The shared lookup
also has a checked closed-slot warning path and a fallback FILE pointer. Its
native initialized prefix has write flag 2 and descriptor 2, consistent with
stderr; that observation does not establish the full warning/fatal policy.
The unchecked null-slot behavior is characterized only at lookup, without
claiming it is safe to call a CRT function on that result.

The 5,828 CPU cases execute the real source-built command/helper instructions.
A separate original-byte replay matches all 5,828 cases. Operand readers,
string-library calls, CRT operations and the returning warning boundary are
explicit models. Assertions compare complete non-stack DS memory, stack cleanup,
preserved BP/SI/DI, DS=SS, DF and ordered boundary calls. The checks cover all
256 FILE flag combinations for EOF/status clearing and all six slots, plus
replacement opens, count/long destinations and full 32-bit tell/seek values.
They do not execute real filesystem operations or prove a real CRT backend.

```sh
./tools/dev --command make test-aspect-script-files
```

The [owned DOS backend](ASPECT_SCRIPT_FILE_BACKEND.md) runs these handlers
against real files in a linked diagnostic, including binary/text I/O, seeks,
EOF/error flags and six-slot repeated cleanup. Remaining work includes deeper
original CRT equivalence and borrowed-stream/fatal-warning policy. Both
compilers, the interpreter lifecycle, EOF destination, FGETS_CRLF setting and
terminal handoffs are now covered by the application integration. Keep filesystem
checks on owned test media. No whole-application gate closes.

The [recovery record](validation/aspect-script-files-native.json) binds source,
compiler fixtures, REA evidence identities, CPU replay and the fresh original-free
build. Earlier oracle attempts remain private: the first corpus declared `TEXT`,
an original reserved word, so all cases failed before reaching their command.
The corrected corpus uses `filedata`; the final corpus additionally includes EOF.
