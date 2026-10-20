# Terminal final-exit ownership

The [process-bank follow-up](TERMINAL_PROCESS_BANK.md) expands real PROGRAM and
setup coverage and corrects a false positive for DOS-restored vectors22h/23h/24h.
The guard audits their effective targets from PSP0A/0E/12; an unsafe saved
self-reference still retains. Its latest banked exit receipt includes six
explicit restored-vector model cases and the actual broader mouse workflows.

The opt-in `--exit-guard` terminal now checks its final DOS4C boundary. Startup
captures the real PSP and immutable static paragraph floor after validating
DS=SS=DGROUP, IF1, PSP signature and MCB ownership/extent. Final cleanup restores
that startup PSP, validates the current MCB again, and audits active execution
state and interrupt references into the complete current PSP block.

If execution is idle and no reference remains, the original terminal exit code
continues through DOS4C. Otherwise DOS31 retains the entire current validated
allocation and returns error15 (raw DOS4D status030F). An invalid context or MCB
at the final boundary enters an STI/HLT holding loop. The guard never invokes
an unknown callback, repairs a vector or guesses a smaller resident allocation.
Existing mouse-owner quarantine still uses its separate DOS31 error14 path;
this guard runs after successful mouse close.

The [validation receipt](validation/terminal-exit.json) binds sixteen actual DOS
cases across keyboard/mouse parents and initial extended-break0/1:

* Mode0: normal exit with a valid external INT60 handler owned by the test parent.
* Mode1: a controlled linked ISR remains registered in INT60; memory is retained.
* Mode2: a controlled outstanding-process flag requires retention.
* Mode3: a controlled foreign PSP token is restored before normal exit.

The independent DOS parent observes actual raw child status, checks the PSP/MCB
and linked callback address, allocates and overwrites the largest free DOS block,
and verifies retained code/data afterward. Mode1 invokes the known registered
ISR and sees its counter advance. The source-owned witness captures the current
PSP and full paragraph count before termination. All sixteen cases pass288
parent assertions; software-busy and foreign-PSP probes are declared state
injections, not actual abandoned processes or DOS-kernel corruption.

Both guarded terminal products also pass thirteen ordinary attached ASPECT
workflows apiece:26 routes and1166 checks, including WAIT/NOCLEAR, failures,
repeated DOS children, source compilation, shared files/environment/enumeration
and all COM/flow combinations. Two retained-child/same-session-retry controls
pass126 checks and still permit normal terminal exit. A fresh declared-source
tree reproduces ten guarded/probe terminals and four existing terminal products,
fourteen byte-identical products in total, without originals or object caches.

The linked instruction model checks ten rejected admissions, all256 vector
slots, six address boundaries/noncanonical spellings, five execution flags,
nine fail-stop conditions, two normal decisions and five CP/M gateway cases.
MCB corruption and holding-loop cases are modeled boundaries, not tests that
damage a live DOS kernel. DOS31 retains all allocations belonging to the process;
automatic repair or unloading is not implemented.

DOS's legacy CP/M entry point needs special handling. The five-byte far JMP at
physical0000:C0 overlaps table slots30h/31h. The DOS witnesses capture unchanged
bytes `EA C0 D1 00 F0`: the real target is F000:D1C0. Interpreting those bytes as
two interrupt pointers produced a false self-reference for a low-loaded parent.
The first guarded retry controls and `guard-retained-diagnostic-01` preserve that
failure. The diagnostic recorded reason1/vector30h after the retry itself had
already completed successfully.

The guard now saves the startup gateway bytes, always checks an EA gateway's
actual target, and treats an unchanged gateway as code. Changed bytes also get
the conservative ordinary vector scan. The model deliberately constructs a
gateway whose pseudo-vector falls inside the application; its real kernel
target must still permit exit. Changed vector30h/31h and a gateway targeting
owned memory must retain. This follows the gateway layout in the
[DOSBox-X DOS implementation](https://github.com/joncampbell123/dosbox-x/blob/master/src/dos/dos.cpp).

```sh
./tools/build test-terminal-exit
./tools/build test-terminal-exit-process
./tools/build test-terminal-exit-source
```

The non-mouse guarded terminal uses64848 data/stack bytes and65384 resident
code bytes. The mouse variant uses64880 data/stack bytes and65532 resident code
bytes, leaving four near-code bytes spare; further resident work needs code
bank placement. The final guard itself is in CONFIG_CODE.

This is a final-exit check, not complete application-wide ownership. Asynchronous
DOS Ctrl-Break/critical-error interception, callbacks stored in arbitrary foreign
driver tables or generated heap code, normal publication, physical hardware and
stock BBS acceptance remain open. No F01–F16 full application gate closes.
