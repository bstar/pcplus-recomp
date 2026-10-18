# Filename clipboard

The maintained terminal provides a15-entry filename clipboard through **Alt-=**,
or **C** from Ctrl-PgUp redisplay. It shares the existing frozen-view/live-screen
owner rather than allocating another full-screen buffer. BIOS mode3/page0,
80x25 VGA-compatible text is required. The existing redisplay ownership gates
refuse entry while a parser continuation, transfer, PROGRAM, macro, raw monitor,
printer controller, BREAK or incompatible viewport owns the terminal.

The list supports A add, E edit, D delete, U confirmed purge, Space tag,
Up/Down/Home/End selection, R decimal separator byte0..255, and P all/S single/T
tagged paste. C selects filenames from the held screen: Tab/Right/Down advances,
Left/Up moves backward, Enter adds and advances, Escape returns to the list.
Another Escape returns to redisplay or the updated live screen. Alt-X cancels
owned output and follows normal shutdown. Local keys do not reach the peer.

## Recovered data and packet behavior

`src/clipboard/clipboard.c` is a separate DOS16 near-cdecl core with caller-owned
214-byte state. Add uppercases ASCII, trims trailing spaces, rejects duplicates
against all15 slots and appends at the allocated count. Edit preserves typed
case and duplicates and may leave allocated empty entries. Delete compacts names
and tags; purge keeps the separator. The source-owned UI uses bounded navigation
instead of repeating the original empty-slot search indefinitely.

Extraction follows the recovered ASCII byte predicate and1..8-character basename
plus1..3-character extension. Longer extensions truncate; extensionless names do
not match. Row edges are bounded delimiters; the original reads neighboring
bytes without that bound. Names refer to remote prompts and need not exist on
local disk. No local file lookup is performed.

All/tagged paste traverses allocated entries, including edited empty strings,
placing a separator after **each** selected entry and one final CR if any entry
was selected. Single sends the first allocated name plus CR, including an edited
empty first name. The maximum packet is196 bytes. Empty list/tag selection sends
nothing. Default separator is CR; R changes the session value. PRM offset04EA
contains the recovered original saved word, but maintained import/persistence
and its original Setup control remain unfinished.

## Serviced output and cancellation

The CONFIG_CODE core/UI use one explicitly checked three-word cdecl callback to
the resident transport. Admission repeats ownership checks, requires an empty
1024-byte foreground TX ring and enqueues the whole bounded packet. Incoming
parser replies may queue behind it. Each **successful UART write** decrements
its remaining prefix; a queued byte alone does not count as delivered. Only
then may Single remove its first entry. This means delivery to the UART, without
claiming remote application receipt.

Escape during a stalled/partial paste removes only its unsent prefix and keeps
a Single entry; later parser replies survive. A prefix already sent cannot be
retracted. Connection owners explicitly mark a discarded clipboard queue failed
through a MODEM_CODE resident-service bridge. A cleared queue cannot masquerade
as successful completion. Retry may repeat a previously sent prefix.

Foreground frame swaps continue servicing actual UART receive, parser, history,
capture and replies. UI keys encountered inside a parser continuation can change
local state but defer painting until the redisplay idle owner has saved the live
screen. Clipboard idle polling repaints only a changed/restored view.

## Validation and limits

`./tools/build test-clipboard` builds CLIPCORE.EXE without originals, runs614
linked core inputs and559 assertions in actual8086 DOS. Optional
`./tools/build test-clipboard-original` compares321 cases against the genuine
resident byte/extraction routines and raw original overlay15 dispatch. Original
UI, beep and output boundaries are explicit fixtures; actual original string
helpers and Single compaction execute. Synthetic analysis executables never run.

`standalone/check_clipboard_live.py` exercises46 linked production inputs under
modeled BIOS/video/UART hardware, including binary196-byte packets, three ring
origins, stalled transmission, partial cancellation, preserved parser replies,
actual modem cancellation, nested redisplay and deferred painting.
`standalone/test_clipboard_live_dos.py` runs two production DOS workflows: direct
list/tag/separator/one/all paste with incoming CPR and live-screen restoration,
and filename selection from redisplay. An independent INT1C observer records
visible list entries; a synthetic modem peer records exact bytes.

The first development DOS run exposed a near call from MODEM_CODE to the new
resident abort routine. It was replaced with a declared far service bridge and
is covered by actual connection cancellation and startup workflows. The first
wire assertion also assumed a contiguous series of separate pastes; a legitimate
CPR reply occurred between them. The test now accepts only that exact independently
checked reply between packets; packet bytes remain exact. The full redisplay
regression caught a header spilling into the first content row after adding the
clipboard shortcut; its label was shortened to fit within the header row.

This is maintained clipboard integration, not completion of F11. Original menu
and field-navigation parity, saved separator adoption, other geometries, clipboard
prompt workflows surrounding batch/single transfers and physical UART/modem
validation remain open. Clipboard local ownership excludes active protocol byte
streams; it does not inject filenames into binary transfers.
