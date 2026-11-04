# Original Screen Pause and live integration

`--screen-pause`, with `--original-reference --local-controls`, enables Alt-N
through the keyboard, original Alt-Z reference and View command browser. The
command sends XOFF, hides the cursor, saves the message row and displays
"Screen paused. Press any key to continue...". One key resumes; that key is
consumed locally, including Escape, arrow keys and Alt-X. The saved row and
cursor shape are restored, then XON resumes the peer. A later Alt-X exits normally.

## Original evidence

The original BIOS scan table maps scan31 to resident BA6F, whose PLINK thunk
selects overlay3 entryDD7E. The recovered [74-byte body](../reconstruction/local_controls/pause.asm)
matches genuine original bytes at fileF3FE..F447 exactly. It calls AB0B for
XOFF/XON,6E5A/6DCA for cursor visibility,765C/7682 for a selected cell region,
3226 for the centered message and64FE to consume one key. Its264-byte local
buffer and callee-cleaned save/restore arguments are retained in the source.

Fresh REA inspection of the genuine resident helpers and saved REA overlay
assembly establish these boundaries. The overlay analysis image is synthetic;
its function bytes are independently checked against the genuine file, and the
image is never executed. The [provenance record](../reconstruction/local_controls/pause-provenance.json)
retains exact identities and Evidence IDs. The separate native CPU proof covers
120 cases with helper services modeled; it does not prove those helpers or the
live application equivalent by itself.

## Maintained application behavior

The live owner implements that sequence using the current UART and video
services; it does not execute the flat original-address body. The shared local
command guard defers entry during parsing, macros, child programs, transfers,
ASPECT, waits, monitor/controller and other screen ownership. The existing FIFO
preserves the deferred request until ownership is released.

While paused, only bounded serial/control polling and the one keyboard reader
run. Incoming bytes remain in the receive buffer, including parser queries,
until resume. Flow controls use the existing priority `uart_flow_pending` path,
so they remain responsive under CTS or peer-XOFF stalls. If THRE is unavailable,
the latest desired control remains pending; a quick resume may replace an unsent
XOFF with XON. The original synchronous THRE/CTS spin is deliberately not copied.
Shutdown also drains a pending manual XON when automatic SOFT flow is disabled,
with the existing bounded cleanup-error policy. No claim is made that a peer
ignoring flow control cannot fill the bounded receive buffer.

Connection notices are queued while Pause owns the status row. After its row
restore, the latest notice/restore event is applied using the real underlay.
This prevents a carrier-loss notice from capturing the pause prompt and later
restoring that prompt over the status bar. The DCD-loss regression executes the
real qualified carrier controller; it advances modeled BIOS time past its
four-tick low-carrier qualification deadline.

This initial integration supports the current page0,80-column color text modes
2/3 with25 physical rows. Unsupported video pages, widths, segments or viewport
geometry are refused before any XOFF or display mutation. Other geometries and
line/status toggles remain in full-parity scope. Status0 means executed,1 means
deferred,2 means reset baseline absent and3 means unsupported pause geometry.

## Verification and release boundary

Candidate terminal SHA256:
`501629c093d731be8f3324f185e128af76e00c2942e5ad3463c1ce7da54edb6e`.
Near DS/SS remains64800 bytes; resident CS is65176 bytes with360 spare. Pause
owns a two-byte active flag and connection notices add four queued-event bytes.
Four service adapters and six relocated far calls are checked independently;
ten damaged, unexecuted images must be rejected.

The [validation receipt](validation/screen-pause.json) separates native-component,
linked CPU, actual DOS, source reproduction and paced BBS results. The DOS test
uses a passive timer observer to capture two equal screens a second apart while
the peer sends bounded in-flight text and a cursor query. Only after the actual
XON may its queued query receive a reply. Direct and Alt-Z workflows cover a
normal key and Alt-X resume, followed by ordinary keyboard traffic and clean exit.

The source-matched ASPECT interpreter remains byte-identical. Disabling Pause
retains the prior keyboard-bank binary. Original splash and packaged START/SETUP
checks are separate from installation. No modem settings, physical machine files
or live BBS/bridge services are changed. Physical BUSY diagnosis, analog timing
and original feature-parity gates remain open.

```sh
./tools/dev --command python standalone/check_pause_native.py --output build/NEW-native
./tools/dev --command python standalone/check_screen_pause_live.py \
  --terminal build/NEW-parent/TERMINAL.EXE --output build/NEW-live
./tools/dev --command python standalone/test_screen_pause_dos.py \
  --terminal build/NEW-parent/TERMINAL.EXE --label NEW-unique-lowercase-label
```
