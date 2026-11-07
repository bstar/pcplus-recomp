# ASPECT DATE and TIME

Both source compilers and the interpreter now implement the original `DATE`
and `TIME` commands. These query the DOS clock; they do not set it. DATE takes
a writable string destination. TIME takes a writable string destination and an
atomic integer format operand:0 means12-hour with AM/PM,1 means24-hour.

```text
string today,now
proc main
date today
time now 1
message today
message now
endproc
```

Globals, locals, parameters and string registers are supported. One comma may
separate TIME operands. Literal/readonly/wrong-type destinations and expression
operands reject. The original compiler accepts constants2 and-1, but the native
runtime bounds check rejects them with operand error7 before formatting.
Neither command changes the comparison result used by `success`/`failure`.

## Original evidence and fidelity

REA's original overlay18 entries E689 and E909 provide17 and33 exact bytes;
resident498B provides121. The source builds all171 bytes exactly. Existing
recovered resident date formatter36D4, DOS date helper776E and DOS time helper778C
supply another103 exact bytes. Flat original SET/FETCH units remain unchanged;
the compact runtime lookup below is a separate maintained memory adaptation.

The DATE formatter preserves year-minus1900. Thus a2026 date ends in`126`,
rather than`26`. It writes into an owned16-byte scratch area and copies into
the script destination. This command does not use or alter directory accounting
records; the separate successful-call accounting correction is unchanged.

TIME0 returns values such as`12:00:00AM`, `12:00:00PM` and`11:59:59PM`.
TIME1 returns`00:00:00` through`23:59:59`. The original24-hour format string
has a trailing percent sign; actual original CRT execution discards it.
The private compact formatter now accepts the three additional recovered formats
and preserves that behavior without consuming a nonexistent extra argument.
No general user-supplied printf language is enabled.

Selected REA records are retained privately in
`analysis/aspect-clock-native-20261106.rea.json`. Handler instruction Evidence:
`ev_1953d0587af4256af4eff5baa2618ad997ce4ecf22e61d2b329d0ede3fe1839c`,
`ev_f71d94e20c5f1a3d9388b68566435e38528a9e094fb85b73718dec2f5bb43576`;
formatter Evidence:
`ev_ef34e543749a3645f18d60c2386b639c3815e7c6236e511f0605640176662f1a`.
The identified synthetic overlay was analyzed only, never executed. Normal
builds consume maintained source and numeric provenance, not that image,
original executables, vendor resources or REA databases.

## Memory funding

The initial larger interpreter failed the real parent/six-stream/nested-child
capacity test. The accepted runtime uses a shared bounded SET/FETCH resolver:
87 one-byte indices select14 near handlers, including the unsupported handler.
The table occupies115 bytes instead of512. Selectors above56h go directly to
the same maintained unsupported error; all other unsupported selectors still
select that error. Both commands tail-dispatch through the same resolver.
Its instructions live in CODE, while its index/pointer tables remain in DGROUP.

This production adaptation is selected by`ASPECT_COMPACT_SET`; original flat
SET/FETCH builds retain their exact indexed-call instructions and full controls.
No stack, heap-growth policy, stream count, serial buffer or retained screen
capacity is reduced. The matched interpreter's code/data allocation grows only
16 bytes from the preceding cbdee194 interpreter. The unchanged fab5ac9e parent
again passes six streams, missing-file recovery and three real nested children.
Its FIRST script now also queries local DATE/TIME strings before the child and
saves all three values afterward; all26 parent checks pass. A fresh full-table
source control still returns an invalid-runtime-state error during the
six-stream child case, while its clock trace itself passes.

## Verification

```sh
./tools/build test-aspect-clock
# Explicit optional original-byte replay, outside ordinary builds:
./tools/build test-aspect-clock-compat
```

The optional compiler oracle compiles161 authored sources with the original
compiler:27 exact accepted outputs and134 rejections. The full actual8086 DOS
compiler suite passes2186 cases, including those sources. Native CPU replay
passes477 date/time scenarios; optional replay compares each with the actual
original resident CRT, including midnight, noon, seconds and year conventions.
The source-side formatter/operand boundaries in that component are modeled;
actual DOS/VM evidence is separate.

The DOS clock suite performs372 interpreter runs over31 same-process rounds,
passing7275 assertions. Independent DOS clock readings bracket output times;
the test never sets the clock. It covers writable destinations, comparison,
six held files, EXECUTE, range failures, truncated/bad operands and repeated
heap/JFT/INT0/FLAGS/ABI restoration. A stale component build was initially
linked into this diagnostic; manifest source checks now reject stale inputs.
The initial missing DGROUP declaration for local time constants was corrected
before the accepted rebuild; all failed captures remain in ignored build storage.

The base runtime regression passes1123 cases/26986 checks with107 supported
slots and108 explicit unsupported opcode slots, plus the complete remaining
SET/FETCH selector checks. Native SET and FETCH component tests still pass.
The external-process interpreter additionally enables DOS/RUN/SHELL; the base
107-slot diagnostic intentionally keeps those three process commands disabled.
The prior compact formatter regression passes3907 cases. A5339-file public
source export rebuilds ordinary ASPECT, matched parent ASPECT and ASPCOMP exactly,
then repeats all372 DOS clock cases without originals/private files/prior objects.

The new matched interpreter/compiler also pass Synchronet's editor/external
viewer and Enigma's carrier-loss/redial/two-login/exact65539-byte retry workflow.
The latter's independent audit checks raw proxy/protocol evidence and finish.
Its first run reached the DOS success marker but could not be accepted because
the old harness required the active server log inode to remain unchanged.
Enigma had rotated that log. The harness now uses the existing checked numeric
rename-rotation collector; the auditor verifies captured segment hashes,
boundary identity and filtered session records. Thirteen journal/relay controls
pass. An unchanged real-capture copy passes, while four copies with changed
segment bytes, missing device identity, mismatched boundary or a dropped
session row reject. The complete BBS test was repeated. The accepted rerun
captured one journal segment, so actual rotation coverage comes from the
separate temporary-file controls, not a claim that the rerun itself rotated.

This checkpoint does not replace the installed Chat/Help release or establish
physical modem acceptance. Current BBS regressions and exact product identities
are recorded with [the acceptance receipt](validation/aspect-clock.json).
Remaining ASPECT families include terminal/modem actions such as DIAL and
EMULATE, interactive input and screen commands, floating-point services and
transfer commands. Their original labels alone do not establish recovered
semantics. The remaining ASPECT/emulation/protocol/Host and whole-application
gates stay open.
