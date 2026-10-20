# Banked terminal DOS execution

The opt-in `--process-bank` build moves the maintained DOS EXEC backend into
PROCESS_CODE. Both public entry names keep their near, caller-cleaned
three-word ABI. A22-byte near entry copies path/tail/result words to an explicit
far entry; that entry copies them into the original near implementation frame.
DS=SS, preserved registers, caller-owned result storage and returned flags keep
their existing contract. The bank also contains the CS-relative saved DS/SS/SP
and EXEC result used when a child returns a changed context.

The635-byte bank contains the implementation, bounds helpers, far wrapper and
saved-context words. All its near calls/jumps stay inside that object segment;
its sole far crossing is the public near entry to the bank. Link validation
checks both aliases, wrapper argument offsets, target segments, MZ relocation,
retained extent and exact bridge instructions. The decoded object audit checks
every call/jump independently of the source text.

The keyboard parent now has746 near-code bytes spare, saving594 bytes against
its unbanked guarded counterpart. The mouse parent has596 spare, saving592
bytes from the previous four-byte margin. Alignment accounts for the two-byte
difference. Near data/stack remains64848/64880 bytes respectively. This creates
room for application trap hooks; it does not implement those hooks.

The [bank receipt](validation/terminal-process-bank.json) binds:

* All68 existing EXEC instruction-model inputs, including bounds/aliases, raw
  child status, DOS errors and changed DS/ES/SS/SP/registers before restoration.
* Actual8086 DOS EXEC, memory shrink/MCB, repeated calls, inherited environment,
  exact tails/FCBs, missing child, resize error8 and successful recovery.
* Five actual DOS COMSPEC/PATH/fallback routes through the C PROGRAM caller.
* Twenty-six attached ASPECT workflows with1166 checks across both parents and
  all COM/flow modes, plus two retained-child retries with126 checks.
* Four independent mouse workflows: PROGRAM, startup repair, live settings save
  and quarantine. They pass41 parent assertions; quarantine repair/reclaim is
  performed only by the controlled test observer.
* Sixteen banked terminal exit cases with288 parent assertions, bound in the
  [exit receipt](validation/terminal-process-bank-exit.json).
* Twenty-two byte-identical products rebuilt in a fresh declared-source tree:
  banked terminals/probes, generic banked backend and unbanked controls, with no
  originals, prior objects or REA databases.

Broader PROGRAM/setup testing exposed a pre-existing final-guard false positive.
Both unbanked and banked diagnostic parents returned030F with reason1/vector22h
despite successful child and driver cleanup. DOS sets a child's return vector
to its caller's execution address; at termination it restores22h/23h/24h from
the exiting PSP before returning to the parent, as shown in
[DOSBox-X termination/EXEC](https://github.com/joncampbell123/dosbox-x/blob/master/src/dos/dos_execute.cpp).
The guard now audits those effective PSP targets. It still retains if a saved
target points into memory being freed. Six explicit model cases distinguish
temporary self-vectors with outside saved targets from unsafe saved targets.
The failed `bank-mouse-lifetime-01` and `bank-guard-diagnostic-01/02` captures
remain in the local build tree. PROGRAM/setup now return normally; genuine
quarantine still retains its registered callback and returns the typed error.

```sh
./tools/build test-terminal-process-bank
./tools/build test-terminal-process-bank-ui
./tools/build test-terminal-process-bank-exit
./tools/build test-terminal-process-bank-source
```

Build outputs are `build/terminal-process-bank/TERMINAL.EXE` and
`build/terminal-process-bank-mouse/TERMINAL.EXE`. Normal publication, asynchronous
Ctrl-Break/critical-error ownership, remaining application services and physical
RS232/WiFi-modem/BBS acceptance remain open. No full F01–F16 gate closes.
