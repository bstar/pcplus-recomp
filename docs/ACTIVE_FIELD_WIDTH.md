# Width changes with active fields

The explicit width transaction now accepts boolean wrapped-field, protected
checking and erase-protection modes in profiles 4 and 6. It preserves the mode
settings while reshaping field flags and stored attributes between 80 and 132
columns. The normal peer width request remains unbound. This extends the
[scroll-field checkpoint](SCROLL_FIELDS.md), rather than enabling every renderer
and application owner at the wider width.

The private reset bank previously stopped at its diagnostic repair service, and
the native geometry converter assumed 24 rows. The transaction now links the
recovered repair, coordinate conversion, default/previous attribute and byte
writer into its private code/data namespace. The ordinary/cold diagnostic still
retains its previous scope and exact executable identity.

A wrapper around the unchanged recovered geometry body replaces only the fixed
row conversion. It copies the retained 80 cells of each admitted row, working
backward when expanding and forward when contracting. Expansion clears added
flags and initializes their stored attributes. Contraction discards columns
80–131; a marker there does not remain attached to a different row. The native
geometry body continues to own width settings, shadow allocation/release and
clearing. Its second argument bypasses its fixed metadata-copy loops after the
bounded wrapper has performed that conversion.

The wrapper selects the canonical left pane and calls the actual native mode0
repair. Markers retain their stored field attribute; ordinary cells inherit it,
including across row boundaries and hidden columns. Marker pixels remain the
normal cleared background, matching mode0 semantics. Protected cells retain
their flags and receive the native protected-foreground treatment. Same-width
resets also repair the cleared display. With wrapping disabled, the planes still
reshape for checking/protection modes and video retains the normal clear.

The projection adds the protected display attribute as a read-only word. The
erase attribute has a separate byte projection and read-only validation: its
root byte is followed by an independent color-mode word and cannot be copied or
staged as a word without conflating those owners. The inspector verifies all 35
word fields and the real private repair entry. Root UART/parser/defaults/handles
remain outside commit. Native failure retains the existing root rollback and
status-row ownership.

## Validation

The [receipt](validation/active-field-width.json) binds the accepted source-only
rebuild in `build/reset-active-source-02`. No original executable or prebuilt
product is copied into its initially build-free tree.

Each transaction parent checks 420 width commits: seven active-mode combinations,
both profiles, both widths/directions, both wide panes, same-width resets and
1/5/24/25-row ownership with visible/hidden status. Independent expected planes
check retained/discarded/added columns, marker values, every metadata guard,
logical video and outside status/shadow canaries. There are 240 native repaint
cases and 240 parser DCH checks immediately after the commit, including protected
bounds and marker deletion. Two cases interrupt the real private repair with
512 binary bytes through the actual root UART ISR. Eight corrupted native results
verify rollback of root planes, shadow, video and BIOS cursor/shape, then retry.

The existing 1,344-case scrolling matrix, plain wide character/line editing,
width rollback/row models and ordinary repair/line/character policy checks repeat.
Four DOS8086 witnesses cover base/branded parents and visible/hidden status.
Their declared observer enables all three field modes before the real width
call, captures the exact new planes and pixels, then releases that initial
fixture before the existing character/field/scroll workflow. These are explicit
API tests, not peer width negotiation or physical-machine tests.

The observer records the active-width result separately from the later parser
screen. Its initial large capture accidentally exceeded a COM segment; the
collector now reuses its local sample storage and checks the executable size
before launch. Another fixture initially wrote a word to the byte erase
attribute; it now stages that byte without changing the adjacent color mode.
Earlier failed attempts remain in ignored build history. The final expected
background also retains the inherited attributes produced by the width repair;
the test stream redraws text after the width clear without issuing another full
clear. It cannot assume every untouched blank still has attribute07.

The first clean rebuild passed the display checks but failed the explicit
nested compiler launch with an ASPECT out-of-memory result. That rejected
attempt is retained at `build/reset-active-source-01`. Adding the private native
code had increased the branded module to 407,120 bytes.

The optional native-bank parent now shares the chooser and PROGRAM screen
backups. The chooser is synchronous and restores before a queued program may
launch. Explicit bidirectional guards reject chooser entry while PROGRAM is
pending/active, and program entry while the chooser holds its saved screen.
Reentrant chooser entry also refuses without changing its current ownership.
A width transaction refuses while the chooser owns the shared rollback buffer.
The editor retains its separate screen buffer because it nests inside the
chooser. Five named UI snapshots now occupy four physical 4,000-byte regions,
recovering 4,000 bytes without reducing any stack or language limit. The memory
inspector allows exactly that one alias pair in the optional overlay build;
ordinary independent UI owners remain unchanged.

Each parent repeats four owner refusals and three chooser/PROGRAM restore
cycles, covering child success, missing executable and insufficient-memory
errors. The real chooser open-error branch saves/restores its screen before the
actual PROGRAM scheduler reuses it. The width model adds a pre-mutation chooser
ownership refusal, bringing its refusal count to 63.

Five nested source compiler cases repeat with the smaller branded parent:
explicit, fallback, chained, rejected-source and chooser-to-program. The last
case opens the directory editor, cancels to the chooser, selects the entry,
connects and compiles source in one DOS process. Its directory check permits
only the selected record's call statistics to change.
The compiler and both runners are unchanged; prior grammar/stack/workspace
evidence is inherited only after checking exact compiler source and product
hashes. No new compiler corpus run is claimed.

- Ordinary executable: `20fa7d618af822acbd953b593cadfa660b97f1c43ff43c8c196dabb9f840f6a9`.
- Base transaction: `7fa71b5458a575164443baa823a41d4eccf70499e6ea2ca510af3c8ab1436ce3`.
- Branded transaction: `0e5fcb900ae87166cf802f4d6639881aea44af930b85f107914754ef136a36af`.

The branded allocated module is 403,168 bytes. Resident code has 298 bytes free;
the added recovery and wrapper execute in the private far bank. No permanent
plane or reduced compiler stack is introduced.

```sh
./tools/dev --command python3 standalone/prove_reset_fields_source.py --output build/UNIQUE_ACTIVE_WIDTH_PROOF --nested
./tools/dev --command python3 standalone/record_reset_fields.py --proof build/UNIQUE_ACTIVE_WIDTH_PROOF --output docs/validation/active-field-width.json
```

Tab-wrapped, vertical-check and reverse-wrapped configurations remain refused.
Partial-width wrapped scrolling, keyboard/UI/ASPECT/modal rendering composition
at 132 columns and width-changing BBS sessions remain open. The card package
has not been changed. Physical modem, reconnection and transfer acceptance are
still separate requirements.
