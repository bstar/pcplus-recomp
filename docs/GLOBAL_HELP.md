# Terminal Help integration

The opt-in global Help profile composes the existing Chat/Redisplay terminal
with the source-built PCHELP companion and an authored47-topic PCPLUS.HLP.
Press Alt-Z for the command reference, then Alt-Z again for Terminal Help.
Escape returns to the same reference window; another Escape returns to the
terminal. F1 retains the selected command's short description.

Build with the pinned toolchain:

```sh
./tools/dev --command python standalone/build_global_help_profile.py --output build/my-help-profile
./tools/dev --command python standalone/test_global_help_main.py --package build/my-help-profile --output build/my-help-test
./tools/dev --command python standalone/prove_global_help_source.py --package build/my-help-profile --output build/my-help-source
```

Output directories must be new. Keep TERMINAL.EXE, PCCHAT.OVL, PCHELP.RTE and
PCPLUS.HLP together. ASPECT.EXE remains a separately versioned companion.
This checkpoint is a local candidate, with no physical deployment or package
selection change. The default Chat profile remains byte-identical when the
new flag is disabled.

## Ownership and native recovery

The command reference queues Help context41 through the ordinary foreground
PROGRAM owner. It drains replies, pauses reception, preserves display/mouse
state, executes PCHELP and restores the UART/IRQ/display lifecycle. The
reference snapshot and PROGRAM snapshot occupy distinct existing buffers.
Successful Help needs no extra acknowledgement; launch/resource/child failures
use the ordinary program-error acknowledgement. Repeated Help releases its
temporary callback pointers before returning.

The recovered132-byte descriptor producer and its50-byte strcpy and3-byte
getDS retain their exact flat comparison. OMF bindings substitute live state
and near callbacks in CONFIG_CODE. Both executable and resource paths resolve
from the launching program's DOS environment trailer, independent of CWD.
The bounded64-byte resolver runs before the native66-byte unbounded copy.
The queued52-byte command storage supplies keys/title/context, adding no
DGROUP allocation. The unresolved native UI word is explicitly zero; raw
mouse scales are passed through. Their full original semantics and helper
mouse interaction remain unverified.

The new HLP is source-owned prose in the observed47-topic order. Terminal
Help also includes the24 authored command-reference descriptions. It does
not redistribute the original help text or require vendor artifacts to build.
Only context41 is connected to a terminal key path in this checkpoint.

## Memory and verification

[The receipt](validation/global-help.json) records exact products and checks.
The accepted parent requires479408 bytes including PSP,16 bytes above the
preceding Chat profile. DS=SS remains65504 bytes with the8192-byte stack;
resident CS is65440 bytes. Existing stream counts and buffers are retained.
An earlier480096-byte candidate failed the six-stream ASPECT child test and
is not accepted. Sharing the resource scanner in the two code banks recovered
the needed space. Default builds still use the unchanged independent scanner.

The shared scanner matches that control in2688 paired real-DOS cases and
passes the preceding30 explicit bounds/alias checks. Cases include malformed
environments, duplicate keys, all byte values, randomized strings and64KiB
terminator boundaries. Synthetic metadata stays inside allocated test blocks;
the tests do not alter actual DOS heap MCBs.

Six normal-main DOS8086 sessions cover success, two Help calls, missing helper,
missing HLP, malformed HLP and software flow control. Passive observations
check the complete reference frame/cursor, actual helper/error display,
ordinary transmitted keys, fresh parser replies and restored hardware state.
The flow case verifies actual XOFF/XON and retained incoming text; its hidden
terminal cursor advances as the queued text is parsed. Companions are on C:
while the working directory is D:. PRM and staged files remain unchanged.

A clean5296-file public-source export reproduces all four products exactly
and repeats the normal/flow sessions without originals, private settings,
previous objects or analysis databases. The unchanged helper separately has
18 original/source DOS comparisons at25/50 rows with144 matching full-screen
frames and cursor states; see [the component report](HELP_PROGRAM.md).

These are bounded emulator and owned BBS-lab checks. Main Help integration
is currently tested at25 rows. The BBS regressions exercise the new parent,
not a Help invocation during a real BBS session. Physical Boca/SPA2102 audio,
all Help contexts, mouse navigation, complete input editing, alternate video
modes and full original feature parity remain open.
