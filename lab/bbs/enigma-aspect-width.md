# ENiGMA width requests during ASPECT execution

The source-built terminal and interpreter now execute the synthetic ENiGMA
width route while a real ASPECT process owns serial input. The script enters
WIDTH after normal login, waits for each returned frame, sends Right, Left,
narrow and wide commands, then returns to Main. A later manual F command must
open File Base after the child returns. These runs use the explicitly checked
incremental-decoder server candidate with immediate modem forwarding.

`peer-width-enigma-aspect-window-03` passes all12 checks with precompiled ASX
and the cooperative script window. `peer-width-enigma-aspect-source-window-01`
passes the same checks after actual DOS ASPCOMP compilation. Its generated ASX
matches the host compiler byte for byte. The script's DOS file records every
successful step as `START|0|1|2|3|4|RETURN|`.

The read-only observer in `peer_width_aspect_watch.asm` identifies root DS
during a genuine BIOS cursor call after the first wide request. It checks the
live geometry, canonical field pointer and active ASPECT owner before accepting
the address. It never seeds fields, invokes a width API, patches an executable
or supplies a serial reply. Timer samples require attached renderer and busy
bridge activity; windowed runs additionally require visible-overlay samples.
Actual child and parent DOS exits check DS=SS, child exit0 and final idle
parser, ASPECT, PROGRAM and native-bank owners at80 columns.

The observer removes its INT10/21/1C hooks before the independent final sampler.
Its first full pilot passed the application checks but correctly failed hardware
restoration because its own INT1C hook remained. The only changed snapshot
bytes were that vector. The accepted repeat restores all42 sampled bytes.
The observer installs only inside the isolated DOSBox process.

Example, with the already prepared/started decoder fixture:

```sh
./tools/dev --command python3 lab/bbs/enigma_peer_width_aspect_dos.py \
  --candidate build/bbs-lab/peer-width-enigma-framed-01 \
  --terminal build/SELECTED-SOURCE-PRODUCT/TERMINAL.EXE \
  --runner build/aspect-register-parent-custom-irq/ASPECT.EXE \
  --compiler build/aspect-compiler-dos/ASPCOMP.EXE \
  --window --label YOUR-FRESH-LABEL
```

Omit `--compiler` for host-precompiled ASX; omit `--window` for the ordinary
script display. Each run validates and privately copies the selected product
inputs. The generated harness adapter only inserts the read-only observer
before the unchanged application; its exact source is retained with the case.
There are no private dialing profiles or real messages/files in the fixture.

The [stock immediate/buffered comparison](peer-width.md) remains separate.
The closed-window source and precompiled cases also pass, completing the
four-case display matrix. The [receipt](../../docs/validation/enigma-aspect-width.json)
independently checks both server-side cursor results
and actual UART bytes, the script marker, private compiler output, distinct
parent/child DS=SS images, window samples and complete hardware restoration.
Its acceptance applies to this composition checkpoint; deployment and full
compatibility remain false.

`peer-width-enigma-stock-aspect-source-window-01` adds a passing DOS-compiled,
windowed case against the unmodified stock decoder with explicit20ms modem
buffering. The receipt retains that fifth run separately from the four-case
decoder matrix. It does not remove the stock immediate-forwarding failure or
guarantee TCP receive boundaries on another network.

The combined receipt binds176 artifacts. Reproduce it with the four decoder
labels above and `--stock-label peer-width-enigma-stock-aspect-source-window-01`
using `record_enigma_aspect_width.py`; each source/precompiled and window state
is mandatory. The temporary servers were stopped after this campaign.

This does not fix remote stock ENiGMA input fragmentation or establish stock
132-column artwork adaptation, active Synchronet width composition, wide file
transfers, carrier/OS interruption, physical modem or card acceptance.
