# Source-owned ASPECT recorder and byte-exact replay

The [source-recorder checkpoint](validation/aspect-recorder-source.json) accepts
the bounded recording core and its complete DOS file/compiler/UART replay path.
It passes17 host cases, six actual DOS recorder cases and six production raw-
output UART cases. Foreground terminal recording, its start/stop UI, shared file
ownership and full F13 acceptance remain unfinished.

`src/aspect/recorder.c` consumes explicit successfully transmitted bytes, rather
than inferring wire data from keyboard words. That preserves expanded bindings,
CP437, NUL and FF. It records backspace as a transmitted byte; it does not erase
earlier wire history. Transmitted groups hold at most40 raw bytes. A boundary,
incoming prompt or successful stop flushes pending data. Received prompts keep
the last16 observed bytes, preserving the documented native leading-control and
NUL filtering. Quote construction uses bounded STRPOKE statements; caret and
adjacent1E/1F encodings avoid the native decoder ambiguity. Generated prompt waits
exit on timeout before sending the following recorded payload.

The generated ASP requires the maintained runtime. Original formatted TRANSMIT
cannot represent every byte because FF means NUL and caret/pause syntax changes
the output. Both maintained compilers therefore accept the explicit extension:

```text
transmitraw "00225E7EFF"
```

It sends00,22,5E,7E,FF literally. Its string operand holds0..80 even hexadecimal
characters, optionally through a string variable. The runtime validates the
whole operand before sending any byte; an odd length, non-hex character or
oversize value cannot transmit a valid prefix. Output uses the ordinary bounded
UART/error/cancellation service, bypassing formatted caret/pause/FF conversion,
local echo and character delay.

The maintained extension is `D7/01`, outside the original215-slot opcode table.
It does not claim recovery of an original command and does not replace a native
slot. Legacy ASX portability is not claimed for generated recordings. Existing
TRANSMIT semantics and the exact native flat dispatcher remain separate checks;
other unimplemented original commands remain explicit failures.

The core borrows no path. Start transfers one stream-close obligation after
argument/state admission, including when the first header write fails. Output
callbacks report status and actual count; positive short writes complete in
bounded progress, while zero/oversized reports fail. Stop preserves the pending
tail and closes exactly once; cancellation closes without publishing a partial
script. The first write failure remains primary when close also fails. Repeated
stop/cancel does not close again. Reentry and active-session replacement reject.
Callers must use unpublished scratch output and publish only after successful
stop. The diagnostic DOS publisher follows that contract; the production shared
file owner is now implemented and separately tested in the
[checked publisher](RECORDING_FILE.md). Terminal integration remains required.

| Evidence | Scope |
| --- | --- |
|17 host core cases |All-octet/reverse output, one-byte short writes, prompt construction/sliding/filtering, cancellation, header/write/close errors, reentry, invalid/state calls,32-bit counters and reuse. File callbacks are modeled. Generated complete sources compile. |
| Six DOS recorder cases |Actual far callbacks, DOS files, DS=SS, one close, DOS compilation and production UART replay. Ordinary and quote/caret/control/FF prompts precede exact all-octet output; a2048-byte payload also passes. A wrong prompt emits only READY>, then exits. An actual write through a stream opened read-only and cancellation publish no ASP/ASX. |
| Six production raw-output cases |DOS-compiled scripts send256 and2048 exact bytes and mixed raw/legacy output. Odd/late-invalid hex and missing serial attachment emit no bytes. INT0 and sampled UART/IRQ/PIC state restore. |
|1125 composed DOS VM cases /27030 checks |Includes eleven raw-output source vectors and three unknown/truncated extension cases, alongside the existing native command/ownership regressions. Serial fixture callbacks are diagnostic models. |
|2025 DOS compiler cases |1059 accepted/966 rejected, byte-identical to the maintained host compiler, including all eleven extension vectors. |
| Legacy runner / native dispatcher |21 actual DOS child runs/105 checks;590 dispatcher CPU cases and3616 DOS checks. Native flat SHA256 remains `d2006fe5dd53b6416aec915c9bd58b4ae1a11fc003aafef090279fa2d37520a6`. |

The initial extended-dispatch build required a near jump because its original
short jump no longer reached; the exact native flat build retains its original
jump. A nine-character authored fixture name was correctly rejected by DOS8.3
path validation and was renamed without weakening the validator. That failed
diagnostic receipt remains under ignored storage. Initial UART diagnostic build
and sampler-mount mistakes are also retained; only the completed campaigns are
accepted in the public record.

```sh
./tools/build test-aspect-recorder
```

This target builds the maintained compiler/runner and creates fresh owned test
directories. The [shared canonical reservation prerequisite](CAPTURE_RESERVATION.md) now
supports recorder target/scratch identities alongside all four existing sinks.
It preserves their ABIs and tests real separate-bank calls, aliases, reentry and
modeled uncertain ownership. The [checked publisher](RECORDING_FILE.md) and its
[code-bank integration](RECORDING_BANK.md) now pass separate component campaigns.

The component is not yet connected to the terminal's Record command.
Remaining work is foreground owner storage, start/cancel/stop UI and
foreground taps for received prompts and successfully emitted user/binding data.
Transfers, scripts, child programs, setup/port moves and error/exit paths need
explicit owner exclusion and cleanup tests before normal publication. Modem/BBS
acceptance must then exercise the integrated recorder with the resulting build;
the earlier stock audio campaign binds its own frozen ASPECT binary and sources.
