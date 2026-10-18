# Live raw monitor

The maintained DOS terminal enters raw monitor with **Ctrl+backslash**. A
source-built BIOS diagnostic verified DOSBox-X `ADDKEY c-\` as AX2B1Ch; the
live key route recognizes AL1Ch. Escape and prompt answers likewise use AL,
normalizing raw BIOS words with nonzero scan bytes rather than comparing the
original owner's already-normalized full words. This is a separate foreground owner, not an
ANSI display option or processed-text capture mode.

The prompt warns that **Y replaces `PCPLUS.DMP`** in the current DOS working
directory. Y selects binary logging. N, Enter or Escape enters view-only mode;
those answers do not create, truncate or append a dump file. Escape inside the
monitor exits it. Entry and exit clear/home the terminal as in the recovered
monitor path; the previous terminal image is not a saved viewer page.

Ordinary literal keys and configured network bindings are still transmitted.
Repeated Ctrl+backslash is ignored. Nested local capture/snapshot/transfer,
PROGRAM, ASPECT and KEY/TEXT actions are suppressed while the monitor owns
input. Escape is consumed locally. Alt-X and configured hang-up stop/close the
monitor first, then perform the ordinary exit or modem action. This does not
implement the original HOOK subsystem.

## Display and file semantics

Received bytes bypass ANSI interpretation and the processed-character capture
sink. Each delivered byte is shown through the actual character renderer:

| Received byte | Displayed byte | Default attribute |
| --- | --- | --- |
|00h|ASCII`0` (30h)|Bold0Fh|
|1Bh|Literal1Bh glyph|Bold0Fh|
|FFh|ASCII`?` (3Fh)|Bold0Fh|
|All others|Original byte, including low control values|Normal07h|

The attributes use the existing native normal/bold words1D32h/1D34h and honor
the explicit PRM values. The synthetic PRM test sets bold2Fh and verifies that
all three special bytes use2Fh instead of the default0Fh. Inbound
CR/LF, backspace and Escape are glyph bytes in this owner; they do not perform
normal cursor/control operations. The table describes bytes supplied to the renderer; its existing charset and
translation rules still apply. The display replacements never change the
binary log. A successful Y session records raw bytes exactly, including00h,
11h,13h,1Ah,1Bh andFFh, without newline or text-EOF conversion.

“Raw” describes bytes delivered by the UART API. Software flow control may
consume XON/XOFF before that API; an all256-byte wire claim therefore requires
HARD or NONE and a transport which delivers those bytes. This is not a Telnet
IAC decoder, physical line analyzer or replacement for modem-side captures.

The raw file owner has a256-byte buffer and an18-BIOS-tick periodic flush,
plus flush/close on leaving, hang-up and application shutdown. It uses a third
checked-file context, separate from continuous capture and snapshots. Explicit
replace is allowed only for a validated regular writable DOS path. Canonical
DOS identity prevents replacing a file already owned by active **or held**
text capture. Relative/absolute/drive aliases are covered; distinct DOS mounts
pointing at one host inode are not an established identity guarantee.

An open denial or canonical collision with no acquired handle leaves the
monitor usable in view-only mode and keeps existing files/owners unchanged;
this is nonfatal. Once a handle is acquired, write/short-write/close errors
disable logging, preserve partial output and latch a storage failure, reported
as exit12 on shutdown when no earlier error takes precedence. A write is not
blindly retried; uncertain close ownership cannot be forgotten or reopened.
Raw display can continue after the logging error. These maintained protections
must not be confused with the recovered native CRT's unchecked outcomes.

Continuous capture remains open or held while the raw monitor runs, but raw
monitor bytes never reach it. Leaving restores normal ANSI/text processing and
the prior capture state. The maintained monitor suppresses live KEY/TEXT/PROGRAM
dispatch for its lifetime. Original hook-enable save/restore is exercised only
in the separate native diagnostic; HOOK execution remains unimplemented.

## Admission boundaries

Live entry requires mode3, page0,80columns and25rows with the supported VGA
path. Unsupported CGA/nonzero retrace-port state is denied quietly before
native display services which can otherwise wait indefinitely. This is an
explicit live geometry limit, not physical CGA validation.

Entry is also denied while a transfer, macro, PROGRAM, partial ANSI parser or
non-idle/non-connected modem operation owns the foreground. An uncertain
monitor file owner prevents another entry. The prompt is state2, raw view is
state1, and ordinary terminal ownership is state0; logging is a separate flag.

## Independent actual DOS verification

`standalone/test_terminal_monitor_dos.py` uses fresh ignored synthetic media,
an explicit frozen source-built terminal hash and an independent TCP/UART peer.
It never supplies terminal-generated replies or replaces product callbacks.
Actual BIOS markers pace the raw payload. A temporary source-built INT16
observer chains the real keyboard read, samples B800 characters/attributes on
the actual digit2 marker before Escape clears the view, then verifies and
restores the original INT16/INT2F chains. Its observer was separately checked
with a source-built DOS video fixture. Alt-X closes the real serial endpoint.

Cases cover all256 byte values; Y replacement and view-only choices; absent,
existing and readonly dump files; more than256 bytes; literal/network key
forwarding and nested owner denial; processed capture active/held and canonical
DMP conflicts; normal ANSI/keyboard resume; an explicit unchanged synthetic PRM;
and final UART/PIC/IRQ restoration. The periodic case uses the independent DOS
INT21 trace to prove an actual write before close. Host-visible file size while
DOSBox's own stdio handle is open is not a valid periodic-flush oracle.

The selected actual DOS suite passed **15 of15 cases** on frozen terminal
`9d90aa1ad8ef629c45613b61c14212fee71a0191603b49a6760d60a861c5451e`.
The ignored artifact index is
`build/terminal-monitor-dos/frozen-9d90-checks.json`, with per-case hashes.
The initial PRM run had a test-oracle failure because it expected default0Fh
instead of the fixture's configured2Fh; its artifacts remain unchanged. A fresh
PRM rerun passed after correcting only the independent expected attribute.
The periodic trace proved a real write36 BIOS ticks before close; exact18-tick
and midnight behavior is covered separately by linked tests.

```sh
./tools/dev --command python3 standalone/test_terminal_monitor_dos.py \
  --sha256 9d90aa1ad8ef629c45613b61c14212fee71a0191603b49a6760d60a861c5451e --label fresh-monitor-proof
```

This harness does not establish physical modem/cable timing, software-flow
all-byte delivery, real disk-full or uncertain-close faults, complete HOOK/
ASPECT execution, other screen geometry or complete PCPlus application parity.
Linked failure/admission tests and the exact native monitor diagnostic are
separate evidence. No original application or analysis executable is launched.
