{ nixpkgs, system }:
let
  baseline = (import ./slmodem.nix { inherit nixpkgs system; }).baseline;
  carrier = ../lab/bbs/patches/synthmodem-carrier;
in baseline.overrideAttrs (old: {
  pname = "pcplus-slmodemd-carrier-i386";
  patches = (old.patches or []) ++ [ (carrier + /slmodem.patch) ];
  postPatch = old.postPatch + ''
    cp ${carrier + /carrier_client.c} carrier_client.c
    cp ${carrier + /carrier_client.h} carrier_client.h
    cp ${carrier + /carrier_protocol.h} carrier_protocol.h
  '';
})
