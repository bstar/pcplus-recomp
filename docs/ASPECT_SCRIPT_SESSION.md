# Connected script sessions

A successful script launched during an established connection now returns
directly to the terminal. Offline scripts and failures retain the serviced
acknowledgement prompt. File → A → Run script lends the selected port to the
source-built sibling ASPECT.EXE and restores raw unread input afterward.

## Port selection and resume

The terminal keeps its current UART in native IRQ-table slot0, regardless of
which COM port is selected. Passing that slot as the child's COM identifier
incorrectly selected COM1 for a COM2 session. The launcher now uses the actual
one-based terminal port number. Linked prepare checks cover COM1 through4 while
keeping the native active slot zero. Invalid port numbers and incompatible
base/IRQ combinations fail before EXEC. The current child interface supports
standard COM bases and IRQs; custom IRQ inheritance remains future work.

The first live Synchronet script attempt sent no credentials. A passive INT1C
video observer subsequently captured `serial service error ... serial 3` before
any opcode executed, confirming the wrong-port admission failure. With port
selection corrected, the script authenticated, but the terminal exited
abnormally while welcome art arrived during the acknowledgement pause. Its
exact terminal errorlevel was not recorded. That attempt's captured child
success/prompt, authentication and failed DOS result remain retained.

An online script should resume its terminal processing as soon as it succeeds.
The connected-success path now restores the saved screen and drains received
bytes immediately. Errors still leave their diagnostic visible, and offline
console scripts still wait for a key. The bounded receive ring and flow-control
requirements remain; this change removes the additional application pause.

## Actual DOS login and editor

`lab/bbs/script_login_dos_probe.py` stages immutable source-built executables and
compiles an authored LOGON.ASP. The terminal first dials the owned loopback
Synchronet. Its menu then launches the script, which transmits the synthetic
LABUSER name, waits for `Password:` using native WAITFOR, and transmits the
synthetic password. Neither credential is in the BIOS keyboard schedule.

The independent audit checks each credential exactly once on decoded BBS wire,
the authenticated server display, unchanged binaries/configuration, sampled
IRQ/UART/PIC restoration and absence of a blocking child-return/error prompt.
The resumed terminal then passes all12 stock FSEditor checks and eight measured
key sequences, ending with draft abort. The script uses COM2/19200/8N1/HARD,
immediate modem forwarding and no artificial packet delay. This advances the
application workflow beyond the earlier script greeting smoke.

Additional current checks cover17 linked launch groups/65 inputs, seven actual
DOS Script workflows, the generic PROGRAM owner, command menu and configuration
far-call ABI. Ninety outputs reproduce byte-for-byte in a fresh Nix source-only
checkout. The parent retains DS/SS65408; the runner is unchanged from the
[input-policy checkpoint](ASPECT_INPUT_POLICY.md).

Run against the existing owned local lab, using a fresh label:

```sh
./tools/dev --command python3 lab/bbs/script_login_dos_probe.py --label my-script-session
./tools/dev --command python3 standalone/record_script_session.py --label my-script-session
```

The recorder requires all current prerequisite reports and a staged package.
It validates source/binary/report bindings and retains the failed attempts,
including the corrected Telnet-prefix checker and observer baseline-order
mistakes. The public ledger is `docs/validation/aspect-script-session.json`.
Earlier input-policy and editor records retain their original identities.

This establishes the selected Synchronet script-login/editor workflow, not
complete ASPECT, all modern BBS interaction, custom UART configurations or
physical Wi-Fi modem compatibility. All F01–F16 application gates remain open.
