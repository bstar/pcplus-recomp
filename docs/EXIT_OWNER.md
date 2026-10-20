# CLI exit ownership

The [attached-terminal follow-up](PARENT_EXIT.md) now verifies retained child
return, lease retirement, error display and continued serial operation.

The banked ASPECT CLI now checks callback ownership before returning to DOS.
Ordinary cleanup still closes its script, UART and renderer owners. The final
guard restores the startup PSP and retries safe break-owner recovery. If the
break owner is CLOSED and no process/display/handle/serial/checkpoint lease
remains, the CLI returns its original result through the CRT's normal exit.

If ownership remains unresolved, DOS4C must not free memory that an interrupt
vector can still reference. The guard validates the current PSP's MCB and keeps
its **entire current allocation** through DOS31, returning state error10. DOS's
return-mode byte distinguishes this from ordinary exit: the recovered EXEC
parent observes raw030A, or778 decimal. The guard neither invokes unknown
vectors nor overwrites their ownership. It does not automatically unload the
retained process later.

`program_exit_begin()` runs before callback acquisition. It requires foreground
DS=SS=DGROUP and IF1, checks the DOS PSP against the CRT's `_psp`, validates the
PSP signature/MCB type/owner/size, and captures a static memory floor using the
CRT's `_STACKTOP` value. DOSSEG places both code banks before DGROUP and the
stack at its static end. The final paragraph count comes from the current MCB,
not a guessed image size or a shrink request. If live ownership remains but
that block cannot be validated, execution reaches a holding loop rather than
falling through to DOS4C. This is a fail-stop policy, not kernel repair.

DOS31 also preserves other DOS-owned allocations and remaining handles; the
[DOSBox-X termination implementation](https://github.com/joncampbell123/dosbox-x/blob/master/src/dos/dos_execute.cpp)
separates this path from ordinary process memory/file release. The tests below
independently check the resulting memory and callbacks under the actual emulator.
Retention is a fatal cleanup fallback and can consume memory until the DOS
session is reset or a verified repair/unload procedure is provided.

```sh
./tools/build test-exit-owner
./tools/build test-aspect-exit-probe
./tools/build test-aspect-banked-cli
./tools/build test-exit-source
```

The [validation receipt](validation/exit-owner.json) binds12 exit cases crossed
with initial break0/1:

* N exits normally with no owner.
* R safely restores a READY owner and exits normally.
* Q retains after an unknown foreground INT1B vector quarantines the owner.
* D repairs a damaged native saved pool from the trusted snapshot and exits.
* P restores the startup PSP after a controlled foreign-PSP token and exits.
* L retains when the caller reports another outstanding lease.

These pass1162 parent assertions. The real recovered DOS EXEC parent validates
the retained main and extra allocation MCBs, allocates and fills the largest
free DOS block, verifies retained code/data bytes, and invokes the known test
handler afterward. Successful recovery returns37 with ordinary exit mode;
retention returns030A. Each case runs in a separate DOSBox instance. The parent
restores its captured vectors/break state before ending the test session.

A separate actual ASPECT CLI probe passes277 assertions. A controlled timer
changes INT1B during real RUN/WAIT, restores its own timer vector, and supplies
one BIOS key. Real cleanup detects the unknown foreground owner; the exit guard
retains the CLI and its allocation. The independent parent then proves the
callback and its data still work after memory pressure. This uses the real VM,
controller, exit guard and caller lease report; the timer mutation is a declared
test stimulus.

The linked instruction model rejects10 invalid admissions and checks four exit
decisions, including a changed PSP and invalid-MCB holding entry. DOS services
and the outstanding-lease callback are modeled boundaries in those cases;
they do not prove recovery from corruption in a running DOS kernel.

The normal banked CLI also passes13 attached-terminal workflows,505 checks,
including successful WAIT/NOCLEAR, failures, compiler fallback, repeated child
execution, shared file/environment/enumeration state and all COM/flow routes.
With the exit guard enabled, all93 full-VM fault/control routes still pass3451
checks. A fresh tree with only declared sources reproduces29 DOS products,
including the normal CLI, both probes, attached terminal, compiler and process
components, without originals, prior objects or REA databases.

The standalone and both attached quarantine paths are covered, including the
[mouse-enabled parent follow-up](PARENT_EXIT.md). Same-session retry still needs acceptance. Normal dispatch
publication, application-wide parent lifetime, the remaining native services
and physical RS232/WiFi-modem/keyboard acceptance remain open. No F01–F16 gate
closes from this checkpoint.
