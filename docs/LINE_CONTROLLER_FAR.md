# Line-controller code placement

The line-edit controller now executes in ASPECT_CODE while its four existing
near public entrypoints remain in the resident segment. This opens resident
address space for the remaining application work without changing line policy,
metadata algorithms or the Control-N wait. The full application remains unfinished.

| Layout | Before (`7477a19`) | Current |
| --- | ---: | ---: |
| Resident code bytes |65526|65246|
| Resident space available |10|290|
| Near data and stack bytes |64832|64832|
| Loaded module bytes |156008|156056|
| Minimum allocated module bytes |343824|343872|

The move frees280 resident bytes. The335-byte far controller remains loaded and
retained across DOS child execution. Its four resident adapters use explicit far
calls and near returns. Register-only callbacks perform the native insert/delete,
foreground poll, low-tick read and UART receive operations; the existing cursor
callback is shared. Geometry failure uses the existing explicit2d98 abort entry.
The ASPECT immediate-read callback now has its recorded caller in the far
controller, so memory inspection tracks that relocated reference separately from
the remaining resident renderer calls.

The exact native line routines, bounded plane owner, DS=SS data, wait flags,
36-tick deadline, local Escape/Alt-X behavior and modem ownership yield remain
unchanged. ORIGINAL still uses native per-line semantics and the serviced
Control-N wait. NETWORK still clips counts, preserves the column and uses bounded
active-region metadata operations and real native field repair.

A frozen source-built previous executable/map is compared with the current image
in192 line cases and96 wait cases. The comparison checks full planes/video,
state, BIOS effects, serial output, remaining keys, tick reads and public callee
registers. The wait cases include Control-N with unread trailing bytes, Escape,
Alt-X, another ignored key, timeout near low-word wrap and active modem yield.
This characterization intentionally uses the prior maintained build; it is not
an input to ordinary application builds or fresh source proofs.

The current-source-only callback suite requires no previous executable. It checks
six register-only callbacks with empty/nonempty receive and two initial FLAGS
states, for24 cases. Every callback return must preserve all general registers
and FLAGS observed at its actual native return. Direct near calls separately
verify state/BIOS effects and declared scalar/callee results. The native BIOS
cursor path leaves the low byte of a temporary stack pointer in volatile BX;
its numeric value changes with the extra far frame. The test does not invent a
stable BX result, and still observes exact propagation of the actual native BX.

Serialized image checks reject45 damaged entry targets, near/far returns,
missing relocations and invalid controller extents. Existing512 bounded plane
cases,45 pre-edit state rejections and eight policy groups remain current
regressions. An unmodified DOS executable with declared test-only plane fixtures
checks full backing guards and exact video. Actual DOS ASPECT cases cover native
edits and the ORIGINAL Control-N wait, with a successful previous-build wait
retained as a baseline. The owned ENiGMA search/NFO route remains a separate
normal-configuration regression on the staged server.

Current checks run through pinned Nix:

```sh
./tools/dev --command python3 standalone/check_line_callbacks_live.py
./tools/dev --command python3 standalone/check_line_controller_layout.py
./tools/dev --command python3 standalone/check_line_attributes_live.py
```

The optional paired characterization additionally needs the source-built
`7477a19` terminal, map and manifest under `build/line-controller-baseline/`,
then runs `standalone/check_line_controller_far.py`. Rebuild that revision in a
separate checkout through its own pinned toolchain; do not use a proprietary
PCPlus executable as the comparison input. The checker requires the recorded
previous maintained executable hash. Fresh source proofs run only the independent
current-image checks, with previous build outputs absent.

See [the validation record](validation/line-controller-far.json). Live ENiGMA
installation, physical modem/video timing, viewport/general emulations and the
remaining whole-application work stay open.
