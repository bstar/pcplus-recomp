# Stock ENiGMA through SynthModem's actual proxy

The subsequent [workstation VM helper update](WORKSTATION_VM_HELPER.md) adds
the separately validated partial-I/O correction to the installed VM. References
to an unchanged VM below describe this earlier JavaScript checkpoint.

The 2026-10-25 follow-up reproduces and corrects the fragmented-key failure
without changing the stock lab BBS. These are actual DOS8086 COM3/IRQ5 sessions
using the branded terminal at 19200 8N1, the real SynthModem proxy and its real
Telnet codec. A synthetic Hayes/nullmodem transports serial data; SIP, modem
DSPs, analog audio and physical CTS timing are outside this experiment.

## Control and correction

The control uses immediate forwarding and explicitly delivers serial input
to the proxy one byte at a time with 2ms spacing. It authenticates and enters
stock ENiGMA's editor, but fails the independent semantic audit. Home placement
and Insert/overtype fail; ANSI fragments such as `[3~` become literal text.
The synthetic control also accidentally saves a post: the recorded
`no_post_saved=false` must not be described as a successful unsaved-editor run.
Only the isolated fixture's synthetic data was affected.

With the existing optional sequence framer enabled at 250ms, the same branded
terminal authenticates, enters the same stock editor, passes every semantic
check and saves no post. Actual DOS video contains UNSAVED and OVR 01,08.
A second run through the combined output-pressure candidate also passes these
requirements, with product and proxy source identities unchanged during the run.
Neither run uses the lab's corrected ENiGMA input decoder.

The framer preserves bytes and forwards plain text immediately. A lone ESC or
incomplete ESC sequence can wait up to 250ms. Sending a complete sequence in one
TCP write addresses the observed local case; TCP does not guarantee those write
boundaries to every remote server. A stream-aware server input decoder remains
the robust general fix. Binary transfers through this physical configuration
are still an acceptance gate.

## Large-output correction

The running upstream backend also rejected a single data block larger than
4093 bytes, ignored write pressure and let CallSession swallow the exception.
The staged source reproduces all three defects. The maintained ControlWriter
splits output into valid frames, retains bounded ordered data and propagates
readiness/drain through the actual backend, session and proxy. Write failures
now end the active call instead of silently continuing with missing bytes.

The combined source passes the existing pressure checks, including 16 MiB of
exact data across real loopback sockets with an initially paused reader. It
also passes the 1,220-assertion Telnet suite, key-framer checks and shortcut test.
The VM-side C helper and DSP image were not changed. Their separate partial-I/O
and analog integrity limitations are not closed by the Node writer test.

## Workstation state

The checked combined JavaScript files are installed in the workstation's
SynthModem checkout. Its private runtime settings enable 250ms sequence framing.
PHONE1 was checked on-hook/idle before the update; rollback files were retained,
only SynthModem restarted, and its VM/registrar/SIP service reported ready.
The V.32bis profile, LOC/1 aliases, adapter, network and live BBS were preserved.
The ordinary DOS application binary remains unchanged.

The [receipt](validation/stock-enigma-proxy.json) binds the control, both passing
sessions, exact video snapshots, component tests and installed file hashes.
The earlier [replacement checkpoint](ENIGMA_REPLACEMENT.md) remains historical
evidence for the initial codec-only deployment and corrected-decoder session.

## Repeat the combined editor check

Use the pinned Nix tools and an already running owned stock ENiGMA fixture:

```sh
./tools/bbs-dev --command python3 lab/bbs/enigma.py status
./tools/dev --command python3 lab/bbs/test_synthmodem_proxy_dos.py \
  --runtime /home/bstar/projects/synthmodem \
  --terminal build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply-lookup-guarded-traps-custom-irq-special/TERMINAL.EXE \
  --label UNIQUE_STOCK_PROXY --framing-ms 250
```

The runner requires a new result label, checks current source-built product
identities, starts its own loopback-only proxy adapter, runs the unchanged DOS
keyboard recipe with a LOC menu selection, audits actual authentication/editor
events and video, then stops its owned adapter. The raw-upstream option in the
DOS harness gives Telnet ownership to SynthModem; the test modem does not also
negotiate or escape those bytes. The existing stock BBS is left running.

Next acceptance work remains physical Boca/SPA2102 login/editor operation,
longer byte-integrity/flow tests, reconnect and transfers, multiline rendering,
the VM helper's partial-I/O behavior and full application/menu parity. The DOS
card is currently absent and has not been updated.
