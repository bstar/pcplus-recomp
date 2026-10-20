# Booted i386 control-helper validation

The maintained control-helper source patch now builds as a static Intel i386
Linux executable through the pinned Nix toolchain and runs inside the upstream
32-bit VM kernel/runtime. This advances the helper beyond host-only testing.
The standalone helper test below does not boot the full SIP/DSP stack. A
separate [Node/helper composition test](#nodehelper-composition) now connects
the actual pressure candidate to that same rebuilt guest helper.

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_vm_control.py \
  --output build/bbs-lab/synthmodem-vm-control-new
```

Use a fresh output directory. The harness builds
`nix#synthmodem-control-i386`, verifies ELF32/Intel386 and absence of a dynamic
interpreter, and checksum-pins the upstream kernel and runtime image from
SynthModem revision `b1752e4d0039e0cff72735924e03aa99922723a8`. The Nix package
reads only public checksum-pinned C/header source plus the maintained patch.
Its i686 GCC/glibc-static environment is pinned by the existing Nixpkgs lock;
the static link avoids depending on the workstation's or guest's libc loader.
The default DOS application build and its inputs remain unchanged.

The original runtime archive is read without filesystem extraction. A separate
archive replaces only the control-helper file's bytes and adds `lab-init`.
Every other archived file's payload is required to remain identical. The lab
init mounts pseudo-filesystems, loads the original kernel-matched virtio modules
and runs the rebuilt helper. It bypasses the normal SIP/DSP startup explicitly.
The original downloaded image is never overwritten.

QEMU uses TCG, one CPU,128MiB, no NIC and two loopback socket-backed virtio serial
ports. One is the real guest control character channel; the other is a modem
character-port stand-in in place of slmodemd's PTY. Host Python supplies only
the remote/control boundary. Coalesced ATZ/ATD1 frames must become the exact
command bytes, and a synthetic OK/CONNECT14400 response must produce the helper's
actual data-mode/status transition. This is not a real modem handshake.

Fourteen checks cover the guest build-id HELLO, coalesced payload/CR ordering,
mode transition,16777219 exact bytes in each direction, observable blocked source
writers and opposite-direction service during each stall. Closing the control
transport must cause the helper to report its explicit error exit1 and the lab
init to power the VM off. Every owned worker must stop without errors.

The first pilot moved exact2MiB/1MiB payloads but did not exhaust QEMU/TCP
buffers, so its backpressure checks failed. That attempt is retained as failed.
The accepted cohort increases both payloads past16MiB and verifies actual stalls
without changing the helper. File sizes/hashes, raw control framing, immutable
inputs and the rebuilt archive's exact delta are audited separately.

Runtime images, executables, raw captures and candidate archives stay under
ignored build storage. The static helper is an optional Nix product; original
images and compiled helpers never become PCPlus application build inputs.

The [recorded receipt](../../docs/validation/synthmodem-vm-control.json) retains
the14 checks, independent raw-frame/payload audit, source/media hashes, Nix
derivation, QEMU command and archive identity. Accepted cohort:
`synthmodem-vm-control-02`.

Next: run the normal slmodemd/PJSIP stack and real DOS/BBS workflows through
the composed candidate.
Native DSP flow credit, serial-to-BBS pressure, SIP/audio, Boca V.8/14.4 negotiation
and physical SPA2102 acceptance remain open. No installed service or live BBS was
changed.

## Node/helper composition

```sh
./tools/modem-dev --command python3 lab/bbs/synthmodem_vm_composed.py \
  --candidate build/bbs-lab/synthmodem-pressure-05/candidate \
  --output build/bbs-lab/synthmodem-vm-composed-new
```

Use a fresh output directory. The candidate must match every file in the
pressure receipt; stage it with the pressure checker first if absent. The VM
media must already be present from the standalone helper test above. Both tests
use the same Nix-built static i386 helper and checksum-pinned runtime media.

The Node driver uses the actual PjsipBackend constructor/control parser/writer
and CallSession attachment/teardown methods. The unopened SIP/RTP resource
imports reject invocation, and session resource ownership is supplied by the
harness. QEMU startup and socket connection are externally orchestrated. The
guest receives ATZ/ATD1; its synthetic modem endpoint supplies OK/CONNECT14400.
The actual helper and Node parser must enter connected mode without forcing
the backend connected flag. Zero post-train hold/quiescence is explicit lab
configuration, not a validated audio-training policy.

The synthetic modem then enters a loopback server address as online data. The
server offers Telnet BINARY in both directions. Pausing the modem-side reader
must propagate pressure across the guest/helper/control socket until the
actual proxy pauses its BBS socket. Resuming recovers16777219 exact bytes;
the reverse path transfers the same all-byte pattern while read continuously.
The reverse test does not establish reverse-TCP pressure support.

The accepted `synthmodem-vm-composed-01` cohort passes19 checks. Four drain events
were observed; at the measured pause the retained ring held20258 bytes and the
Node socket held69425 wire bytes. Both payload hashes are
`18a38005f8d075ef78597b4e16417c65ec9a823be88f9a7af1a69ea8bda9bb8e`.
Actual session hangup closes the control socket, retires the writer/drain owner
and produces the expected guest helper error exit1 followed by VM poweroff.

The Python audit independently decodes all32773 guest frames, reconstructs the
hostname plus reverse payload, checks forward modem bytes and decodes the BBS
stream without using the candidate codec. The
[receipt](../../docs/validation/synthmodem-vm-composed.json) binds raw wire hashes,
all candidate files, harness inputs, Nix build, image delta and tool versions.
The synthetic CONNECT14400 is a parser fixture: it proves no V.32bis negotiation.
No real modem DSP, SIP/RTP/audio, DOS client, BBS software or hardware runs here.
