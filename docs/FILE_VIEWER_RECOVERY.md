# Internal View a File recovery

The internal viewer's read/format/page contract is now recovered from the original
2.01 code and eight original-executable DOSBox workflows. A source-built
[incremental decoder](FILE_VIEWER_DECODER.md) and [read-only owner](FILE_VIEWER_OWNER.md)
now pass component checks; their composition and maintained viewer UI are still
pending. This evidence does not
enable Alt-V or change the selected physical installation.

[Provenance](../reconstruction/file_viewer/provenance.json) binds the original
regions and REA Evidence IDs. The [runtime receipt](validation/file-viewer-original.json)
binds generated input identities, passive observer source, complete captured VGA
frames and the original executable identity. Proprietary binaries, configuration
and raw analysis bundles remain in ignored local storage.

## Confirmed behavior

The controller at overlay20:E660 opens the file in binary mode (`rb`). The page
renderer at E898 calls the native `fgets` with a buffer-count argument of134:
each read consumes at most133 bytes, including a terminating LF when present.
The renderer clips each chunk to the screen width (statically capped at132),
then trims trailing bytes whose unsigned value is at most32. It writes the
remaining bytes directly as screen characters. It does not perform terminal
escape parsing, tab expansion, CR handling or80-column wrapping.

The actual80-column/25-row original workflows confirm:

- A line with80 visible characters and more input is clipped, rather than
  wrapped at column80. A133-byte chunk can occupy one row while its remaining
  characters are discarded visually; the next chunk occupies the next row.
  If the next chunk contains only CR/LF, that row is blank.
- An embedded tab, CR, ESC or Ctrl-Z survives inside a row as a raw screen byte.
  Ctrl-Z does not terminate the file. Bytes80h,81h,DBh,B0h andFFh survive exactly.
- An embedded NUL ends the displayed string, but the rest of that input chunk
  is consumed. Trailing spaces, tabs, Ctrl-Z and CR/LF are removed.
- Empty input displays a blank page with the original footer. An unterminated
  final line is displayed. A400-byte file without LF produces four rows:
  three80-character clipped rows and a final single character.
- There are24 content rows and a footer at row25. If a file ends exactly at
  the24-line page boundary, Page Down displays a blank page. Further Page Down
  does not change the captured page; Page Up restores the exact first page.
- A95,040-byte fixture advances to page23, starting at byte69,696/line529.
  This corroborates32-bit offsets rather than a64-KB seek limit.
- An absent filename displays `FILE NOT FOUND...`; acknowledgement returns to
  the prompt. Explicitly clearing its retained field then entering the valid
  filename opens the file. Escape restores all2000 terminal cells, cursor
  position and cursor shape in each normally sampled workflow.

The original hides its cursor by setting its position to row100/column200 in
these captures. Full viewer-frame checks include all character and attribute
bytes: content attribute07h and footer attribute71h with this reference PRM.
No claim is made about all possible configured colors or video geometries.

## Static observations awaiting further runtime coverage

The E7F8/E84C helpers maintain an array of32-bit offsets. Page Up moves back
two stored indices, renders and stores the following offset; Page Down renders
from the current offset and stores the next one. Home resets through the
controller. The Page Down helper decrements index100 before rendering and
caps the resulting index at100. This implies a native100-page navigation cap;
the present runtime fixture does not reach that cap.

The render routine computes a pointer one byte before its line buffer when
`strlen` is zero, then reads it in its trimming loop. That is a static
out-of-bounds concern, not an observed crash. The maintained implementation
must trim with an explicit length guard rather than reproduce this access.

The configured external viewer at DS:1EE1 is a separate command path. Its PRM
binding, quoting/length contract and launch integration remain unresolved.

## Reproduction and boundaries

Within the pinned Nix environment, run each case in a fresh ignored output:

```sh
./tools/dev --command python standalone/test_viewer_original_dos.py \
  --case binary --output build/viewer-original-new
```

Run the eight cases listed in the producer, then validate them together:

```sh
./tools/dev --command python standalone/record_viewer_original.py \
  --input build/viewer-original-new \
  --output build/viewer-original-new/acceptance.json
```

The producer requires the existing ignored original executable and reference
configuration. It is outside all source-only application build inputs. It runs
only the unmodified original, with8086/FPU-off emulation and a dummy UART. The
passive timer observer captures at most seven stable screens using an additive
checksum; it is not an exhaustive event trace. The checker compares complete
captured frames, not that checksum. The large-file fixture filters the observer
to the expected final page and therefore does not establish terminal restoration.

The first exploratory retry recipe appended to a retained filename and failed
to open its intended file. Its local report is retained in the receipt but is
not counted as an accepted workflow. The corrected fresh recipe explicitly
clears the field before retrying; no original bytes or settings were patched.

## Remaining implementation

Implement a bounded incremental decoder and a banked serviced viewer, with
read-only handle ownership, canonical file/share checks,32-bit seek positions,
close-error quarantine and exact frame/cursor restoration. UART/parser service,
capture/HOLD/printing, cancellation and carrier-loss/reconnect must continue
through the modal viewer. Validate original-frame comparisons and DOS error
paths before enabling Alt-V in the normal terminal. Preserve the full remaining
feature-parity inventory and physical Boca/SPA2102/SynthModem acceptance gates.
