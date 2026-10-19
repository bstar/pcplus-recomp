# Actual DOS parent status service

The admitted ASPECT child now requests STATUS through ASIOv4 capability version
2. SET WHENCASE invokes that service with BX=FFFF, selecting the parent's duplex
value for the status snapshot. STATUS requires the live child UART lease;
closed-phase requests return typed14 before native status drawing or DCD input.
Post-close diagnostic EMIT has a separate lifetime. The four cases below exercise
the live phase; closed-phase rejection is a separate linked/API proof. The parent draws through the recovered 515-byte
status body, 175-byte helpers, bounded far formatter and actual text/window
services described in [STATUS_RENDERER.md](STATUS_RENDERER.md). No child string
or formatter pointer is passed to this operation.

`standalone/test_aspect_status_dos.py` executes the actual product pair and a
passive source-owned observer. The frozen product identities are:

| Product | SHA-256 |
| --- | --- |
| TERMINAL.EXE | `e9c8a731df6af6bc0f2afd25fec1363ce6607dc2be284f1ab911e41d1217ecc5` |
| ASPECT.EXE | `65b3e08de86f436e4216ec2238a20d42b667ef21e1ec2d49a5a745c50daa935a` |

The report `build/aspect-status-dos/final-03-phase/checks.json` passes **four cases and
152 checks**, with SHA-256
`3f11546fe724d6901633205dd60689b8b6464fc4e950ddcdb6d148d4ebe4f8d5`.
The executed checker has SHA-256
`70c577b42481f1f1832b0384c122ccae3f4e9da491bdf1f120b2949024f5bbdc`.

The cases exercise WHENCASE ON, OFF and repeated changes with ANSI, and ON with
VT220. Each directory-bound script first consumes the initial banner and real
DA/CPR queries with WAITFOR, requests status through SET WHENCASE, and pauses
before transmitting its selected synthetic password. A later query checks that
the parent cursor remains coherent. The observer collects 38 timer samples per
case while the actual child is in PAUSE; these are observations, not a count of
STATUS invocations.

The observer derives child addresses from the linked map, qualifies the actual
child PSP signature and DS=SS, and requires current opcode88 before sampling.
It copies 162 video bytes at B800:3840, including the native 81st cell beyond the
visible row. Exact expectations cover all 81 characters, fourteen label
attributes1E, remaining attributes1F and the extra blank cell with attribute1F.
The row contains LOGIN.ASX, the actual ANSI or VT220 profile, FDX, 38400 N81,
LOG CLOSED and PRINT OFF. Parent duplex/profile/UI attribute and the child's
WHENCASE value are sampled independently. Both parent duplex and profile are
retained.

The existing renderer harness also checks native query replies, adopted screen
and history, unchanged parent JFT and capture/printer owners, directory
accounting, unchanged inputs/products, ordinary parent keyboard resumption and
restored hardware state. Expectations are serialized before DOS execution. No
query reply, text renderer or status formatter is replaced by the test peer.

Two carrier labels, ON-LINE and OFF-LINE, are declared before execution; all four
runs observed ON-LINE. The passive observer does not read the UART MSR, whose
read would clear delta bits and alter product behavior. This proof therefore
does not independently correlate the displayed label with a physical DCD level.
Actual carrier instructions and modeled carrier inputs belong to separate
component evidence. The modem peer and UART/BIOS here are emulated.

The failed first attempt remains at `build/aspect-status-dos/actual-01/` and is
indexed in `build/aspect-status-dos/attempt-history.json`. Its ANSI cases passed;
the VT220 case incorrectly combined PRM profile4 with a synthetic selected
directory entry still specifying profile6. The actual connection correctly used
the directory's ANSI selection. The corrected fixture specifies profile4 in both
owners and retains the original VT220 expectations. No product change or
weakened status expectation was used to resolve that failure. The earlier
`final-02` four-case success remains unchanged. After adding the live-UART phase
guard, the same checker and predictions were rerun against the new products in
`final-03-phase`; all four cases pass again.

This suite covers the parent's default FDX projection and the script-triggered
BX=FFFF service path. Direct scalar overrides, invalid clients, hidden/alternate
status layouts and HDX projection are separate linked/API tests. DISPLAY is not
executable in this checkpoint, so no DISPLAY/status ordering or suppression
claim is made. These cases do not establish every parser stack bound, physical
modem/CGA timing, arbitrary-bytecode safety or complete application behavior.
Full-application gates remain open.

Use a fresh output label when repeating the proof:

```sh
./tools/dev --command python standalone/test_aspect_status_dos.py \
  --label new-status-run \
  --terminal-sha256 e9c8a731df6af6bc0f2afd25fec1363ce6607dc2be284f1ab911e41d1217ecc5 \
  --runner-sha256 65b3e08de86f436e4216ec2238a20d42b667ef21e1ec2d49a5a745c50daa935a
```

`--prepare --label new-predictions` compiles only the owned source fixtures and
writes predictions; it neither rebuilds nor executes the products. Raw local
reports and synthetic DOS artifacts remain ignored.
