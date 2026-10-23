# Streamed help resource

The optional PROGRAM notice build reads `LOCHELP.HLP` from the current DOS
working directory. Alt-Z opens the view while a PROGRAM error notice owns the
display. The companion is generated from authored notice/serial descriptions
and the existing command-menu descriptions: 26 topics, 131 lines, 9,111 bytes.
No original help text or executable is an input to this build.

Build through the pinned Nix environment:

```sh
./tools/build help-resource
./tools/build test-help-document
./tools/build test-help-resource
./tools/build test-help-resource-combined
./tools/build test-help-resource-source
```

The ordinary child is `build/aspect-help-resource-parent/ASPECT.EXE`; its
`LOCHELP.HLP` companion must be copied into the DOS working directory. The
separate fault child is in `build/aspect-help-resource-fault`. These use the
existing capability16 terminal in `build/terminal-mouse-notice-input`.
The published/default products and the preceding two-topic help products
retain their existing executable bytes. Resource help is an explicit build
option requiring notice banking, sound, input and contextual help.

## Navigation and search

Left/Right selects a topic; Up/Down, PageUp/PageDown and Home/End scroll within
it. `/` edits a literal query of up to31 ASCII characters; Enter searches titles
and body lines with ASCII case folding. F3 advances to another matching line,
then another topic, wrapping once through the preceding prefix. Escape cancels
query editing or a running search. Outside those operations, Escape, Enter or
Alt-Z returns to the notice. No-match feedback keeps the current page visible.

CP437 text is preserved. The reader accepts LF or CRLF and lines up to80 bytes;
the view wraps a full80-byte line across74 and6 columns. Generated prose is
wrapped at74 columns. An absent file selects the preceding compiled two-topic
view. A damaged/unreadable opened resource displays an error page which can be
closed normally. Other open failures retain the existing input error policy.
There is no configurable help path or executable-directory search yet.

## Storage and ownership

`src/help/document.c` validates the index incrementally, reading one38-byte
record per admission step. Starting a topic requires at most two record reads;
text steps read at most80 bytes and publish only complete lines. Search is
resumable and cancelable. File positions are32-bit, including offsets beyond
64KiB and a search continuation after line65535. The file must remain immutable
while open; validation does not provide a snapshot against concurrent writes.

`src/help/resource.c` keeps two page buffers and owns a read-only DOS handle.
It does not load the complete index or file into memory. DOS open/seek/read/
close live in a small assembly backend, with no CRT file ownership. Code lives
in NOTICEINPUT_CODE; the ordinary child uses53,248 DGROUP bytes including its
8KiB stack. The terminal near segment is unchanged.

The input facade checks the underlying notice identity and generation before
idle resource updates and key dispatch. Closing retires the file before the
view; failed file close keeps its owner available for retry. View cleanup
retains the existing guarded snapshot/foreign-window policy, including discard
without stale repaint after the underlying window has retired. Transport,
flow, speaker and service work continue while help is open. Both notice clocks
remain paused. Unresolved ownership uses the existing process-retention policy.

## Accepted evidence and remaining work

[The independent audit](validation/help-resource.json) decodes the actual DOS
captures, checks current source/product hashes and preserves the selected raw
cohort under ignored build storage. It accepts:

- 168 host/8086 DOS reader/search checks, including a real seek beyond64KiB,
  short/read failures, malformed text and a65536 search continuation.
- 49 actual DOS view/controller checks, including exact frame and20-byte file
  handle table restoration, scrolling, full-width CP437 text and repeated use.
- Six terminal sessions across COM1/2, standard/enhanced BIOS, mouse-driver
  presence/absence, normal search, missing fallback and damaged-resource error.
  Search/F3/no-match/cancel are observed in actual captured help screens.
- 18 combined window/help/speaker failure sessions. Raw reports establish
  ownership retention, controlled repair, private stream preservation,
  callback retirement,508 queued bytes and successful subsequent DOS EXEC.
- A656-source rebuild reproducing four executables and two HLP companions;
  separate647/641/632-source proofs reproduce the unchanged earlier products.
- Four current loopback ENiGMA/Synchronet record/replay sessions. These check
  coexistence with the resource-enabled child; they do not interact with help.

The arithmetic adjustment in the format decoder also passes52 host/DOS checks
and a separate optional read of all47 topics/463 lines of the existing original
HLP. That original stays private, outside normal compilation and public Git.

Early diagnostic attempts exposed a host warning, an executable name beyond
DOS8.3 and unsupported near long-arithmetic imports from the bank. Those were
corrected before the selected passing runs. The audit itself corrected its
expected missing-file BIOS mode and CRLF literal to match the recorded inputs;
those audit failures were not product failures.

This is a maintained help implementation for the PROGRAM notice context.
The command-menu prose is shared at generation time; its existing runtime UI
and matcher remain separate. Broader context mapping, shared menu integration,
original PCHELP descriptor/process/UI parity, arbitrary OS/corruption failures,
other DOS kernels and physical hardware acceptance remain open. Full F01–F16
application requirements and Boca/SPA2102/SynthModem integration remain open.
