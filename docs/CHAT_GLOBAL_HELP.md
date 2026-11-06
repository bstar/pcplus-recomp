# Chat Alt-Z Help checkpoint

The opt-in `--chat-help` profile opens the source PCHELP context3 from Chat
with Alt-Z. Escape returns to Chat, preserving the unfinished line and its
screen/cursor. Enter then sends that line once. The ordinary command reference
continues to use context41. This is an experimental local checkpoint; it is
not a selected physical release.

```sh
./tools/dev --command python standalone/build_global_help_profile.py --output build/my-chat-help --chat-help
./tools/dev --command python standalone/test_chat_help_main.py --package build/my-chat-help --output build/my-chat-help-test --rows 50
./tools/dev --command python standalone/prove_global_help_source.py --package build/my-chat-help --output build/my-chat-help-source
```

Use fresh output directories. The companion PCCHAT.OVL retains API0106 and
its exact preceding bytes; PCHELP.RTE and the authored47-topic HLP are also
unchanged. The ordinary global Help build without `--chat-help` still produces
the exact471d5856 parent. See [the receipt](validation/chat-global-help.json)
for complete hashes and bounded acceptance.

## Original behavior and ownership

The [saved REA context trace](GLOBAL_HELP.md#next-original-context-chat)
establishes that original Chat writes context3, and the keyboard poll consumes
Alt-Z before ordinary Chat input. Alt-F6 remains Redisplay.

The source frontend intercepts Alt-Z after its existing busy, key-hold and
Redisplay continuations. It queues context3 without calling Chat stop/unload
or beginning a new session. The PROGRAM owner already preserves a distinct
full-height screen buffer, drains TX, sends software XOFF when enabled, masks
the UART/releases its interrupt vector for DOS EXEC, and restores the hardware,
mouse, display and cursor afterward. Pending PROGRAM work holds RX in the
real UART ring. The normal foreground code cannot run concurrently with the
synchronous DOS child.

The storage guard remains in place for ordinary PROGRAM requests. Their
entry clears CX; a separate private entry receives the Help context and admits
the active Chat storage owner only when CX is3. The near value is preserved
across the recording-owner query. Other existing recording, display, port,
controller, connection and pending-program checks remain active. No new near
state, loaded-module state or snapshot arena is allocated for this admission.

## Memory correction and tests

The initial479504-byte parent successfully opened Chat Help but failed the
six-stream ASPECT/nested-child regression. It is rejected. Maximum compiler
optimization made the shared path scanner larger, so that candidate is also
rejected. Measured size-only compilation (`-os`) of the scanner in both code
banks, plus removal of duplicate admission checks already guaranteed by the
existing frontend, produces a479392-byte parent. Stacks, stream counts and
buffers are retained: DS=SS65504, stack8192, resident CS65452.

The size-only scanner matches the unchanged independent implementation in2688
real-DOS paired cases and passes all30 preceding bounds/alias checks. The
current parent passes the six-stream ASPECT case with three nested DOS children.
A source-only cold export rebuilds all four products exactly, repeats normal
reference Help and its XOFF/XON case, then runs actual normal-main Chat Help
at25 and50 rows. A passive timer observer captures complete Chat/Help/Chat
frames and BDA cursor states. It admits the first Chat frame only after `AB`
is visible, confirms the context3 heading, and checks identical return frame
and cursor. The preserved line transmits once; after leaving Chat, ordinary
keys and a fresh parser reply work. Hardware snapshots and PRM remain unchanged.

The [recovery follow-up](CHAT_HELP_RECOVERY.md) closes repeated Help, resource
failures and raw receive/software-flow return at all four supported heights,
and reruns Enigma/Synchronet for this exact parent. It also repeats the prior
busy/cancellation pressure regression. The tests still do not independently
witness loaded-module memory identity or every lifetime edge. Help queued
during busy parser/TEXT/full deferred input, geometry faults, physical
Boca/SPA2102/SynthModem acceptance, other contexts and full original feature
parity remain open. The subsequent [native-wait checkpoint](CHAT_HELP_BUSY.md)
adds exact-capacity FIFO Help and sampled loaded-image identity; it does not
close every wait state or module lifetime/geometry fault.
The [connected Enigma editor test](CHAT_HELP_BBS.md) additionally covers real
authenticated idle-editor return, resumed editing and independent final cells.
