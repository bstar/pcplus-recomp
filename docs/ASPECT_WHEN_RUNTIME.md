# WHEN in the DOS runtime

The maintained DOS runner now executes native WHEN/CWHEN registration,
receive matching, TRANSMIT actions and deferred CALL actions. SET WHENCASE
controls matching independently of WAITFOR case selection. This integrates
the [602-byte native component](ASPECT_WHEN.md) with the existing dispatcher,
FILE owner, value stack and local frames. It is still a partial ASPECT runtime;
complete application keyboard/UI, Host and other command families remain open.
The [validation record](validation/aspect-when-runtime.json) binds this checkpoint
to the source-built parent and runner, including successes and retained failures.

The host compiler emits these forms from source. Registration requires an
active serial backend; an unavailable backend reports unsupported before
registration. Ordinary slots are0–2; DISCONNECT uses its separate encoding.
Numeric slots outside0–2 compile but fail the native bounded runtime reader.

```text
proc main
    when 0 "READY" call worker
    waitfor "END" 10
    transmit "MAIN CONTINUES^M"
endproc
proc worker
    integer local_value
    local_value = 37
    transmit "EVENT^M"
endproc
```

A match seeks the actual script FILE and stages its return/frame state. It
does not synchronously run a second interpreter inside the receive callback.
An active WAITFOR completes before the handler body runs. Multiple staged
calls retain native LIFO order. Native pattern truncation, first-character
fallback, ASCII case folding and repeated rearming are preserved; these are
not replaced by a regular-expression engine or a one-shot event queue.

## Ownership and service timing

The runtime shares native state rather than copying counters:

| Native word | Shared owners |
| --- | --- |
| E2F8 | WHEN active count, receive monitor enable and dispatcher rewind enable |
| E382 | Flow gate, dispatcher wait suppression and COMGETC echo suppression |
| 8E20 | Actual UART receive count and dispatcher queued-input test |
| E398 | WHENCASE, separate from WAITFOR's E396 |

The exact service routine runs at dispatcher and native4E34 cancellation
points. WAITFOR and RGET therefore service disconnect actions while waiting.
Low-level transmit, raw receive, pause and renderer callbacks retain transport
polling and Escape cancellation without recursively running WHEN services.
The child defers service while on a parent renderer callback stack, then checks
at the next safe native service point. Native pattern matching runs on each
translated lead before rendering; parser continuation bytes stay raw and do
not enter WHEN or WAITFOR a second time.

The carrier backend reads the actual UART MSR DCD bit. Reading MSR also clears
its delta bits; the checker models that hardware side effect explicitly.
Closed ports are not read. Diagnostic carrier levels and scheduled drops are
declared fixture inputs, not evidence of a physical modem connection.
See [native timing evidence](ASPECT_WHEN_SERVICE_TIMING.md) for wait/TX timing,
queued-input rewind and the independently executed original-program traces.

Startup resets active count, disconnect arm and the three match cursors, and
selects insensitive matching. It does not invent a full-record zeroing rule.
Cleanup disarms before FILE/global release, restores gate/deferred state and
leaves unread UART bytes for ASIO handback. Error, stack exhaustion and budget
tests check cleanup before the next script starts.

The maintained child still uses immediate Escape cancellation. Native abort
confirmation and full local keyboard/UI dispatch are not reconstructed in
this owner; unsupported local UI keys report an error. Ordinary keys now use
the [shared profile output path](ASPECT_KEY_OUTPUT.md). The child's enabled
keyboard setting is an explicit maintained policy, not a newly proved native
startup default.

Keyboard acquisition now preserves the original scan/keypad identities through
the recovered BIOS normalizer; see [ASPECT keyboard acquisition](ASPECT_KEYBOARD.md).
This does not implement the still-unsupported local-key dispatcher.

## Raw backend compatibility

Native idle draining needs a consumer. The admitted parent renderer supplies
one, and an active WHEN pattern supplies another. A raw-only caller with neither
must retain bytes for explicit receive commands and ASIO return. The SERIAL
application build therefore adds a documented idle-admission hook to the
recovered dispatcher; its flat native and diagnostic builds remain unchanged.

| Backend | Queued input between ordinary commands |
| --- | --- |
| Admitted resident renderer | Native drain, matching and display |
| Raw backend with active patterns | Native drain and matching |
| Raw backend without renderer/patterns | Preserve for explicit reads and parent return |
| Native-composition diagnostic | Native drain with declared queue/clock models |

An initial integration used unconditional native draining for raw-only leases.
That consumed suffixes before parent handback and failed the existing FIFO and
mapper checks. The failed serial/directory runs remain under
`build/aspect-when-attempts/f53-native-idle-*`; final compatibility retains the
same assertions. The actual RX counter remains one physical word in every
backend. No fake zero-count alias is used.

## Validation

The runtime diagnostic passes825 actual8086 DOS cases and18,298 checks,
including33 authored WHEN cases, all149 unsupported opcode stops,255 unsupported
SET subcommands, and four truncated/invalid WHENCASE encodings. SET opcode9E
does not imply that other SET commands are implemented.

The full parent/child composition passes eight DOS cases/315 checks. A passive
timer observer qualifies the actual child PSP and DS=SS and records nonzero
native call depth/gate while the peer withholds END. It observes depth/gate2
for two pending calls. Tests cover C7/C8, local37, LIFO, XLT once, raw CSI
continuations, timeout versus Escape with observed pending calls, and typed
handler-error recovery. The real parent engine supplies DA/CPR replies and
retains screen/cursor/history. Neither the peer nor observer parses queries.

The original isolated receive fixtures remain unchanged. Their component
COMDATA tail values are distinct from full-program values: native idle drain
can consume the suffix before the following assignment. Explicit
`aspect_receive_runtime_overrides.json` records the composed expectations and
requires the old fixture hashes/expectations to match. Original full-flow
RG0/RG1/GCLEFT/RGGLOB traces corroborate this distinction. RGGLOB also needs
an advancing diagnostic clock after its initial assignment consumes input;
earlier frozen-clock timeouts are retained under `build/aspect-when-attempts`.

Useful commands, all through the pinned Nix toolchain:

```sh
./tools/dev --command python3 standalone/check_aspect_runtime.py
./tools/dev --command python3 standalone/check_aspect_when_carrier.py
./tools/dev --command python3 standalone/test_aspect_script_serial_dos.py
./tools/dev --command python3 standalone/test_aspect_script_directory_dos.py
```

The carrier checker covers1,061 linked CPU inputs including all256 MSR values
on COM1–4, no-I/O closed-port behavior and shared state aliases. Separate child
RPC tests cover register/FLAGS/stack and actual DOS lifecycle. Physical modem
DCD/CTS timing and all full-application gates remain open.

Five additional actual UART cases distinguish raw-backend policies: active
patterns match during idle processing; absent/canceled patterns preserve exact
unread RAW bytes; a raw C8 handler executes after WAITFOR. The unchanged legacy
suite passes28 serial-script and15 metadata/preload cases. Final Synchronet
login uses WHEN to send the username during WAITFOR and passes all12 editor
checks through draft abort. ENiGMA's login/editor regression passes with explicit
30ms modem buffering and standard keys; the earlier immediate-forwarding failure
remains open. A fresh source-only tree reproduces all91 outputs byte-for-byte.
