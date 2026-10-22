# BBS recorder replay: current failure boundary

Actual DOS tests against the existing loopback Synchronet and ENiGMA fixtures
successfully create recordings through File/C and compile them with DOS ASPCOMP.
**Fresh-session replay is not accepted.** The retained attempts are bound by the
[diagnostic record](validation/bbs-recording-failure.json).

Credentials precede recording and are absent from the recorded transmit payload.
Synchronet records Main → Files → Main (`5451`); ENiGMA records Main → Messages
→ Main (`4D0D510D`). Both recording sessions exit normally and restore their
sampled UART/DOS state. Replay uses File/A and the source-built ASPECT runner.

The first attempts (`recorder-current-01`) stopped at an incorrect audit boundary:
the Hayes model forwards configured shutdown `+++`/`ATH` bytes to its TCP peer,
while the audit expected navigation to be the final bytes. The model does not
implement escape-to-command mode. This limitation is explicit in subsequent
checks; production modem commands are unchanged.

The next attempts (`recorder-current-02`, terminal `d7d8b18e`) exposed an actual
stream mismatch. Recording included raw ANSI continuations before input
translation, creating a prompt such as `CPlus Lab: ESC[37m`. Native ASPECT
WAITFOR receives translated lead bytes, while its renderer consumes `[37m`
outside the matcher. Those generated prompts could not match.

The corrected tap observes the normal lead after input translation. Continuations
stay outside recording; an unread parser lookahead enters recording only if
subsequently delivered as a normal lead. Obsolete four-byte deduplication state
is removed. Linker alignment leaves keyboard/mouse near-data spare at 112/64
bytes and resident-code spare at 366/216. ASPECT's native behavior is unchanged.
Ten linked RX campaigns pass, and 623 damaged layouts/bindings/order mutations
reject, including an explicit translation-before-recording check.

The corrected build is
`f041eeaaaeff9e38d8169625f499cd1f26ead00695e343d3e8fe36a4d61987c6`.
Attempts `recorder-current-03` show partial improvement: Synchronet emits both
recorded commands and later keyboard input, but the final recorded prompt names
a different message area from the new session. ENiGMA still emits only its first
recorded command pair before subsequent keyboard input. Both replay attempts
time out without normal DOS exit, so neither proves parent return or cleanup.
ASPECT forwards ordinary keyboard input while waiting; those bytes alone do not
prove the script completed. Failed and successful subchecks remain distinct.

The next diagnostic must capture the actual translated WAITFOR stream and wait
outcomes, distinguish changing prompt content from renderer/matcher behavior,
and exercise both same-session and fresh-session replay. Do not weaken the
navigation, normal-exit or restoration checks, or edit generated scripts and
present that as a recorder pass.

Reproduce with fresh labels, one session per synthetic account at a time:

```sh
./tools/dev --command python3 lab/bbs/recording_dos.py synchronet --label NEW
./tools/dev --command python3 lab/bbs/recording_dos.py enigma --label NEW
```

The fixtures use loopback ports 23231/23233 and synthetic lab accounts. Tests
use COM2, 19200, 8N1, HARD under DOSBox-X. Software audio, physical Boca/SPA2102,
real escape/hangup behavior, transfers and every full F01–F16 gate remain open.
