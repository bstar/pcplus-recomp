# Booted i386 control-helper validation

The maintained control-helper source patch now builds as a static Intel i386
Linux executable through the pinned Nix toolchain and runs inside the upstream
32-bit VM kernel/runtime. This advances the helper beyond host-only testing.
It does not boot the full SIP/DSP stack or compose the Node pressure writer yet.

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

Next: connect the actual Node pressure candidate to this rebuilt helper in one
VM test, then run the normal slmodemd/PJSIP stack and real DOS/BBS workflows.
Native DSP flow credit, serial-to-BBS pressure, SIP/audio, Boca V.8/14.4 negotiation
and physical SPA2102 acceptance remain open. No installed service or live BBS was
changed.
