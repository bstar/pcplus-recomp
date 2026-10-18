# Native monitor and binary dump

This is a static F10/F12 contract ledger, not a live monitor implementation or
runtime compatibility result. Retained REA assembly establishes resident
`1aaa..1bbd`; the original executable was read only after verifying SHA256
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
No original application, synthetic analysis executable, private configuration,
media or BBS session was executed or opened. No new REA session was required.
Resident offset x maps to EXE file offset `1200h+x`; initialized DS begins at
file offset `25950h`. Saved exports are ignored analyst artifacts, never build
inputs. The following Evidence IDs refer to assembly, not inferred pseudocode.

## Entry, keys and lifecycle

The executable advertises `MONITOR    Ctrl-\` at EXE26630h / DS0ce0 and
`Monitor Mode ...` at EXE261e3h / DS0893. The actual keyboard dispatcher1604
proves the advertised key:1930 subtracts001ch, branches to18f8 and calls1aaa.
This is a literal normalized keyboard word001ch. An arbitrary BIOS word with
low byte1ch and a nonzero high byte is not established as equivalent here.

`1aaa()` is near, no argument, preserving BP/SI/DI and restoring SP. AX/BX/CX/DX,
ES and flags are not a general preserved-register ABI. Its275-byte body:

1. Sets DS332c=1 and refreshes status2fb8. Saves word1d6e locally, clears it
   (disables the KEY/hook trigger during the modal session), and clears/homes
   the terminal through24e2.
2. Saves a screen image and draws the prompt window with3fc7(329e), retaining
   returned far pointer DX:AX. Displays `LOG TO DISK? (Y/N)` (DS422a), then calls
   callee-clean6dde(default0, attribute[1f7c], coordinate031ah).
3. If the answer is nonzero, resolves `PCPLUS.DMP`, opens it in `wb`, and stores
   a private near CRT FILE pointer at BP-2. Local DI means logging requested,
   **not** open succeeded. Restores the prompt window/screen through4015.
4. Repeatedly sets help context397a=0019h. If RX count8e20 is nonzero, dequeues
   exactly one aa65 value, draws one character through0730, and optionally
   writes the original value to the private FILE through8436. It then checks
   keyboard availability651a and, when available, reads through64fe.
5. Exact keyboard001bh exits. Exact001ch is ignored, preventing recursive
   monitor entry. Every other key is put in cffa and passed to the ordinary
   dispatcher1604: this is not a monitor-specific read-only key whitelist.
6. If logging was requested, calls fclose on the private FILE once, ignoring
   its return. Clears332c, restores the saved1d6e word, clears/homes through24e2
   and refreshes2fb8. It does not restore the pre-monitor terminal contents.

6dde accepts Y/y as1, N/n or Escape as0; Enter retains default0. Other input
beeps and repeats. It returns AX and consumes its three word arguments with
RET6. Thus Escape at the initial prompt selects a monitor without disk output;
it does not cancel monitor entry. Escape during the main loop exits monitor.
The normal keyboard reader6530 can intercept Alt-Z for contextual help using
397a. The direct initial651a check is not itself a general application poll.

No idle timeout, cancellation flag, carrier-loss exit or foreground task handoff
is present in1aaa. RX ISR operation continues, but the loop is synchronous.
One-byte rendering/file IO and nested ordinary key services can delay dequeue;
there is no native overflow accounting, checked-write failure stop, or owner
admission against capture/transfer/program work in this body. Ordinary keys may
transmit through1604/ab0b and may invoke other local services. That is a real
integration dependency, not evidence that those nested paths are safe.

## Bytes on disk versus displayed characters

| Dequeued SI | Argument to0730 | Attribute word1f70 | Argument to8436 |
| --- | --- | --- | --- |
| 0000h |0030h (`0`)|[1d34]|original0000h|
| 001bh |001bh|[1d34]|original001bh|
| 00ffh |003fh (`?`)|[1d34]|original00ffh|
| all other values |zero-extended low byte|[1d32]|original SI|

The renderer is called directly, bypassing0610's control/escape dispatcher and
09b6's processed capture/printer logger. CR0dh, LF0ah, SUB1ah and DEL7fh are
not filtered or newline-expanded by this monitor body. They, NUL, ESC and FFh
are passed unchanged to binary putc when received at this boundary. There are
no per-byte headers, timestamps, separators, character attributes, CRLF record
boundaries or end-of-session marker in the examined writer. Binary CRT output
is distinct from the normal append-text capture policy. Renderer0730 still has
its own charset/translation/metadata branches; the table proves its argument,
not every resulting glyph for all profiles. Native entry leaves the last
selected attribute in1f70 rather than restoring the pre-monitor attribute.

This is **UART-dequeue data**, not an unconditional physical-wire recorder.
aa65 loads a ring byte then ANDs AX with configured word8e22. Its RX count and
read-pointer/flow-resume logic are shared with ordinary input. The original ISR
checks software-flow flag3354 before queueing: received11h/13h change TX pause
state and return without entering the ring when software flow is enabled.
With that flag disabled they follow normal queueing, subject to capacity and
other hardware constraints. UART framing/parity/7-bit configuration and receive
mask can already have changed which bytes reach monitor. No TX stream is
written by1aaa. Local echo can traverse ordinary terminal/log routes, but that
is not evidence of outgoing bytes being appended to this DMP FILE.

## DMP filename, overwrite policy and missing reader

DS468bh is `wb`; DS468eh is `PCPLUS.DMP`.1afd pushes the binary mode, calls
353d on the name, then fopen841a.353d first tries fopen(name, `r`) and closes a
successful probe. If that fails, it looks up getenv through the pointer at
DS324c (initially the string `PCPLUS`), copies the value into global8f0a,
appends `\` if needed, and concatenates the supplied basename. Without an
environment value it returns the original basename. This resolver has
unchecked copies, no path-capacity/error reporting, and a nonexclusive probe
before subsequent open. An existing file found by that probe is subsequently
opened `wb`, which is a truncate/write request, not append or no-overwrite.

Only the retained1aaa assembly references literal468e among the searched saved
resident and overlay function exports. No DMP reader/replay parser or separate
DMP container format is established. This bounded search does not prove that
all indirect filename construction or every unexported original path was
covered. The `.DMP` filename is therefore explained by a concrete binary writer;
a replay UI or special file header must not be invented from the extension.

## UI and ownership contracts

`3fc7(descriptor)` is caller-clean2, returning allocated saved screen as DX:AX.
Descriptor329e initially contains five words `(1,5,5,30,1f7c)`: the final word
is an attribute pointer, dereferenced for7088.3fc7 brackets UI through6b5a,
6e78(64c8), allocates/copies video memory through6bbe, conditionally calls775a
when1d3e is set, then draws the window through7088.6bbe allocates using
word7a7c and copies that byte extent from configured video segment7a78. Failure
is passed to488f; this is not a checked optional-null window contract.

`4015(descriptor, saved_offset, saved_segment)` is caller-clean6, matching the
monitor's push(segment), push(offset), push(descriptor). It passes descriptor
words and the far pointer to callee-clean732e (RET12), calls6b42, and does not
return an owner token.732e eventually calls7558 with the saved far pointer;
7558 restores configured video memory and frees the allocation via85fc.
Animation/cursor policy lives in these recovered services. Critically, monitor
clears the terminal **before**3fc7 saves it: this save/restore pair removes the
initial prompt; it is not a preserved pre-monitor terminal view.

The DMP FILE is private to this invocation. It is not D114 (processed capture)
or8ff0 (printer).1aaa does not disable/close398a capture,398c hold, or3988
printer state; received monitor bytes bypass their09b6 branch. Ordinary local
dispatch can still operate these services. There is no same-path exclusion
against other CRT streams, and fopen/putc/fclose outcomes are all unchecked.
A failed open can therefore leave logging requested with a null FILE pointer.
Exact diagnostic recovery should expose that gap rather than replace these
calls with successful no-ops.

## Next implementable units and bounded integration policy

- Recover1aaa as the275-byte modal owner, and353d as the105-byte filename
  resolver separately. Link actual0730,UART dequeue, keyboard and CRT putc/
  close for diagnostic composition. UI3fc7/4015 and prompt6dde contracts are
  established here; preserving them requires their real dependencies.
- A maintained foreground monitor should explicitly own RX, admit only when
  transfer/modem/parser/program owners permit it, retain services for UART/flow,
  and expose bounded cancellation. It can use the recovered three special-byte
  display rules without routing incoming ESC through the terminal parser.
- A checked binary dump needs its own admitted file owner and explicit policy
  for overwrite versus exclusive creation. The current capture/snapshot owners
  must not silently be reused while active. Disk partial-write/close failures,
  same-path aliases and ambiguous close need truthful states. Native `wb` and
  unsafe environment fallback remain distinguishable from a safer live policy.
- Required component tests: all256 dequeued bytes and restrictive mask, 11h/13h
  under both software-flow modes, Y/N/Enter/prompt-Escape versus loop-Escape,
  ignored Ctrl-\, ordinary-key handoff, disabled/restored hook, screen-state
  ownership, actualbinary NUL/SUB/FF, failed open/write/close, and no lost RX
  during prompts or cancellation. No such runtime results are claimed here.

## Evidence register

| Saved resident assembly | Evidence ID |
| --- | --- |
|1aaa modal monitor|`ev_0f26ef2aff3f6adb5aabe206ab2baa495cbdb748081537ed07650e2ba498d55e`|
|1604 keyboard dispatcher|`ev_b21291abf4490cc6ecbcbe1f8b3a97938d5a9915fa4cc5c5213f0ec2a523534e`|
|353d filename resolver|`ev_1cd43dbde8697560fddafd763fd3ab56971d91bd6badd8b88553d8e1cc1d6417`|
|aa65 dequeue|`ev_2f3a515406feeefac19bd44ae69af23f38391f6d69628dfad4636e172193ffee`|
|0730 character renderer|`ev_9c6a5e39afa954b0ee6e1ccd4e0b1e9a0875c99f4ca252e5a1fa2e8cd62b53ec`|
|2fb8 status|`ev_37f3de96121de4b87b610528664677582883ea518eaecb770ba29ed10ada9cbe`|
|6dde Y/N prompt|`ev_974957d973c0620063fb4517598f57d6d1733280f7852f9de54d5584a9cedd03`|
|651a keyboard peek|`ev_48d6c28112f790241be86ebec067721a418d9ec212038de6cac7db98e3c85f4f`|
|6530 help-aware peek|`ev_f068e7ff28145081cb89976d9e59818dda36b27f1e902dcc5fc2cd19fc56f095`|
|64fe keyboard read|`ev_a0803ef1cf06eceb0e6ac4bb68eaa1be812e5057c364829c740ea0b7a4c7a479`|
|3fc7 screen/window save|`ev_514475ed9cfddeb91f68952bf4a780db041beb823867d9db10634444d6421ee5`|
|4015 screen/window restore|`ev_53e4920fe7959b99129f397b07124585bbee97a90399ed526b7b78fa56bd13b2`|
|6bbe video allocation/copy|`ev_d12ff3b06d0e6d51cebfd612a11c0fd10c5c7026cb8b350a0cfca83e4f49ebf1`|
|732e restore owner|`ev_e784b51c6ffb9c2ec3ef059cbdfa5125d6f6338b5000b212603e562418b4dc32`|
|7558 video restore/free|`ev_85669903ca2eb10f5e0aea847b7bc0c230ca5f7bc349a17cfbb2bf4c1fc83ad1`|
|8436 putc|`ev_9f27b2e0c4579953671867596b65615e5a6ceb853e73e9cb62527bedcb9239cd`|

Verified original byte anchors, end exclusive:

| Resident span | EXE start / length | SHA256 |
| --- | --- | --- |
|1aaa..1bbd|2caah /275|`f37c44a6f96de7f9b30801f8c5da90934c9ce621f29b8d9c23e3a36e9b83e8fe`|
|353d..35a6|473dh /105|`c7ec6dcd6c2a8f0bd8bbe662d0c4e31f1fa7db0b4c2b844848a054bc47fa3319`|

ISR software-flow branches accb/ad09..ad40 are already preserved in
`reconstruction/uart/core.asm` with original addresses and provenance in
`core-provenance.json`. Existing [CAPTURE_NATIVE_INVENTORY.md](CAPTURE_NATIVE_INVENTORY.md)
provides the independent processed logger/printer contracts; this monitor
ledger does not change those scopes.
