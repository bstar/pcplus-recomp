{ baseline }:
let carrier = ../lab/bbs/patches/synthmodem-carrier;
in baseline.overrideAttrs (old: {
  pname = "synthmodem-control-carrier";
  patches = old.patches ++ [ (carrier + /control.patch) ];
  postPatch = (old.postPatch or "") + ''
    cp ${carrier + /carrier_protocol.h} vm/ctrl/carrier_protocol.h
    cp ${carrier + /carrier_server.h} vm/ctrl/carrier_server.h
    cp ${carrier + /carrier_server.inc} vm/ctrl/carrier_server.inc
  '';
})
