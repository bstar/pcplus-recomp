# Native PCSETUP invocation

Original PCPlus2.01 launches a separate setup child from overlay3:D4D0..D5F7.
This ledger reuses retained REA assembly and SHA-verified original resources;
it does not execute PCPlus, PCSETUP, an analysis carrier, or a private PRM/DIR
file. No new REA session was required or opened. Normal source builds do not
read these ignored analyst artifacts. Original EXE SHA256:
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.

## Native entry, executable and command string

The recovered keyboard dispatch table maps Alt-S scan1Fh to residentBA63. The
retained overlay trampoline manifest resolves BA63 to **overlay3:D4D0**. This
is the original setup command; the maintained terminal's Alt-S upload shortcut
is a separate interface decision, not proof of original shortcut compatibility.

The parent constructs:

```
<current PRM path> PCPLUS <unsigned decimal packed far address>
```

At D517 it copies the current string at DS5EC0, then concatenates literal
` PCPLUS ` from DS5EAA and the decimal number. DS5EC0 is initially
`PCPLUS.PRM`, **but is mutable resolved configuration-path storage**, not a
constant basename or application directory. Locator3:D647 copies resolver
results there, expands a current-directory path and can add a drive prefix.
The native parent adds no quoting/escaping or size bound to these strcpy/strcat
operations. Its command buffer occupies60 bytes before the adjacent16-byte
number buffer in the local frame; arbitrary long paths are not a safe new ABI.

The executable resource is `PCSETUP.EXE` at DS5EB3. Resident353D resolves it
separately: try the requested name in the current directory, otherwise use the
configured environment-name pointer DS324C (initially`PCPLUS`) as a directory,
append a backslash if needed and append the filename. This does not guarantee
PCSETUP lives beside the current PRM, nor establish a modern PATH-search policy.
The resolver's existing unchecked buffer/empty-environment/probe behavior is
recorded in RAW_MONITOR_NATIVE.md and its recovered module.

### Address encoding and arguments

76B0 returns DS in AX. D4D0 forms a two-word value with low word1B84h and high
wordDS, then calls unsigned conversion89FA with radix10. Its A5E8 core handles
a32-bit high/low value; the89FA entry sets its signed-format selector to0.
Therefore:

```
packed = (DS << 16) | 0x1b84
number = unsigned_decimal(packed)
```

This is a packed **segment:offset**, not the physical address`DS*16+1B84h`.
For synthetic DS1234h, the decimal argument is305404804 (12341B84h); its physical
address would instead be13EC4h. That example uses no original/private memory.
The1B84h offset is the start of the proved1264-byte parent PRM memory image.
No image length/version/checksum is included in this command string.

For a path without whitespace the string has three whitespace-separated parts:
PRM path, literal`PCPLUS`, and number. The literal is an observed parent/child
marker; the absent child has not established how it parses or validates it.
Passing the pointer and comparing changed parent memory afterward strongly
supports a shared-memory setup mode. It does **not** prove the child's actual
write rules, bounds, save/exit semantics or private protocol compatibility.

D4D0 calls the existing433D executor with five arguments:

| Argument | Value |
| --- | --- |
|Program|Resolved`PCSETUP.EXE` near filename pointer|
|Command string|Constructed path/marker/packed-pointer string|
|Command-processor flag|0: direct spawn, noCOMSPEC or`/c`|
|Post-child key-wait flag|0: no optional local-key pause|
|Executor screen-save flag|0: wrapper's optional screen/vector branch skipped|

The direct spawn uses synchronous DOS EXEC; key-wait0 does not mean an
asynchronous child. The parent resumes after child termination. D4D0 ignores
433D's returned AX status and continues its restoration/change-detection path.

Assembly order matters: three zero flags and the command pointer are pushed
before resolving the filename through353D, then its result is pushed and433D
called, followed by caller cleanup10. Some retained pseudocode incorrectly
assigns those already-pushed values as extra353D arguments and shows433D with
one argument. The actual stack layout, recovered executor and cleanup prove
the five-argument call; do not reproduce that decompiler artifact.

## Parent memory, screen and serial lifecycle

Before launching, D4D0 snapshots selected words:1D60, normal attribute1D32,
terminalID1D18,1D64, status/UI flag1D46 and cursor-related setting1D48.
It separately calls6BBE to allocate/save the video image, retaining returned
far pointerDX:AX. The parent PRM image is not copied into that screen allocation
or serialized into the command tail; the tail contains its original parent
DS:1B84 address. No full PRM rollback image or transaction is created here.

The existing433D executor checks its reentry guard333C, saves cursor/display
state and invokes mouse services. Because D4D0 passes screen-save0, the
executor's conditional6BBE/758A/40C9 pre-child branch and7508/40DF post-child
branch are skipped. D4D0 supplies its own outer screen snapshot instead.
433D still invokes **03A7 after the direct child returns**, before its display
restoration.03A7 refreshes the selected communication port/driver and calls
recovered UART configuration paths0366/033E plus interrupt/driver helpers.

No explicit pre-child UART disable, RX/TX drain, file-handle close, snapshot of
all hardware registers or serial ownership token is established by this setup
caller/inspected executor path. It would be inaccurate to describe it as the
maintained terminal's checked suspend/EXEC/resume protocol. Ordinary DOS process
memory and CRT heap handling are delegated to the recovered spawn chain; this
caller alone does not prove safe memory shrinking or child handle inheritance.
The original child may cooperate with the resident parent, but that cannot be
asserted without its binary. No continuous BBS traffic/serial preservation claim
follows from merely seeing a setup spawn.

After433D returns, D4D0 calls4870 on its saved screen far pointer;4870 restores
via7558 and frees it, or invokes488F for a null pointer. This is not a checked
optional-null snapshot contract. It then calls40F6, whose verified original
instructions perform these copies and reread BIOS display state through6D1A:

| Configuration word | Runtime destination |
| --- | --- |
|2068,206A|7A50,7A52|
|1D1C software flow|3354|
|1D1E hardware flow|3356|
|1D22 scroll setting|9016|
|1D44|7A92|
|1D3C|7A94|

40F6 has no independent retained REA export in this inventory; its bytes were
decoded read-only from verified original resident40F6..4123. Neutral unnamed
fields remain neutral rather than invented setup labels.

The remainder compares live parent values with its selected snapshots:

- If1D64 changed, call3:DEF8: reset its underlying mode, set receive mask8E22
  toFFh, call35D7 for value1 or change mask to7Fh for value2.
- If1D46 changed, normalize it from the current zero/nonzero test and call46BA
  to refresh status/terminal geometry. The assembly stores1 for a previous
  current value0 and0 otherwise before that helper; this is an observed toggle
  preparation, not a generic validated boolean assignment.
- If terminalID1D18 or normal attribute1D32 changed, or current3254 differs from
  setting1D2E, call full reset20A4(1).
- If1D60 changed, call78A2 with0 when it is nonzero orFFFFh when it is zero.
  The verified78A2 helper issues BIOS INT16h withAX0305h, usingBX0000h or010Bh;
  no new timing/rate unit is inferred from that toggle.
- Select40DF/40C9 according to1D2C; these conditionally call5C20 with1/0, under
  existing runtime gates. Complete device semantics remain outside this ledger.
- If1D48 changed, clear cursor-flags333E bit0 for a nonzero value or set it for0.

This is selective application of changed shared state. It does not reload the
PRM file in D4D0, validate every field, recover the child's UI or establish an
atomic save. Reapplication runs even when spawning failed, because the returned
status is ignored by this caller.

## Standalone support and authorized inventory

The authorized inventory `analysis/pcplus-originals/README.md` and SHA256SUMS,
confirmed by a read-only listing of that directory, contain three PCPLUS EXEs,
a help file and the2.01 readme. **PCSETUP.EXE is absent.** No unapproved drive
search or original binary copy was performed to fill that gap.

The original `PCPLUS-2.01-READ.ME` does establish a standalone setup workflow:
its low-memory section (lines40..49) says the auxiliary tools, including
PCSETUP, must be started separately at the DOS command line when there is too
little memory to launch them from PCPlus. It discusses the parent's192K minimum
and restrictions below295K. Readme SHA256:
`c7b2f81fdcfab8ec0eb2f27c6efa60b8b2812912d37537ff233d87c4f793226b`.
This is historical usage evidence, not an independently measured memory limit.
It does **not** give the exact standalone argument syntax, default file search,
help switches, save behavior or a requirement to supply the parent's marker
and packed pointer. No standalone command is asserted as tested here.

A source-owned staged PRM editor can expose independently validated fields
through its own UI/CLI without accepting this legacy shared-memory protocol.
Its checks, staging and serial ownership must be documented as maintained
behavior; the absent PCSETUP does not authorize claiming original interface
compatibility, complete setup reconstruction or full-application completion.

## Evidence ledger

| Retained assembly | EvidenceID |
| --- | --- |
|3:D4D0 setup caller|`ev_dd1d40e9cbad7523a355eeea9364e2483b3b2d79e4a051b4911a7905b8eda450`|
|3:D647 current PRM path|`ev_0b7e0098ca824727703a9c43e5df54c85c2b94a7564b9ae9830451d095e2ce34`|
|76B0 DS getter|`ev_dbc4fc5446117d676b8d36125be1c028d30f8561943520620c3e18e0fd063d32`|
|89FA unsigned decimal entry|`ev_1af0ecd2c05917fe2dfd8c9ff440a7c8c597c00a2fde9c493d2d3a45f625d24b`|
|A5E8 high/low formatter|`ev_cd0f272c3313e69c350752076d84da5068ba032605ba48b7f9b56a521630cf10`|
|353D executable resolver|`ev_1cd43dbde8697560fddafd763fd3ab56971d91bd6badd8b88553d8e1cc1d6417`|
|433D executor|`ev_a5c189826e129ae1c8a59c464a4fb7be362d61aaeadcb2317f2c1b78b19768ad`|
|03A7 post-child communication refresh|`ev_7d74b6645819435577993debdd67e07b05b44257d47fddb9007e405b4727836f`|
|6BBE screen allocation/save|`ev_d12ff3b06d0e6d51cebfd612a11c0fd10c5c7026cb8b350a0cfca83e4f49ebf1`|
|4870 screen restore/free|`ev_96965061d48282dbba8fc0b1083bac343af45d1c86376b2955f2dcfc245bded3`|
|3:DEF8 receive-mask change|`ev_2e0d886530aabdddeddfbcf0f3fbb56e0f0f87dde7cc5be55f581c581ade257e`|

These exports live under ignored`analysis/pcplus-main/functions/` and
`analysis/pcplus-overlay-anchored-03/functions/`. Ignored
`analysis/setup-native/provenance.json` binds export hashes, original identity
and the observed authorized-file inventory. Original short resources were
checked at DS5EC0/5EAA/5EB3 in initialized data (file25950h+DS offset).
No new session or runtime test was needed; no session was left open.
