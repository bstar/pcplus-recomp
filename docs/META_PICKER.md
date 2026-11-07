# Serviced Meta Keys picker

The file picker now has a source-built, serviced sorting/navigation/view core,
connected to the deferred filename prompt. Directory enumeration and live parent
integration remain separate. The installed application has not changed.

## Original behavior

The shared picker is overlay **1**, `d0d0..d301`; its redraw, selection, scrolling
and sorting helpers are `d304`, `d38a`, `d3e9`, `d446`. It is called by the Meta
Keys loader in overlay 3. The analyst replay explicitly maps both overlays from
the SHA-checked original executable; the synthetic analysis image is never run.

REA authorities include dispatcher
`ev_8b25472dcd7a958eb15c1e63715c94accb2205d1fcb6ac8c4bb2088d26653844`,
redraw `ev_f03b1432a4d9edd777f5643602db22563b9d527c04eeeff3240aa0592a937e8e`,
selection `ev_aa6d23793e2ce95eb157688a31514bbe2bd8bb4c8b7ac3373e0a828b30993c3a`,
scroll `ev_64151658e4cec1076946bc2dc8807977913d33b9d0d96819726caee125a4ff5d`,
sort `ev_583409ca6ae642e00a7b56e8c9d9a74cf1f33776015147ae4813c06ca456d5d5`
and its case-insensitive comparator
`ev_499bb65ce9d48fc563cebd97e586e76391be37202ae00754bec35ba734755848`.
The original SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.

The native picker uses nine-byte stem slots and a 15-row viewport. Up/Down move
within that viewport and scroll one line at its edges. Home selects the first
entry. **End selects the first row of the last full page**, rather than the last
entry. Page Down can show a partial last page. Page Up resets selection to the
first row when moving a page, but does nothing to selection when already at the
first page. Boundary arrows do not ring; unsupported keys do. Enter selects;
Escape cancels. The list is ordered using ASCII case-insensitive comparison.

The explicit original-instruction replay executes the dispatcher, helper and CRT
sort/string bodies with synthetic enumeration and modeled formatting, window,
keyboard and bell services. Its corpus covers 99 cases, 2,431 pre-key states,
counts 1..350, mixed case, punctuation, eight-byte names and high CP437 bytes.
The analyst stack is moved beyond list storage. This is not execution of DOS
FindFirst/FindNext or VGA, and does not establish original behavior at 1,001
entries. The original's stated capacity is not treated as proof of its storage
safety. The [frozen fixture](../standalone/fixtures/meta_picker_native.json)
contains authored input names and observed outputs/states, not original binaries.

## Source core and composition

`meta_picker.c/.h` takes 20 bytes of caller-owned far state and a separate
9,009-byte far table for up to 1,001 stems. Collection, sorting and interaction
are explicit phases; no allocation, DOS, BIOS, blocking keyboard or UART access
occurs. Each sort step performs at most 64 adjacent comparisons, so a future
foreground owner can service the terminal between steps. This is a maintained
stable sorting implementation, not recovered sorting machine code. Distinct
synthetic names produce the original ordering; duplicate-input behavior is not
claimed as native parity.

All buffers are bounded, nonwrapping and disjoint. Outputs are refused on alias
or before acceptance. The caller owns table lifetime and must not mutate it
while the picker is active. The supplied 80x25 frame view draws list cells at
native rows 5..19/column 35; its border is authored and bounded to rows 3..21,
columns 32..47. It does not acquire VGA ownership or restore a previous screen.

The actual source-built DOS8086 diagnostic checks sorting, viewport/selection,
bells and selected names against every native trace, and verifies list cells and
unchanged cells outside the view. A separate reverse-ordered 1,001-entry case
checks maintained capacity and limit refusal, not original capacity parity.
Argument guards cover segment wrapping, table/output aliases and an invalid
viewport that would otherwise wrap an unsigned sum. Far table/state placement,
DS=SS and the linker's null guard are checked.

The same executable composes empty filename Enter → picker → selected stem →
normalized `.KEY` load request, and no-entry cancellation. File enumeration is
still supplied by the fixture; this is not a user-ready file picker in PCPlus.

```sh
./tools/dev --command python standalone/build_meta_picker.py \
  --output build/NEW-meta-picker
./tools/dev --command python standalone/prove_meta_picker_source.py \
  --build build/NEW-meta-picker --output build/NEW-meta-picker-source
```

An isolated ten-file source export repeats the executable and complete DOS
checks without original executables, private files, prior objects or ancestor
Git. The outer pinned Nix environment supplies tools. The
[receipt](validation/meta-picker.json) binds the accepted source/product identities.

## Remaining integration

Actual DOS enumeration must preserve the caller's DTA and directory state, use
canonical resource search/claims, distinguish end-of-list from IO failure, and
retain an explicit capacity-limit outcome. The existing transfer enumeration
adapter documents Watcom's DTA behavior, but its global transfer state must not
be borrowed by the picker.

Missing-file defaults/create, checked persistence/live adoption, file/EXEC
admission and quarantine, modal frame/cursor restoration, application scheduling
and memory/capacity, BBS regressions and physical acceptance remain open. No
interactive parent/package/remote service has changed; RCE81708 is unchanged.
No complete feature-parity gate is closed by these component results.
