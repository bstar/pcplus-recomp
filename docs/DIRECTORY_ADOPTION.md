# Apply a directory selection

[Selection/settings workflow coverage](DIRECTORY_ADOPTION_SETTINGS.md) now
includes native preview-A IRQ-only changes after a deferred PRMEDIT save,
and settings save/cancel after selection and a child directory change.

The later [IRQ/settings-path checkpoint](IRQ_HANDOFF_AND_SETTINGS_PATH.md)
fixes immediate old-IRQ PIC restoration and PRMEDIT's acceptance of the saved
absolute filename. Its receipt records the new application/editor identities
and the narrower regression scope; the evidence below retains its original
binary identity.

The opt-in `--directory-adopt` application adds **A: apply selection** to the
Alt-D preview. R checks resources and C compiles without applying them. A stages
the selected KEY/KBD/XLT/script resources, compiles an ASP when needed, and
commits the selected context, target, serial settings, modem commands, transfer
preferences, keyboard/actions and translation through the foreground PROGRAM
owner. It does not dial automatically. After returning, the maintained backtick
menu's Connection group can dial the selected target.

```sh
./tools/dev --command python3 standalone/package_special_edition.py --build \
  --custom-irq --directory-adopt --output build/adoption-package
```

Admission requires a disconnected, drained line and no competing foreground
owner. UART IRQ/IER/RTS and the original vector stay quiesced while staging and
validating. An asserted hardware carrier also refuses selection. Old pending
call accounting and pending settings offers refuse; accounting must retire
before its exact expected-old context can be replaced. The accepted PRM,
proposal and actual session are checked by the existing resource owner before
adoption. Directory preview retains a canonical directory filename in this
variant, so later accounting and settings operations survive CWD changes.

The worker prepares bounded modem commands without transmitting them, checks
translation and settings-context publication, releases any old-format software
pause and checks UART readiness. A port/IRQ transfer repeats the existing late
arrival checks as the final fallible hardware operation. No IO or foreground
scheduling intervenes between the final validation and publication. A broken
post-transfer invariant stops the application instead of resuming mixed state.
The existing PROGRAM restoration reinstalls the chosen serial format and ISR.
Profile changes use the existing staged profile reset after screen restoration;
the selected profile keyboard is installed with the new display defaults.

Translation bytes and their Reload/Edit canonical identity publish together.
Original CLI resource provenance remains distinct from directory-derived option
bits. Missing directory bindings reset defaults instead of retaining the prior
board's actions. The chosen directory context and source-rate/clipboard baseline
also move together; negotiated speed remains a separate active value.

An 80-byte initialized block in HOOK_CODE retains the accepted script's
canonical ASX name and fingerprint beyond the preview lease and child memory
loan. Automatic launch uses that full name. Immediately before ASPECT prepare,
a selected script is reserved, reread through the checked non-inheritable
reader, compared and closed. Changed files refuse execution. An uncertain close
or claim release retains ownership and blocks subsequent EXEC. External writers
and namespace replacement are not locked; CRC32 is damage detection, not
authentication. Header checking is not complete bytecode validation. The
prelaunch read is synchronous under the existing serial handoff; sustained
incoming traffic during a large script check still needs acceptance testing.

The compiler transaction remains in its separate persistent 256-byte far owner.
The adoption modem plan uses frozen offsets 8724..9810, outside accepted proposal,
bundle and session snapshots. Both 63,000-byte history allocations and the
8,192-byte stack remain. Native timer samples observe stack use but do not prove
a complete worst-case high-water mark. Exhaustive application stack acceptance,
additional port/IRQ combinations and failure-race coverage remain open.

The [receipt](validation/directory-adoption.json) binds exact application state
before the return prompt and after restoration, source-only package reproduction,
linked ownership/adapter checks and software connection evidence. The DOS
connection tests apply a board, execute an actual PROGRAM CD or COPY, dial a
loopback TCP peer through DOSBox modem emulation, and verify automatic scripts.
They cover canonical ASX, ASP compilation and rejection of an ASX replaced after
adoption. A valid decoy in the changed CWD must never execute. This carrier model
is deliberately separate from transparent null-modem TCP, which asserts carrier
as soon as TCP connects. Neither model proves analog or physical modem behavior.

The final checkpoint passes eight Apply workflows plus the profile 4 switch,
42 existing read-only/compile workflows, three dial/script workflows, 20 linked
adoption guard cases, 15 CLI inputs, 35 retirement inputs and five native retirement
workflows. Nested packaged compilation/history passes. Seven older executables
remain exact. The isolated rebuild from 778 source files reproduces all ten package files;
the 18-source translation rebuild repeats 13 DOS workflows with 823 assertions.
The ENiGMA check uses 250 ms sequence framing and 20 ms input-byte pacing. The public
receipt records earlier failed fixtures and the explicit limits of each check.

Full F01–F16 application acceptance, an independent complete BBS character/
attribute rendering comparison, physical Boca/SPA2102 reconnect/transfers and
card installation/acceptance remain open. Loopback ENiGMA checks exercise an
owned fixture and proxy; the live BBS, bridge, ATA, network and card are untouched.
