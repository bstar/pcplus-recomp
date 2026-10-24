# Alternate field-cell output

The former `render_font_output` boundary is now backed by recovered native
field-cell output. It marks metadata and draws a character with the appropriate
attribute; it does not download or select fonts. The old symbol name retains
the original two-word, callee-cleaned ABI.

## Native evidence

Original executable SHA256: `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Explicit analyst recovery verifies these original ranges. Ordinary application
builds use source plus the recorded hashes and never read the original.

* `f412..f45b`: 74 bytes, `4238d1712605155eae22e288bec765b7e7d3bf4cdac8a71ca405aaa738ea0c16`.
* `f45c..f47a`: 31 bytes, `93a86aee72ff230cce2f88dafc7a3d39f66e77a6a811c6d7053a229ed37d3826`.
* `6fa0..6fce`: 47 bytes, `57301f1aaf386d6b48cd18376a06363cf0c6cd5f382266d39123fb4d6040212a`.

REA output dossier: `ev_9ba37655f5393246fd69aadffb2c665e1de309fcf5ff01eb6ffe48c54874be63`.
REA attribute dossier: `ev_00a413edb91c97be838a8ba9d074f7b89ef3dd6d4aa7cb4e32cbcc29c5847dad`.
These use the static-only overlay13 analysis image; copied helper bytes are
independently checked against the original. The output unit includes one
padding NOP omitted from Ghidra's function-body ranges. Synthetic analysis
images are never executed or deployed.

Without native output translation, the helper writes metadata byte1 and forms
its display attribute as `(old_attribute & 0xf8) | (preset & 7)`. Thus background,
blink and the existing intensity bit remain from the cell. With translation
enabled, it writes metadata byte3 and uses the preceding field-value attribute.
The low character byte is written unchanged in either helper branch.

## Application ownership

A checked far adapter requires bounded current geometry, matching logical
offset, both owned metadata planes, DS=SS and valid execution flags. Real native
output, attribute selection, previous-value lookup and text writing execute
behind it. The reader temporarily switches DS to video memory after extracting
its stack argument, then restores DS before returning. This transient does not
perform DS-relative stack accesses.

The high-level renderer applies the native output map and byte mask before
calling the helper. Its256-byte table is a source-owned identity map by default;
configured test maps are fixtures, not recovered factory tables. Admission
requires its canonical pointer and bounded resource. Arbitrary byte masks
cannot index beyond that full table. Output mapping remains separate from
UART input translation and never feeds mapped glyph bytes back into the parser.

Current-profile RIS now captures the output enable flag, map pointer and byte
mask along with the existing state. The table itself is an immutable application
resource, so reset restores selection without allocating another table copy.

The ASPECT far-code segment now has an explicit group. This prevents automatic
DOS linker packing from sharing its CS with the splash segment when resident
code approaches64KiB; the MZ/map gate still requires a distinct CS and offset0.

## Conventional-memory correction

The first clean proof failed in the DOS source-compilation case. A shorter
host path failed identically. Passive exit observations showed the nested
compiler either starting and returning1 or failing to start when the observer
grew; the ordinary bare compiler cases still passed. No compiler diagnostic
text was recovered from the temporary log, so the precise first failed
allocation is not established.

The directory editor now shares its4000-byte backup with the serviced viewer's
live-screen backup in the optional overlay parent. Both entry directions check
the other owner's state; the chooser and PROGRAM checks also prevent nested
ownership. The editor clears its owner only after restoring, including accept
and cancellation. Its backup remains distinct from the enclosing chooser's
backup. Default non-overlay builds retain independent frames.

Together with the earlier chooser/PROGRAM sharing, this reduces retained UI
storage from20000 to12000 bytes. The compiler's24576-byte stack, VM's8192-byte
stack and language/workspace limits remain unchanged. A DOS source-compilation
pilot with mapped output and the script window open now passes with an exact
ASX match and compiler exit0. The linked ownership check covers12 refusals,
three PROGRAM returns, editor accept/cancel and viewer screen restoration.

Both DOS observers also record child exits, DS/SS and the interpreter's compiler
call/exit/errno words, using offsets from the runner's map. They observe only
while the parent session is active. Source cases require two child exits and
one successful compiler call; precompiled cases require one child exit and no
compiler call. Collection utilities cannot overwrite these observations after
the parent exits. Compact source cases still make no full-plane snapshot claim.

## Verification

The [sealed receipt](validation/alternate-output.json) binds864 source files
and1380 artifacts. An initially build-free source tree reproduces four parent
products, both interpreters, the unchanged compiler and the unchanged CSI
diagnostic exactly. No original executable, private configuration, disk image
or REA database is an application build input.

Each linked-model trial checks12,288 cell cases covering every byte and palette
value across both profiles, widths and panes, with1/5/24/25 rows. It also checks
96 high-level renderer streams with output mapping/masks, direct output and
field/checking/protection combinations. All other pixels, field values, cursor
caches and hidden shadow bytes must remain within their owners.

Six real foreground UART-IRQ injections occur while DS points to video memory.
The native reader resumes correctly and all512 queued bytes survive. Nine bad
states refuse before mutation. Three RIS cases restore mapping selection, and
12 active width transitions preserve the map and continue drawing correctly.

All55 DOS workflows pass:18 new output cases,16 protected-erase cases,
eight ordinary wide-ASPECT cases, eight field/local-view cases and five
ordinary nested-compilation workflows. The new cases cover status visible or
hidden, script window closed or open, precompiled or DOS-compiled source and
ordinary or mapped output; two additional cases exercise mask127. The policy
diagnostic passes58,906 DOS checks and42 independent CPU probes.

Both transaction parents repeat the earlier width/field/scroll/reset/viewer,
ownership and IRQ gates. The original compiler and both interpreters remain
byte-identical to the preceding checkpoint; compiler grammar/stack evidence is
bound through the prior receipt. The new DOS compilation cases run afresh.

For the basic optional parent and linked output check:

```sh
./tools/dev --command python3 standalone/build_terminal.py --native-reset-bank --native-reset-transaction
./tools/dev --command python3 standalone/check_alternate_output_live.py --terminal build/terminal-native-bank-transaction/TERMINAL.EXE
```

The complete proof is `build/alternate-output-source-02`; the recorder checks
its source/artifact custody, exact products and full case matrix. The earlier
failed proof and diagnostic pilots remain in ignored build storage.

The later [peer-width checkpoint](PEER_WIDTH.md) supplies that experimental
binding. Other unsupported emulations and application families, physical
modem/BBS interoperability and card deployment remain separate.
The receipt explicitly retains `accepted_for_deployment: false`.
