# Native Meta Keys editor components

The original Alt-M editor remains unavailable in the interactive build. This
checkpoint recovers three native components needed for that command and tests
their behavior independently. It does not select, package or install a new
terminal. The existing KEY executor and its strict reader remain separate.

Original executable identity:
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
REA/Ghidra 12.1.2 analyzed the existing overlay-3 analysis image
`fff9700d…`. That synthetic image was never executed. Each recovered function
independently reassembles to the identified original file range, with the exact
offsets, hashes, external data and service boundaries in
[provenance](../reconstruction/meta_editor/provenance.json).

| Component | Original relative range | Bytes |
| --- | --- | --- |
| Semantic defaults | `e24a..e261` | 23 |
| Text-field key filter | `e261..e294` | 51 |
| Selected-row editor | `e294..e3a5` | 273 |

REA evidence includes row assembly
`ev_9715e3d77e9540c7766bdcd522bb72e2dae440aa96513c0c0a338c292866cdc3`,
field-filter assembly
`ev_4d2fb7babb06d907ee451f5172b5786156748aefeac0e8996b678a9f7f173b40`,
defaults assembly
`ev_759edfe9e57c43926b819d4c40d8094b66cede44556408d4b01e2c039ff69468`,
and outer-dispatch pseudocode
`ev_a1a870d1d2c2754325165f8155f2645805d413818b24f53fbf8bf375476f9bbf`.
These are static observations; the separate source-built DOS replay establishes
the named component behavior below.

## Observed behavior and boundaries

There are ten 54-byte records: a kind WORD and 52 stored text bytes. Defaults
set kind 3 (TEXT) and the first text byte to zero, preserving the other 51 bytes.
They do not zero the complete table or create a file by themselves.

The row editor stages its kind locally. Enter or Tab enters the shared text
editor, passing the same record text pointer for input/output and a 50-byte
content limit. Other kind-selection keys cycle ASPECT, PROGRAM, HOOK and TEXT,
except Escape and Shift-Tab. Escape discards the staged kind. Shift-Tab commits
it and returns that key. A shared-editor return of -1 leaves the kind unchanged;
Shift-Tab returns to kind selection; other returns commit the kind and propagate
the return code. The four field-navigation control WORDs are restored on return.
The input wait limit is reset to the configured default after each key read.

The field callback changes Tab and Shift-Tab to Enter in the pointed key WORD,
returning the original Tab/Shift-Tab code. Code `00ff` returns -99 without changing
the key. All other 16-bit inputs return zero and leave the key unchanged. This
does not establish the meaning of that special code in every shared-editor path.

The outer dispatcher is statically observed at `df44`: Tab/Down moves forward
and Shift-Tab/Up backward, wrapping through all ten rows. R revises, L loads,
S saves and C initializes the definitions. Escape closes the window. Accepted
row edits already reside in memory; disk saving is a separate operation.
Filename selection, automatic creation, error prompts and the complete shared
text-editor cancellation policy are not reconstructed by these three bodies.

The row index must be 0..9 and the initial kind 0..3. These original bodies have
no defensive row/kind validation. A future live caller must provide it. The
native blocking key/text callbacks also need serviced ownership adapters before
they can participate in the terminal's foreground loop. Neither the original
wait loop nor a test service is currently linked into the interactive parent.

## Verification

```sh
./tools/dev --command python standalone/build_meta_editor.py \
  --output build/NEW-meta-editor
```

The ordinary source-only build uses three public ASM files and an authored
diagnostic host. Flat output matches all 347 recovered bytes. The OMF product
executes in actual DOS8086: all 65,536 field-key inputs, three nonzero-tail
default fixtures and 320 row scenarios (all ten rows, four kinds, eight paths).
Tests compare complete records and surrounding guards, staged-kind behavior,
return codes, saved controls, wait state, service arguments and call counts.

The diagnostic text service deliberately writes a marker even when returning
cancellation. That verifies the row body's aliasing and kind-commit boundary;
it does **not** claim the original shared text editor makes that same canceled
write. Keyboard, rendering and text editing are authored service fixtures. No
UART, file save, real UI scheduling or physical acceptance is exercised.

An isolated eight-file public-source export reproduces the exact diagnostic EXE
and repeats its DOS replay without originals, private data, prior objects or
ancestor Git. The outer checkout supplies pinned Nix tools. The
[validation receipt](validation/meta-editor.json) binds these finite gates.
Alt-M window/navigation, text editing, checked KEY persistence, live action-table
adoption and full F02/F05/F06 acceptance remain open.
