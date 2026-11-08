# ASPECT MZ load layout and startup accounting

The opt-in full GET build now pads its MZ header by whole paragraphs before
the load image. This changes the on-disk header layout while preserving every
load-image byte, relocation-table entry, initial register, minimum-extra-memory
value, feature and buffer capacity. The default reviewed build is unchanged.
The full application gate remains open.

## Loader accounting

The earlier audit calculated actual image length rounded to a paragraph plus
MINALLOC and the PSP. That is an arithmetic lower bound, not sufficient EXEC
admission accounting. The [published Microsoft DOS4 loader](https://github.com/microsoft/MS-DOS/blob/main/v4.0/src/DOS/EXEC.ASM)
computes the image extent from512-byte pages minus header paragraphs, then adds
the PSP and minimum extra memory. [DOSBox-X's loader](https://github.com/joncampbell123/dosbox-x/blob/master/src/dos/dos_execute.cpp)
uses the same page-based minimum and separately constructs an environment.
Actual environment sizes and allocation behavior must be measured in the tested
runtime; these source references do not establish the user's DOS6 behavior.

`standalone/mz_layout.py` now records both bounds. It validates the declared
DOS-only file length, header/relocation extents and overlay number. Header padding
keeps the file in its existing final512-byte page and leaves at most15 bytes
unused in that page. It updates only size/header fields and inserts zero header
bytes. Before/after load-image and relocation-table SHA256 must match, as must
the arithmetic lower bound. This is a layout transformation of newly generated
source-built executables, not original application input or code replacement.

For the GET child at that checkpoint:

| Property | Before | After |
| --- | ---: | ---: |
| Header bytes | 992 | 1440 |
| Load-image bytes | 120414 | 120414 |
| Arithmetic minimum including PSP | 139168 | 139168 |
| Page-based minimum including PSP | 139616 | 139168 |

The448-byte disk increase removes448 bytes of page-rounding admission overhead.
It does not reduce the program's static storage or guarantee dynamic allocations.
The load-image digest remains
`fc1a0b24d4da10edd58f1a4c6a1ef9969c81f80cb3fde79e8b68cacd53dfd3d8`.

## Execution evidence

[The receipt](validation/aspect-get-mz-layout.json) binds source and artifacts.
A source-authored five-byte MZ return0 program is tested in both header layouts,
with the same1KB minimum extra allocation. A DOS8086 COM probe reserves memory
to leave each of161 exact block sizes and executes both variants:322 EXEC calls.
Thresholds are2816 and2352 bytes, exactly464 bytes apart, matching header padding.
All lower attempts report DOS8, all admitted children return0, and every attempt
restores the allocator's original largest block. The observed thresholds include
that runtime's empty-environment overhead; they are not physical DOS thresholds.

The complete installed-feature-set parent plus capability22 still passes all six
actual GET cases, including the retained FOPEN stream, with the aligned child.
The isolated public-source replay also runs this calibration, seven CLI cases
and the113 host/218 DOS file API checks. Both full executables reproduce exactly.
The default reviewed interpreter remains byte-identical.

At that checkpoint the heavier keymap parent got past DOS EXEC, but the C runtime exits1 with
errno5 before any script/main work. The passive child probe shows no near heap,
no native error and zero runtime steps/allocations. Its allocation is8698
paragraphs (139168 bytes); the environment occupies73 paragraphs (1168 bytes)
for140 string bytes. Adding the16-byte environment MCB accounts for the entire
140352-byte pre-EXEC block. This is a failed startup gate, not a passed GET test.

The later [compiler executor](ASPECT_COMPILER_EXEC.md) funds startup and passes
the six larger-parent GET cases without reducing capacities. Its broader peak
memory/feature gates remain open.

Further work must verify actual dynamic memory while preserving features/capacities,
then verify the larger pair, full variable/stream co-residency and real DOS/physical
acceptance. The header fix alone does not close those gates. Repeated/EXECUTE GET,
WHEN actions, remaining field policies, both compilers and full parity remain open.
No selected package, installed files, DOSBox configuration, hardware or private
settings change in this checkpoint.

```sh
./tools/dev --command python standalone/test_mz_layout_dos.py \
  --output build/FRESH_CALIBRATION
```
