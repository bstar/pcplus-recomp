# Serviced history export

Open redisplay with Ctrl-PgUp and press W. Enter an ASCII DOS 8.3 pathname (up to63
bytes), then Enter. Existing files are appended; a missing file is created
exclusively. No replacement or truncation command is provided. Escape cancels
filename entry. During an append, Escape cancels the operation and keeps the
viewer open; accepted bytes remain in the file. A second Escape returns to the
live terminal. Alt-X closes the file, restores the live view and exits.

The output is the viewer's frozen chronological native history, so later input
cannot change the bytes being exported. Stored CR becomes CRLF; other recorded
bytes, including Tab, CP437 and binary markers, pass through unchanged. A full
wrapped snapshot beginning with CR skips that oldest marker, matching the
recovered traversal rule. No newline is forced onto a final partial line.
An empty history does not create a file. W can append the same snapshot again.

Each foreground turn processes at most128 source bytes and writes at most256
output bytes. The main loop keeps polling serial, keyboard, capture and other
existing owners between chunks, and avoids HLT while export work is pending.
The checked file owner uses32-bit DOS positions/totals, including output larger
than64KiB.
DOS kernel calls themselves can take time; physical disk latency, UART throughput
and hardware flow timing remain unverified. Sustained receive backlog can defer
idle work until the input catches up, as with search.

## File ownership and failure behavior

History has a fourth fixed checked file owner, with the same96-byte result and
134-byte private descriptor ABI used by the capture/snapshot/monitor owners.
All four protect each other's result/descriptor input spans and canonical open
or uncertain identities. DOS Truename precedes acquisition. Append opens
write-only and seeks END on that same handle. Only actual file-not-found permits
exclusive creation; invalid paths, devices, readonly files and other-owner
collisions never fall back to replacement. These are in-process DOS identities,
not external-process locks or proof about host hardlinks/remapped drives.

Positive short writes and DOS write errors retain their exact accepted prefix,
stop further output and close once. A close with an uncertain result is never
retried or forgotten. It prevents another history acquisition and blocks PROGRAM
so a child cannot inherit an unresolved handle. Normal shutdown reports unresolved
write/close/recovery failures with exit12. Preflight/open denial is shown in the
viewer and permits normal terminal use and exit. Append cannot roll back bytes
already accepted by DOS and is not crash-atomic.

The filename field and navigation remain local, with no terminal output.
The existing live-frame swap continues receiving/parsing/capturing and replying
while the stable viewer remains visible. A connection notice closes the viewer
and its current file before drawing over the restored live frame.

## Evidence and verification

[Recovery ledger](REDISPLAY_CLIPBOARD_RECOVERY.md) links original append/CRLF and
wrapped-ring traversal observations to retained static REA evidence. The live UI,
file safety policy and serviced scheduling are maintained implementations, not
recovered original source.

[Hash-bound validation](validation/history-export.json) combines27 linked inputs,
three production DOS workflows,167 damaged-frame/layout rejections, the full
70-command terminal regression and63 byte-identical Nix outputs.

The linked cases execute the actual far callback, fourth file owner, native
UART/parser and PROGRAM refusal. They check125,998-byte full-ring expansion,
DWORD append offsets, preserved binary prefixes, exact output, continued input,
partial cancellation, errors, close ambiguity, path guards, both directions of
four-owner exclusion and input aliases. Only kernel/BIOS/hardware boundaries are
modeled. Shared file-fault diagnostics also run in actual8086 DOS.

The DOS workflows create a real file, append twice past a70 KB prefix and deny a
missing destination directory without exiting with an error. An independent
INT1C observer records the success/denial footer. Exact chronological lines,
CRLF, final partial text, prefix preservation, repeated snapshot equality,
independent incoming cursor replies, local filename keys, resumed ordinary keys
and final UART/PIC/vector/video restoration are checked separately.

An initial unpaced missing-directory recipe did not reach the expected denial;
its retained fixture is `build/checkpoints/history-denied-unpaced`. The final
recipe adds a delay within its longer filename burst to stay below the BIOS
keyboard queue capacity. No runtime change was made for that retry.

```sh
./tools/build test-redisplay
```

Filename clipboard extraction/editing/tagging/paste, complete original redisplay
UI, other video modes and physical validation remain open. F11 is not closed.
