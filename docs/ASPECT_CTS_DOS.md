# Actual DOS emulated CTS stalls

[Validation](validation/aspect-cts-dos.json) accepts two8086 DOS sessions on
parenta4c377c9/runnerec93148f: HARD and BOTH. The owned peer lowers the emulator's
CTS line for1.2seconds while releasing the script's GO wait, then raises CTS.
No payload byte arrives before the rise. Both2,048-byte transmissions, parent
keyboard/query return, child exit and42-byte hardware/JFT/file-owner restoration
pass. The passive timer sees hardware flow enabled and zero software-pause ticks;
the peer never sends XOFF.

This uses `transparent:0` in the pinned DOSBox-X2026.07.02 nullmodem transport.
The upstream [readChar implementation](https://github.com/joncampbell123/dosbox-x/blob/dosbox-x-v2026.07.02/src/hardware/serialport/nullmodem.cpp)
decodes FF followed by a control byte: bit0 supplies CTS and bit1 supplies DSR.
FF FF denotes a data FF. The peer sends FF03 initially, FF02 to lower CTS while
retaining DSR, then FF03 to restore CTS. This drives the emulated MSR through
the normal transport; no product or port-read result is patched.

The [pinned Nixpkgs derivation](https://github.com/NixOS/nixpkgs/blob/f13ff45afd1bb73e640eaa08a7066dbed07e3238/pkgs/by-name/do/dosbox-x/package.nix)
selects the matching2026.07.02 tag. The audit records the actual Nix executable
and wrapper hashes plus retained upstream source hashes. It independently
decodes raw transport receives, including all11 RTS/DTR status frames per case,
and compares the resulting UART stream with its declared expectation. HARD has
2,109 UART bytes; BOTH has2,113 including its four software-flow bytes. Neither
transport metadata nor socket success substitutes for a UART-byte comparison.

```sh
./tools/build test-aspect-cts-dos
```

These are short, clean emulated CTS stalls. Longer stalls, timeout/cancel
handback under low CTS, RTS receive throttling, sustained RX pressure, carrier
reconnect and physical ISA UART/Boca/SPA2102 timing remain unverified. This
checkpoint closes no full application or physical-hardware gate.
