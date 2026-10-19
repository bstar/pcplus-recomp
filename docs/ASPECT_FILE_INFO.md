# ASPECT filesystem queries and rename

The maintained DOS compiler, host compiler and production `ASPECT.EXE` now
support `ISFILE`, `GETFSIZE` and `RENAME`. The dispatcher implements 92 of 215
slots; 123 remain explicitly unsupported. This advances F13 without closing
any whole-application gate.

```text
integer missing
long bytes
proc main
isfile "DOWNLOAD.ZIP"
missing = failure
getfsize "DOWNLOAD.ZIP" bytes
if success
rename "DOWNLOAD.ZIP" "ARCHIVE.ZIP"
endif
endproc
```

`ISFILE` attempts a binary read-only open and closes a successful open. It sets
comparison to 0 for openable files and 1 otherwise; it is not an attributes-only
existence check. `GETFSIZE` opens in binary mode, seeks to the end, writes the
long destination and closes the file. Failed open sets comparison to 1 and
consumes the destination operand without changing its value. Success starts
comparison at 0; the original handler does not convert failed seek/tell/close
results into a different comparison. The recovered component explicitly tests
that policy; broader CRT equivalence remains unproved.

`RENAME old new` uses DOS interrupt 21h/AH56h. Comparison is 0 on success or the
raw DOS error word. The DOS regression checks error 2 for missing source and 5
for an existing destination, preserving both existing files. The native helper
uses its initialized DS snapshot for the destination's ES segment.

All operands are atomic. Paths accept string constants/variables/parameters;
`GETFSIZE` requires a long destination. A single optional comma may separate
arguments. Leading/trailing/doubled commas, parentheses, expressions and wrong
types reject. The original compiler's 84 authored cases establish 17 exact
accepted ASX results and 67 rejections, including locals and parameters. The
full DOS compiler passes 1,564 cases: 882 accepted outputs match the maintained
host and 682 are rejected.

The new module contains 177 exact native instruction bytes across three commands
and two helpers. REA/Ghidra evidence comes from the original resident/overlay18
analysis carrier, which is never executed. Ordinary builds consume authored
assembly and numerical locations/hashes; they never read the original binary.
The component executes 322 source-only cases and a separate 322-case actual
original-byte comparison with explicit operand/stdio/DOS boundaries.

The query stream has a separate temporary owner, so all six numbered script
streams can remain open. The final invocation cleanup closes that temporary if
long-destination decoding aborts after open. Close retires the owner before
calling stdio and is never retried after an ambiguous result. Per-file ASX
cleanup does not replace outer invocation ownership.

Actual 8086 DOS testing adds 155 invocations in one process and 1,103 assertions.
It verifies 70,001-byte binary files, retained destinations after failed open,
raw rename errors, unchanged existing file contents, parameter destinations,
six occupied script slots and malformed/truncated destination aborts after
fopen. Used near/far heap blocks and the inherited handle table remain identical
after warmup. INT0, FLAGS and the native ABI restore after each invocation.
An explicit ASP CLI child compiles and runs the same query commands.

A real terminal child queries a generated file, checks its size, renames it and
checks the new name before transmitting its login password. The passive parent
observer requires normal UART/keyboard/history/handle restoration and working
input afterward.

The optional ENiGMA `--file-info-login` regression writes a five-byte probe,
checks its size, renames it and checks the new name before authenticating. It
then passes all eighteen checks across the existing custom search/index/DIZ/NFO
route. The original341-run stream regression still passes4,727 assertions, and
a fresh original-free rebuild reproduces225 byte-identical outputs. This uses the isolated
patched copy of the owned board and synthetic data; the live decoder and actual
catalog remain unchanged. Physical RS-232 Wi-Fi modem validation remains open.

```sh
./tools/dev --command make test-aspect-file-info test-aspect-file-info-compiler
./tools/dev --command python3 standalone/test_aspect_file_info_dos.py --label unique-info-run
```

The first DOS fixture used an unsupported global initializer and stopped at
compilation; that fixture was corrected. The second run caught a real OMF
relocation defect: local file-mode strings lacked a DGROUP declaration and
caused failed opens. Declaring the data group corrected the linked application;
the flat native instruction bytes were unchanged. Those failed attempts remain
in ignored analysis/build evidence, separate from the successful third run.

See the [validation record](validation/aspect-file-info.json) for current binary,
compiler, VM, parent, ENiGMA, package and original-free rebuild identities.
The [stream-command checkpoint](ASPECT_SCRIPT_FILE_RUNTIME.md) retains its
separate historical evidence. Remaining language families, recorder, application
services and the full F01–F16 requirements are still required.
