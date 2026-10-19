# Native SET handlers and integration dependencies

`src/aspect/set_commands.asm` builds 225 recovered bytes in fourteen flat units
and a relocatable OMF object. All flat units match PCPlus2.01 original ranges
and SHA256 values. Ordinary builds read maintained source and a public hash/range
baseline, with no original executable or installed configuration.

This component is not yet linked into ASPECT.EXE. The maintained runtime still
supports only SET WHENCASE. The [compiler checkpoint](ASPECT_SET_COMPILER.md)
already emits the selected eleven settings; application integration must also
provide the native status refresh and setting lifetimes.

```sh
./tools/build test-aspect-set
# Optional offline comparison with the locally retained original:
./tools/build test-aspect-set-compat
```

The source-only CPU checker passes 3,487 cases and visits all 101 recovered
instructions. It exercises every byte value on each of nine boolean/duplex
settings, all valid PAUSECHAR/TXPACE values plus boundaries, query helpers,
PAUSECHAR sign extension, decimal limit arithmetic and the DS=SS near ABI.
Byte reads, bounded numeric operands, status drawing and query destinations are
declared test boundaries. They are not emulated DOS UI, FILE or UART services.
The OMF object builds separately; these CPU tests execute the flat source units.

Independent original-program CPU replay covers 29 compiler-emitted SET records,
twelve query-helper cases and a raw RXDATA overwrite, using the original
dispatcher/table, wrappers and numeric readers. Query-helper coverage does not
establish GET source grammar. A separate six-case original replay verifies the
DISPLAY selector, mapping/WHEN monitoring, direct print and local transmit echo;
its renderer is an explicit capture boundary, not a complete terminal parser.

The [validation record](validation/aspect-set-native.json) binds these retained
reports, REA identities, maintained sources and current tests. Original SHA256:
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.

## State and native behavior

SET at5458 clears E38E, reads its subcommand, calls the DS:4D24 table entry and
tail-jumps to2FB8 status refresh. Native table indexing is unchecked; a maintained
application table must provide explicit unsupported entries for every other
byte selector. The generic setter stores a raw byte as a word. This differs
from the existing maintained WHENCASE wrapper's explicit boolean validation.

RXDATA writes E382, shared with the interpreter flow gate and receive echo
suppression. It overwrites the counter; it does not update an independent
receive-enable flag. KEYS ON writes1 to E380, disabling native local key service.
PAUSECHAR stores only the low byte at1D66 after checking32..126; its query helper
sign-extends that byte. TXPACE stores a checked0..999 word at1D68. Actual nonzero
transmit pacing still needs the calibrated6B72 platform service.

DISPLAY OFF affects received-lead rendering through4C3C/4C74. Mapping and WHEN
matching continue. Direct print, half-duplex transmit echo and status refresh
can still draw. The parent renderer lease must therefore survive DISPLAY OFF.
Raw escape continuations remain queued when the renderer is not entered;
matching them against the displayed parser's continuation behavior would be
incorrect.

## Status refresh work

The 515-byte2FB8..31BB status body already exists in
`reconstruction/terminal_reset/status_refresh.asm`. It depends on status data,
formatting, text/fill services and carrier state. The live parent's
`screen_viewport_refresh` currently stops explicitly, apart from a separately
paired capture-error path. That capture exception cannot provide SET refresh.
The existing resident renderer RPC has BEGIN/EMIT/END, with no status operation.

Recovery found a relocation omission at3044: the script-label pointer was a
literal D464 in the OMF build. It now uses `terminal_reset_script_label` while
the flat build retains native D464. A new linked regression first reproduced
the wrong D464 versus actual D565 pointer, then verified the corrected pointer
and label bytes against the original path. It stops at the explicit UART-status
dependency; it does not claim completed status rendering.

Next integration needs the remaining formatting/fill owners, bounded status
state/resources, a guarded resident status operation and deliberate adoption of
session settings. Parent near-memory headroom is48 bytes, so added code/data
must respect the existing far-storage and CONFIG segment strategy. Returning
success without the status operation would hide missing application behavior.

Retained REA evidence includes generic E6BB
`ev_0eac28aff291b49ec3d0558f8f05ee1eedb3010924224c14dc0014c056185ef8`,
decimal DDA7 `ev_c83f8fc5153ef8704ecf7828b52bc9309a198836822c9abf045419b163d1a79b`,
and status2FB8 `ev_37f3de96121de4b87b610528664677582883ea518eaecb770ba29ed10ada9cbe`.
Tiny wrappers and dispatcher also have exact original byte/range and CPU replay
evidence. No invented REA identity is assigned to those listings.
