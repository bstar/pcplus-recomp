{ pkgs }:
# Separate test device, never the default DOSBox-X or a workstation install.
# Stock nullmodem FF flags control CTS/DSR, while TCP attachment owns DCD.
# This opt-in high-bit marker exposes DCD as an external hardware stimulus.
pkgs.dosbox-x.overrideAttrs (old: {
  pname = "dosbox-x-pcplus-dcd-lab";
  patches = (old.patches or []) ++ [ ./patches/dosbox-dcd-control.patch ];
})
