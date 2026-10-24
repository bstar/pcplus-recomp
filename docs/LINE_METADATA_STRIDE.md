# Logical row stride for line editing

The live NETWORK line owner now uses `screen_attribute_row_bytes` for logical
row arithmetic, deleted-field scanning, insertion/deletion shifts, vacated-row
fills and the native repair region's end. These operations previously used
literal80-byte rows. The [receipt](validation/line-metadata-stride.json) records
the changed default terminal, actual DOS regression and source reproduction.

`terminal_line_metadata_move` separates the two logical-plane shifts/fills from
physical video and native field repaint. The existing live owner still performs
admission, selects the previous attribute, calls the recovered video operation
and repairs any surviving field boundary. The kernel receives insert/delete and
the fill attribute, reads the logical row stride, and handles overlap in the
required direction. It preserves BP/BX/SI/DI/ES, leaves DS/SS unchanged and returns
with DF clear. Its caller must supply admitted disjoint near planes, a bounded
region and row-start cursor offset; this internal entry adds no unvalidated
user-facing mode or general memory API.

The actual linked kernel passes480 independent immutable-row comparisons:
240 at80 columns and240 at132. Cases cover restricted regions, intermediate and
final rows, heights1/5/24/25, insert/delete, three fill bytes, arbitrary field
marker/value bytes and both input DF states. The entire near data/BSS outside
the stack is compared, including nonempty receive/deferred state. Full4096-byte
plane tails, physical video and the far shadow must remain unchanged outside
the intended plane edits. BIOS/DOS and port access are forbidden in this kernel
test. The test enters the real linked far-code segment; it substitutes no
product instructions.

Existing live behavior passes512 parser/attribute cases with192 native field
repairs and45 refusals before editing, eight line-policy groups,24 native-return
callback checks and45 rejected layout/relocation mutations. An unmodified DOS
terminal run passes partial-region deletion/repair, clipped repeated insertion,
last-row large counts, full video/plane/guard comparison, cursor reports and
all42 sampled hardware bytes. That DOS fixture explicitly seeds protected
attribute metadata at one BIOS boundary; it is not a normal profile selection
or a BBS session.

The changed default terminal SHA256 is
`af1301a13bb82e2136cfe8e63138f8ed05cf205a98c9ed8de316cf079ea9b029`.
Its near data/stack remains65,440 bytes. A fresh397-file source tree reproduces
the executable exactly, without originals, old objects or analysis databases.

The fresh application build also exposed an integration error: the new native
width-request diagnostic was picked up by the modes-directory glob and entered
its flat `ORG` branch during OMF assembly. The builder now excludes that
separately owned native entry, as it already excludes the diagnostic modem
attempt. The source proof deliberately includes the width diagnostic file;
removing only its exclusion reproduces the NASM failure before an executable is
linked. The corrected source-only build passes with that file present.

## Reproduction and remaining work

```sh
./tools/dev --command python3 standalone/build_terminal.py
./tools/dev --command python3 standalone/check_line_metadata_stride.py
./tools/dev --command python3 standalone/check_line_attributes_live.py
./tools/dev --command python3 standalone/check_line_edit_live.py
./tools/dev --command python3 standalone/check_line_callbacks_live.py
./tools/dev --command python3 standalone/check_line_controller_layout.py
./tools/dev --command python3 standalone/test_line_attributes_dos.py --label UNIQUE_STRIDE
./tools/dev --command python3 standalone/prove_line_metadata_source.py --output build/UNIQUE_STRIDE_SOURCE
```

Use `standalone/record_line_metadata_stride.py --proof ... --dos ... --output ...`
to seal matching results. The new kernel check is also included in the ordinary
test and application-component source-proof workflows.

Live admission remains80 columns. The132-column checks prove logical-plane
movement only; native132 video/panes, field-repair composition, parser admission,
local UI, parent/child ownership and BBS width changes remain open in
[the integration boundaries](LIVE_WIDTH_INTEGRATION.md). The accepted branded
package and card have not received this change. No complete compatibility or
full-application gate closes here.
