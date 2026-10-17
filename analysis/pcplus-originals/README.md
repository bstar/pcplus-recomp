# PCPlus binary analysis set

These are working copies from the mounted DOS card. The source card files were not modified.

| File | Origin | Identification |
| --- | --- | --- |
| `PCPLUS-main-2.01.EXE` | `MS-DOS_5/PCPLUS/PCPLUS.EXE` | ProComm Plus 2.01, DOS MZ, x86, 214,016 bytes |
| `PCPLUS-utils-2.01.EXE` | `MS-DOS_5/UTILS/PCPLUS/PCPLUS.EXE` | ProComm Plus 2.01, DOS MZ, x86, 214,016 bytes; distinct SHA-256 |
| `PCPLUS-1.1B.EXE` | `MS-DOS_5/UTILS/PROCOMM/PCPLUS.EXE` | ProComm Plus 1.1B, DOS MZ, x86, 185,392 bytes |
| `PCPLUS-main.HLP` | `MS-DOS_5/PCPLUS/PCPLUS.HLP` | Help file accompanying the main install |
| `PCPLUS-2.01-READ.ME` | `MS-DOS_5/UTILS/PCPLUS/READ.ME` | Version/readme from the utility copy |

SHA-256 values are listed in `SHA256SUMS` (for the five copied source artifacts).

## REA status

REA opened `PCPLUS-main-2.01.EXE` as `dos-mz`, x86, SHA-256 `6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904`.

The initial connected MCP server lacked provider environment variables. A later filesystem inspection found an existing user-local Ghidra/Java installation, so the earlier statement that the software was absent was incorrect.

The current workflow uses a Nix-managed REA 6.5.0 stdio MCP server with Ghidra 12.1.2 and JDK 21. REA verified the original MZ import and exported assembly/pseudocode for 515 automatically discovered resident functions. These exports are in `../pcplus-main`; 48 pseudocode files contain a bad-instruction warning and must not be treated as recovered buildable source. The 155,952 appended bytes were not included in that resident-image decompilation.

A target-specific parser based on the analyzed PLINK86 loader subsequently extracted 32 overlays and validated all file boundaries and 502 entry trampolines. Overlay 32 is startup data. The 31 code overlays are analyzed in explicitly synthetic parent/data contexts, with provenance and limitations in `../pcplus-overlay-images/manifest.json`. Those analysis images must never be run or deployed.

The two 2.01 executable copies differ only at ten contiguous byte positions within startup data overlay 32; their resident bytes and 31 code overlays are identical. No code patch distinguishes the copies.

The initial four-routine, 81-byte reconstruction is preserved in `../../reconstruction/build/verification.json`. The current build additionally recovers the complete 1,099-byte UART block and the 46-byte receive timeout, totaling 1,145 unique source bytes. See `../../reconstruction/uart` and `../../reconstruction/dist/tech-net-candidate/manifest.json`. Full DOS emulation tests now exercise serial queries and keyboard input; see `../PCPLUS-EVALUATION.md`. The complete source project remains unrecovered.

The executable is a proprietary compiled DOS program. A decompiler can produce assembly and approximate pseudocode, not the original source project or build system. Rebuilding the original product would require recovering substantial missing source-level structure and toolchain details. Both targeted assembly reconstruction and a separate implementation remain options. Preserve these originals while evaluating either approach.
