# EMULATE keyboard I/O and queued receive

The unchanged optional parent `856a9c85` and interpreter `5c641ac4` pass three
additional actual DOS workflows, 34 checks each. The
[validation record](validation/aspect-emulate-io.json) binds source, products,
generated observer/scripts, raw wire, exit state and screen captures. No build
is selected or deployed; installed R59A85A8 remains unchanged.

## Failure recovery

| Case | CPU | Mutation after valid startup | First native exit |
| --- | --- | --- | --- |
| Missing keyboard | 386 | Delete the explicitly imported KBD | error 5, opcode 2F |
| Truncated keyboard | 8086 | Replace that KBD with three bytes | error 5, opcode 2F |

Both scripts stop before the statement following EMULATE. A delayed peer DA
query receives the prior ANSI identity after the failure. A later script restores
the exact keyboard fixture and opens all six streams; the next recovers a missing
file, and the final script performs strict KBD-backed VT220/ANSI switches with
actual profile DA replies. The final reset screen is exact, keyboard/hangup work,
all four exits have DS=SS and the checked cleanup/native owners are zero.

This verifies native command failure through the actual imported parent service,
not a substituted error result. The query verifies retained profile identity;
it does not compare every pre-failure screen cell. Unknown close outcomes and
asynchronous fatal reset remain separate cases.

## Queued input during repeated imports

The DOS386 workflow performs 128 alternating profile switches using an explicit
seven-profile KBD. The peer supplies 1,536 ASCII bytes as 512 `PKT` markers in
32 paced chunks. Native WHEN TRANSMIT acknowledges every marker exactly once.
After the loop, the peer waits for RXWAIT before sending the WAITFOR terminator;
normal idle receive can legitimately consume an earlier terminator.

The passive observer records 650 parent keyboard-I/O entries, including 130
reads: 128 switches plus the two later recovery/profile checks. Queued child RX
is present at 185 of those I/O entries, with a sampled maximum of three bytes.
Sampled dropped-byte and serial-status maxima are zero. All 512 acknowledgments,
subsequent scripts, final screen and hardware restoration checks pass.

The observer extends the existing exit witness with read-only entry samples.
It reads no UART registers, calls no DOS services inside its hook and writes no
application state. The 386 observer resides in UMB; the 8086 case uses conventional
memory. These diagnostic runs change memory/timing footprint and are not new
unobserved-capacity proofs.

The host observes about 1.08 seconds from RXREADY to RXWAIT and 1.39 seconds to
RXDONE in this run. These intervals include VM, file, reset, receive, pattern,
TX and host scheduling costs, including concurrent fixture load. They do not
bound an individual import/reset, worst-case IRQ latency or a physical 16 MHz
386SX. This finite paced stream does not establish full-ring pressure, sustained
line-rate headroom, hardware RTS/CTS or SIP/audio acceptance.

## Reproduction

Use a fresh output name and the pinned environment:

```sh
./tools/dev --command python standalone/test_aspect_emulate_io_dos.py \
  --terminal build/emulate-rpc-parent-20261107/TERMINAL.EXE \
  --runner build/emulate-rpc-child-checked-20261107/ASPECT.EXE \
  --output build/my-emulate-io-check --case receive
```

Use `--case missing` or `--case short --cpu 8086` for the two failure cases.
The authored KBD has normal/keypad Enter bindings and otherwise empty slots;
it contains no installed private configuration. The mutable recovery backup is
staged separately from immutable fixtures and its final state is checked.

The fixture history retains the initial backup-immutability, omitted normal
Enter and premature terminator mistakes. Those tests are not accepted receipts;
application bytes were unchanged throughout.

## Remaining

Expand native abort/fatal-reset composition and sustained receive/flow stress
beyond this finite overlap case. Reproduce a matched capability 20 package from
public sources before selection, then repeat physical Boca/SPA2102/SynthModem
acceptance. The wider original-feature inventory remains open.
