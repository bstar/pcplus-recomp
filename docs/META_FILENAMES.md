# Meta Keys filename selection checkpoint

The original Load command opens an empty eight-character filename field. Enter
returns the trimmed length; **empty Enter invokes a separate file picker**.
A nonempty name is uppercased and receives `.KEY` if it has no dot. Save writes
the currently selected filename directly, without a Save As prompt. Escape from
the name field, or cancellation of the picker, leaves the selection intact.
These details matter when connecting the serviced Alt-M editor to checked IO.

REA static analysis of original overlay 3 observes load `e0d0..e16d`, save
`e16e..e189`, normalization/load/default behavior `e18a..e1cb`, and resident
callback `4aa7..4acb`. The original SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`;
the synthetic static analysis image has SHA256
`fff9700d3b5e76b8f0d76c3a9df7051bfa39f87c0891bd593a8f84f19c758b19`.
The synthetic image was never executed. Evidence:

- Load: `ev_01ef5e1485264783ea6b307d6d2fe014634648cec868abf0e81d369775c0bf71`.
- Save: `ev_8fd8e445cd7d6aec7df9937d24c275c7d372224b3c7f9882aadd233856636611`.
- Normalization/defaults: `ev_3c4203cbaaf4ae88d584aabfab5ca1e9c4e9c6c907a5638830cc6eeb55dabc8c`.
- Filename callback: `ev_6d9e4b765bd0be63bbc2a427f1f3e876ec2414074b9d4144f0ae8c57e68bd2a9`.
- Picker: `ev_b5f69bd5a2bcae47a2d2777f8bc324e0ad53ef9a36ba2106d466fe481c9e462d`.

The original picker is a substantial separate workflow: enumeration, extension
stripping, sorting, a 15-row viewport, scrolling and selection, with up to 1,001
entries. It is **not** implemented by this checkpoint. A deferred picker request
and explicit completion boundary preserve its place in the workflow.

## Serviced components and verification

`meta_filename.c/.h` implements the native eight-cell field with 22 bytes of
explicit caller-owned far state. All operations are serviced and memory-only.
Enter commits through NUL and returns trimmed length; cancellation writes no
destination bytes. The field starts empty even when the destination contains
text. Space/dot inputs are consumed without a bell. Tab and byte FF are raw
input here, unlike the Meta definition field; Shift-Tab rings the bell. Native
full-final-cell Backspace and Insert/cursor-shape behavior are preserved.

An explicit analyst replay runs the **actual original** shared-editor/callback
instructions from the SHA-checked original executable over synthetic bytes.
Only keyboard, rendering, cursor and bell services are modeled. The frozen
[corpus](../standalone/fixtures/meta_filename_native.json) has 314 cases and
1,304 pre-key states, including all 256 byte-valued keys and all eight cursor
positions. Source-built DOS8086 replay compares field bytes, cursor, shape,
bells, return values and all 64 destination bytes, including opaque tails.
No original executable participates in ordinary component builds.

`meta_file_prompt.c/.h` adds 92 bytes of far state for deferred name/picker/load
routing. Save immediately returns a request for the owner's existing selection;
Load collects a name or requests the external picker. Picker completion accepts
an eight-byte stem plus NUL. Normalization is ASCII case/extension processing,
not DOS filename validation, canonical identity or permission to mutate a file.
The eventual owner must resolve and validate the absolute target before IO.

The DOS diagnostic also composes the existing serviced Meta dialog, the new
prompt and real checked file IO over owned scratch files. It opens MAIN.KEY,
selects NEXT.KEY, loads its definitions, edits a definition, saves it and reads
back the exact result. Cancellation and failed primitive loads preserve the
active name/definitions. An explicitly missing primitive load creates no file.
This does not implement the original higher-level load/default/create policy.
Near/far argument guards and unchanged D:\LAB working directory are checked.
The prompt completion is modeled; there is no actual picker, VGA popup or UART.

```sh
./tools/dev --command python standalone/build_meta_filename.py \
  --output build/NEW-meta-name
./tools/dev --command python standalone/prove_meta_filename_source.py \
  --build build/NEW-meta-name --output build/NEW-meta-name-source
```

The diagnostic passes 5,555 checks. An isolated 23-file source export reproduces
its executable and complete DOS results without originals, private files,
previous objects or ancestor Git. The outer pinned Nix environment supplies tools.
See the [receipt](validation/meta-filenames.json).

## Still required for integration

The original higher-level loader initializes TEXT/empty definitions and attempts
to create a file when its read fails. Its defaults preserve other record-tail
bytes. Reconstructing that policy with checked IO, including missing-file creation
and distinguishing corrupt/unreadable existing files, remains required; primitive
load failure preservation is not claimed as original whole-workflow parity.

Actual file enumeration/sorting/viewport UI, resource search and canonical claims,
file/EXEC admission, baseline selection/adoption, close uncertainty/quarantine,
foreground scheduling, native VGA equivalence, application memory/capacity and
BBS/physical acceptance remain open. These components have not been linked into
the interactive parent or installed. RCE81708 and its physical acceptance remain
unchanged; no full F02/F05/F06 parity gate is closed.
