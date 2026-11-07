# Experimental ASPECT EMULATE integration

The optional interpreter now executes native EMULATE through the parent-owned
profile transaction. Actual DOS tests switch VT220→ANSI twice in one retained
terminal session and verify profile-specific DA replies. **This candidate is
unaccepted:** the combined six-stream/nested-child capacity workflow fails eight
of30 checks. The installed release remains unchanged.

The [validation record](validation/aspect-emulate-rpc.json) records
`profile_execution_passed: true`, `capacity_accepted: false` and `passed: false`.
This keeps the normal command proof separate from deployment acceptance.

## Matched protocol and native binding

Parent `856a9c85` publishes renderer capability20. Both the parent allocation
validator and the child client require that version. Request20 carries a scalar
selector in BX through the existing bridge. The parent's ordinary child/PSP/DS
checks and PROGRAM ownership gate precede the operation; returned UART ownership
and the profile owner's modal/view/staging guards still apply.

The child profile is selected by `emulate_vm=True` in the experimental process
builder, requiring the ALARM/snapshot configuration. Opcode2F resolves to the
recovered15-byte EMULATE owner. It reads a byte and stores it in a local scratch
word, then its reset dependency delegates to the checked parent request. The
scratch word is not a renderer cache or a live parent setting. A typed parent
failure follows the existing native runtime-error/abort path.

The child checks attachment, client and serial lifetime, PROGRAM/window/confirm
ownership and active synchronous-request flags. A successful request commits
through the parent's existing keyboard staging and reset. Supported maintained
profiles remain4/6. The other31 original names are compiler-recognized; their
runtime implementations remain open. No modem redial or remote reset sequence is
introduced.

## Actual DOS observations

The normal workflow passes26 checks with the386 DOSBox CPU profile. A synthetic
serial peer responds to script markers by sending real DA queries and ACK
strings. It supplies no terminal replies. The observed wire contains this pair
twice, with each response produced by the actual parent parser:

```text
PROFILE4\r  ESC[?62;2c
PROFILE6\r  ESC[?1;2c
```

Both FIRST scripts finish, the six-stream and missing-file/recovery scripts run,
DATE/TIME traces are saved, ordinary keyboard input resumes, and UART/PIC/vector
state, PRM and fixture identities are preserved. Initial CPR1;16 precedes the
first switch, proving the initial banner rendered before the full reset. The
final terminal area contains ACK6 and blanks with the configured attribute:
reset removed the old banner and ACK4, and the later received ACK6 rendered.

The generic connection harness's old final-banner-preservation check is false
for this intended reset. The specialized result retains all other checks and
replaces that assertion with initial CPR ordering, both new DA pairs and an exact
post-reset view. The generic capture is retained; it is not represented as an
unqualified passing result.

An additional native component replay still passes768 cases and the exact15-byte
hash. A normal parent/interpreter rebuild with this feature disabled remains
byte-identical to `689bdce9` / `b4f0aecc`.

## Capacity remains unaccepted

| Product | Minimum including PSP |
| --- | ---: |
| Capability20 parent `856a9c85` | 479,760 bytes |
| EMULATE interpreter `051a1199` | 131,344 bytes |

The interpreter grows176 bytes from `b4f0aecc`; the parent grows32 bytes from the
previously funded parent component. This adds208 bytes to that accepted pair.
The combined held-stream workflow fails `four_calls`, `all_six_streams`,
`first_file`, `six_files`, `profile_reset_replaces_old_view`,
`actual_parent_clock_queries`, `three_nested_children` and
`exact_viewport_cells`. Peer/initial reply, file-identity, hangup and hardware
restoration checks still pass. These failures prevent release acceptance.

A trial disabling inlining in the request-client compilation did not lower the
131,344-byte minimum. That experiment is not selected by the builder. Continue
funding actual code while retaining streams, buffers, stacks and heap policy,
then rerun capacity before broader acceptance.

The remaining work includes negative version/MCB/lease cases, modal/WHEN and
native error cleanup, fatal-reset faults, receive-service timing, new source-only
cold reproduction, and current Enigma/Synchronet/package/physical gates. Normal
success does not prove those negative paths. Do not deploy this candidate. Full
F01–F16 parity remains open.
