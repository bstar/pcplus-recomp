# Startup configuration for the live terminal

The live importer stages and validates a **known subset** of the original
1,264-byte PRM memory image, then initialize owned runtime state explicitly. It
does not memcpy the legacy image into the reconstructed data segment. This documents the
partial configuration import and its original-code evidence; directory UI, dialing,
scripts, alternate emulations and the rest of PCPlus remain application work.

All observations below come from the SHA-verified program and retained REA
exports. This code/schema audit used original instructions and synthetic configuration
fixtures; it did not read installed or private PRM contents. A matching length is not a format
signature. The importer should require an explicit compatible-file option and
reject a malformed or unsupported selected subset before accessing UART hardware.

## Exact startup sequence established from code

Resident helper `40f6..4123`, omitted from the retained function export inventory,
is visible directly in the verified original instructions. Its slice
`4102..4113` performs:

```text
DS1d1c → DS3354  (configured software flow → live UART flag)
DS1d1e → DS3356  (configured hardware flow → live UART flag)
DS1d22 → DS9016  (configured scrolling → saved reset default)
```

These are separate words. Neither flow flag is an enum selecting the other.
Resident `04c8` also restores configured software flow to the live flag when
leaving its temporary line-configuration mode. Overlay19 `ea2c` copies configured
hardware flow to the live flag after changing it. This corroborates the distinction
between PRM settings and active UART state.

Resident `20a4` is the profile/reset service. Its argument controls whether to run
full profile initialization: zero skips directly to `23a8`, whereas nonzero runs
profile derivation and state reset. Therefore calling `20a4(0)` is insufficient
to apply a newly selected terminal profile. The full routine also calls original
keymap/file, geometry, display and UI services; the prototype must initialize its
owned state instead of pretending those unrecovered services have executed.

A safe maintained ordering is: read into an opaque staging image; validate the
selected known subset and CLI policy; construct a final immutable settings plan;
commit serial options and terminal settings; derive profile flags; reset parser,
cursor, saved state and metadata planes; derive current attributes from configured
normal; initialize video/tabs; check BIOS port presence; acquire UART/IRQ resources.
Keep all validation before resource acquisition. CLI overrides should act on whole
categories, as documented by the application, with no silent fallback after a
malformed requested file. Whether to validate overridden PRM values as well is
an explicit product policy; never let invalid raw table indexes reach assembly.

## Import allowlist and validation policy

Offsets below are hexadecimal within the PRM image, whose original DS base is
`1b84`. Ranges describe the proposed maintained interface. They are distinguished
from original observations where necessary.

| PRM offset | Original DS | Value | Recommended live import rule |
|---|---|---|---|
|0000|1b84|Port index|Original UI/storage has indices 0..7. Current host supports COM1..4, so accept 0..3 and reject 4..7 as unsupported. Convert to CLI COM number by adding 1.|
|0002|1b86|Baud index|Accept 0..8 and map to300,1200,2400,4800,9600,19200,38400,57600,115200; never use as an unvalidated pointer-table index.|
|0004|1b88|Parity|Accept 0..4: NONE,ODD,EVEN,MARK,SPACE.|
|0006|1b8a|Stop bits|Accept 1 or 2; original line-control helper treats2 specially.|
|0008|1b8c|Data bits|Accept 7 or 8, matching recovered selection UI; do not rely on the assembly fallback for arbitrary values.|
|0174+2*i|1cf8+2*i|UART I/O base table|For selected COM1..4 require standard base03f8,02f8,03e8,02e8 respectively, then require agreement with the BIOS BDA entry before UART IO. Do not apply arbitrary addresses from a memory image.|
|0184+2*i|1d08+2*i|IRQ number table|For selected COM1..4 require4,3,4,3 respectively. This is the prototype's standard-port policy, not a claim that original custom ports cannot exist.|
|0194|1d18|Terminal ID|Accept 4 VT220 or 6 ANSI; reject other profiles as unsupported. This does not assert complete implementation of either profile.|
|0198|1d1c|Software flow|Accept exactly 0 or 1; copy to live DS3354 alias.|
|019a|1d1e|Hardware flow|Accept exactly 0 or 1; copy to live DS3356 alias.|
|019c|1d20|Autowrap|Accept exactly 0 or 1 and initialize the owned wrap state. The full reset does not overwrite this word.|
|019e|1d22|Scrolling|Accept exactly 0 or 1; use as initial scrolling and as its saved reset default.|
|01ae,01b0,01b2,01b4,01b6|1d32..1d3a|Normal,bold,additional preset,reverse,underline attributes|Accept 0..255, reject nonzero high bytes as unsupported word flags. This bounded policy matches text-cell attribute storage, without claiming all original setup paths are recovered.|

The selected IRQ is used by original `0366` as `vector=irq+8`. Recovered UART
mask/unmask code `add6/ae12` indexes eight master-PIC mask words and writes port21.
Thus 0..7 is only an indexing bound, **not** a safe general IRQ policy. The current
source-owned mask table actively supports IRQ 3/4 only; other entries are inert.
Reject arbitrary IRQ0/1/2/5/6/7/8+ in this prototype rather than hijacking another
service or claiming slave-PIC support. Never import an interrupt vector, saved
handler, port-register address or PIC mask directly from disk.

Original flow flags can both be 1. The original code copies both independently,
and its paths test them individually. If the maintained option layer supports
only NONE/SOFT/HARD, either add an explicit supported BOTH configuration or reject
1/1 as unsupported. Silently choosing one loses represented behavior. Zero/zero
means NONE; one/zero SOFT; zero/one HARD. Physical modem handshake correctness is
separate from accepting those flags.

Only the selected port's table pair is applied. Unused entries remain opaque;
their storage must not be interpreted as active hardware. Do not describe a raw
whole-image decoder as semantic validation of every original setting.

## Profile-derived flags: actual values

`20c0..2283` derives these values from terminal ID, not PRM fields. Original DS
addresses are authoritative where module names are potentially misleading.

| Original DS | VT220 ID4 | ANSI ID6 | Integration alias or observation |
|---|---:|---:|---|
|d122|1|1|`attributes_color_mode`, also `screen_doublewidth_enabled`; shared storage|
|8fe8|1|1|`terminal_dec_keys`, also `terminal_input_mode_8fe8`; profile capability gate, not current application-arrow mode|
|8ff6|0|1|Existing alias `attributes_monochrome` is misleading: this is the ANSI/IBM-PC profile flag, **not monochrome monitor detection**|
|8ff8,9004,cd36,9038|0|0|Other emulation-family flags|
|900c|0|0|`screen_cursor_wrap`|
|9018|0|0|`screen_vertical_attribute_check`|
|9020|0|0|`terminal_newline_mode_9020`|
|9026|0|0|`terminal_control_mode_9026`|
|9032,903e,9048|0|0|Other emulation gates|
|904c|0|0|`csi_report_private_prefix` / `scroll_skip_attribute_scan` shared word|
|9056|0|0|Other emulation gate|
|9058|1|1|Derived as900c==0 &&9032==0 &&9020==0|

Do not copy any of these flags from the PRM image or infer a monitor type from
8ff6. When adding modules, all aliases for a given original DS address must share
one backing word. Their names do not authorize independent state.

## Clean runtime and attribute state

Full reset `2287..2304` clears words 3350,334e,397e,cd84,ceb0,ce0e,399a,cdf0,3260,
cd2c,cdec,3732,3736,3734,3730,372e,372c,3340,ce04,cdd2,cde8,cde0,3982. It clears
byte 321c (reverse latch), byte cc9e and 72 bytes beginning cc4a. It sets 3980,cdfc,
cd24 to 1. In particular, cd24 is the saved autowrap value; the live 1d20 remains
unchanged. It copies 9016 to 1d22 and d004, normal 1d32 to current 1f70 and saved cdd4,
and the normal low byte to d008. Later it sets bottom margins cee4/ce3a from 334a,
initializes keymap arrows with `[`, cursor shape and default tabs, and clears/fills
owned display metadata. These steps depend on valid geometry and backing buffers.

One exact distinction matters: this reset slice clears blink 397e and reverse 321c
but **does not clear bold 397c**. Fresh-process initial data has bold 0. A maintained
clean startup should explicitly initialize bold, blink and reverse to 0; call this
clean initialization rather than claiming the original profile-reset service did
all three. Parser parameters/pending input, origin state, wrap pending, current
and saved cursor positions, translation/graphics state and owned buffers also
need clean source-owned initialization. None comes from unvalidated PRM bytes.

Do not import PRM offset03ec (DS1f70), even though the opaque original save image
contains it. It is the live current attribute, mutated by SGR. Startup derives it
from the configured normal attribute. Other unrecognized PRM words, pointers,
UI state and saved/live values are outside the allowlist and must remain unapplied.
This is a semantic boundary in the maintained importer, not a claim that the
original whole-image reader filtered them.

There are two different attribute operations:

- Profile initialization copies configured normal directly into current. With
  normal 001e, initial current is 001e for both ID4 and ID6.
- SGR0 helper `1c8c` calls reset`24da`, clears bold/blink/reverse and then applies
  the 8ff6 override. With normal 001e, SGR0 produces 001e for VT220 but 0007 for ANSI.

Therefore using SGR0 to initialize imported colors would change original startup
behavior for ANSI. Preserve the profile-specific recovered behavior; a later color
reset from the remote BBS may deliberately change it. Underline and reverse also
have 8ff6 branches, while bold's nibble path is selected by d122. These flags are
not interchangeable.

## Actionable synthetic vectors

Use a synthetic 1,264-byte image, set only proved fields and fill the rest with a
sentinel. Assert ignored bytes never enter owned state. This is a test fixture,
not a complete original startup PRM.

| Vector | Expected outcome before UART acquisition |
|---|---|
|COM2 index1,base02f8,IRQ3,baud index5,parity0,data8,stop1,soft0,hard1,ID6,wrap1,scroll1,normal 001e,current00ff|Accept;19200/8N1/HARD,profile8ff6=1,initial current001e; later SGR0 yields0007.|
|Same,ID4|Accept;8ff6=0,initial current001e; later SGR0 keeps001e.|
|wrap0,scroll0|Accept; preserve disabled wrap and scrolling; saved reset scroll also0.|
|Port index4,baud index9,parity5,data6,stop0/3|Reject each independently; no UART IO/vector installation.|
|ID0/5/7/ffff|Reject unsupported selected profile.|
|Selected base0000 or03f8 forCOM2; selected IRQ0/2/5/8|Reject unsupported selected port mapping.|
|soft2 orhardffff; wrap2;scroll2;any attribute0100|Reject each out-of-subset value.|
|soft1 andhard1|Explicit BOTH support or unsupported rejection; never silently reduce.|
|currentffff,unknown wordsffff with otherwise valid allowlist|Current derives from normal and unknown words stay unapplied; rejection is not required merely because ignored bytes are nonzero.|
|Unsupported CLI token,failed/short/long PRM read or invalid selected subset|Failure leaves runtime staging uncommitted and hardware untouched; no repair rewrite.|

## Evidence and reproducible original slice replay

The verified EXE SHA256 is
`6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.
Resident file offsets add 1200 hex. Startup data is overlay32, file offset 153936.
Retained REA function evidence:

| Original function | Evidence ID |
|---|---|
|20a4 profile/reset|`ev_e5cd926306b36dfee8a944f6362792f774404d81eeb8a28f433854a8b6938c54`|
|1c8c normal SGR|`ev_278d71e87b070fe171240ab40bdfc7bb22e422a9494aa5a486b09a5cbaea5888`|
|04c8 temporary line settings|`ev_eff01dde627eed6d260f3b7e543a264ca98b853ac21dcee235c418bb2de1a35b`|
|0366 port addresses/vector|`ev_31c70c725487dc7c5de3c8fb6f1200110dd014d9da92ca651065e54613bdf24e`|

The tiny 40f6 helper was directly decoded from the verified original; it is not
misrepresented as a retained function-level REA export. Its flow/scroll slice
is independently executed by the optional analyst replay:

```sh
./tools/dev --command python3 src/config/check_startup_original.py \
  analysis/pcplus-originals/PCPLUS-main-2.01.EXE
```

The replay verifies the full EXE hash, runs actual 20c0..2283 profile derivation for
IDs 4/6, all eight boolean flow/scroll copy combinations at 4102..4113, reset current/
scroll/latch behavior at 2287..2304, and actual 1c8c/24da SGR0 behavior. It stops before
unexecuted keymap/UI/file services rather than substituting no-op implementations.
Its output is `build/config-analysis/startup-replay.json`. These are controlled
instruction-slice observations, not an assertion that the original application
boot sequence or a full reconstructed application has been run.

## Implemented maintained boundary

`src/config/terminal_import.c` validates the allowlist into a staged40-byte plan;
`src/terminal/configuration.asm` applies it before BIOS serial checks and UART
acquisition. `@FILE.PRM` selects a read-only file explicitly; serial CLI categories
override after whole-allowlist validation. Both flow flags enabled are accepted.
The live scroll flag is initialized; the original full reset service and its
saved-scroll aliases remain unreconstructed. Imported normal initializes current,
saved and erase attributes directly, without invoking SGR0.

The near C boundary uses unsigned16-bit statuses, assembly-owned DS=SS startup,
explicit DOS-library linking and an8-KiB stack. It does not establish general CRT
initialization. Default builds read no original program or private configuration.

`./tools/build test-terminal` includes119 CPU import cases and15 DOS filesystem/
UART cases. Optional `src/config/check_startup_original.py` separately replays
SHA-verified original startup fragments and is never a default build input.

With `/D:target`, the assembly loader instead invokes `terminal_startup_read`,
which reads once and stages both serial/display and modem plans before committing
either. An invalid modem subset does not partially commit serial settings.
The [connection controller](CONNECTION.md) documents the bounded live policy;
complete legacy startup and the original modal dial-attempt remain unfinished.

The40-byte plan retains TEXT pause byte (PRM01e2) and calibrated delay units
(PRM01e4) at offsets36/38. Live TEXT uses the pause byte; ordinary-byte pacing
is maintained fast policy, not an interpretation of calibrated units as milliseconds.
