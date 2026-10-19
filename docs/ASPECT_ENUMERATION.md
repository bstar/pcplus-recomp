# ASPECT file enumeration

The maintained compilers and production DOS interpreter now support FINDFIRST,
FINDNEXT, `$FILENAME`, `$FNAME`, `$FEXT`, `$FATTR`, `$FDATE`, `$FTIME` and `$FSIZE`.
That checkpoint implemented94 of215 opcode slots and rejected121. The later
[file attributes integration](ASPECT_FILE_ATTRIBUTES.md) extends this to96/119. The
whole ASPECT language, recorder and F01–F16 application gates remain open.

```text
long bytes
proc main
findfirst "DOWNLOAD\*.ZIP"
while found
message $FILENAME
bytes = $FSIZE
findnext
endwhile
endproc
```

FINDFIRST accepts an atomic pattern string and an optional atomic attribute
string. A single comma may separate those arguments. FINDNEXT takes no arguments.
The attribute letters are R, H, S, A, D and V, case-insensitive. Omitting the
attribute string uses mask 1; supplying an empty string uses mask 0. The original
compiler's 46 authored cases establish 17 exact accepted ASX results and 29
rejections, including local/parameter operands and read-only builtins. The full
DOS compiler regression passes 1,610 cases: 899 exact accepted outputs and 711
rejections. Ordinary builds read no original compiler or executable.

`FOUND` is the shared native result for text FIND and file searches. File
searches set it to 1 for a result and 0 otherwise; they do not replace the
comparison used by SUCCESS/FAILURE. A text FIND between file searches changes
FOUND but does not destroy the enumeration context. Another FINDFIRST replaces
the previous search. A failed search preserves the previous filename fields
and size; callers must check FOUND before using them.

`$FILENAME` is the full DOS basename; `$FNAME` and `$FEXT` split it at the native
first-dot boundary. Directory entries `.` and `..` retain their names and an
empty extension. `$FATTR` emits R/H/S/A/D/V in that order for set bits. `$FSIZE`
is the raw 32-bit DOS result. Date/time strings retain the original display-line
layout and formatting: a leading month space is skipped, DOS years are expressed
as years since 1900, and fixed field offsets can expose odd output for values
wider than the original layout. The explicit empty attribute mask selects the
original unformatted-name service, leaving old date/time fields unchanged.
These are recovered behaviors, not a redesigned metadata API.

REA/Ghidra evidence identifies 675 exact native instruction bytes: two command
handlers, the attribute parser/formatter, result normalization, DOS search
services and six string/one long getters. Computed formatter branches needed
focused instruction/byte inspection beyond Ghidra's function-body output.
The source-built component passes 885 cases and a separate matching original-byte
replay, including every attribute input byte, all masks, default/explicit flags,
files, directories, dot entries, volume labels, large sizes and getter pointers.
CRT formatting/string calls and DOS returns are explicit component boundaries.

The maintained runtime adds three explicit ownership/bounds policies:

- Save and restore the caller's DOS DTA around every search operation. FINDNEXT
  reselects the owned 43-byte search record each time. Before FINDFIRST it returns
  no result without adopting another caller's search. DOS searches do not own
  persistent file handles; the context survives EXECUTE and resets on a new
  outer interpreter invocation.
- Give the source pattern its own 81-byte buffer. The original 74-byte region
  adjoined the DTA, even though ASPECT strings can contain 80 bytes.
- Guard the original volume-label normalization when strchr returns null. The
  original then writes through DS:0000 with memmove; the exact component retains
  and characterizes that bug. The runtime skips that move for a label without
  a dot, preserving its name and empty extension. Its object differs from the
  flat native baseline by an explicit four-byte admission check.

Actual8086 DOS testing passes310 same-process VM invocations and22,377 assertions
through the full compiler/interpreter with real files,
including 70,001 bytes, hidden/read-only entries, directories, explicit empty
attributes, shared FIND state, retained failed-search fields, search replacement
and EXECUTE continuation. Invalid attributes and a truncated optional flag abort
with normal cleanup. Each invocation requires an unchanged foreign DTA pointer
and all 64 sentinel bytes, INT0/FLAGS/ABI restoration and no live file/heap owner.
Repeated runs also compare used near/far heap blocks and the DOS handle table.
A separate real kernel composition interleaves an unrelated CRT find_t search
between the native first/next calls and checks that its DTA and contents survive.
The actual linked runtime volume guard preserves the DS:0000 prefix.

A production terminal child gates its login password on a successful enumeration,
matching name/size and exhausted FINDNEXT, then returns to working parent input.
The optional ENiGMA `--enumeration-login` mode performs the DOS-compiled search
before authentication and writes the exact trace `FILECHK.BIN|FILECHK|BIN|5`.
It then requires all existing custom search/index/DIZ/NFO navigation checks.
This is an isolated patched copy of the owned board with generated files; live
decoder installation, the actual catalog and physical modem validation stay open.

```sh
./tools/dev --command make test-aspect-enumeration test-aspect-enumeration-compiler
./tools/dev --command python3 standalone/test_aspect_enumeration_dos.py --label unique-enum-run
```

The first attribute-oracle expectation incorrectly treated V as a directory mask
when parser mode 0 rejects both V and D; fixing that expectation changed no native
instructions. Two initial links exposed missing DOS prototypes and C symbol
aliases; no broken DOS product was executed. The first complete VM run passes;
a second adds the 80-byte pattern boundary. Historical failed build/probe attempts
remain in ignored analysis/build directories, separate from successful evidence.
The first clean rebuild matched232 of234 products: the workspace ASPINV/ASPEXP
diagnostics were stale after the builtin changes. Both were rebuilt and checked
(1,611 inventory and3,494 expression cases) before repeating the fresh comparison.

The [validation record](validation/aspect-enumeration.json) binds current binaries,
native/compiler/VM/parent/ENiGMA results, the refreshed DOS package and a fresh
original-free source rebuild of234 byte-identical outputs. Remaining ASPECT families, full application services,
other emulations/protocols/UI, Host and hardware requirements are still required.
