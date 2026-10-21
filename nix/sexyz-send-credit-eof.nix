{ pkgs }:
let
  credit = import ./sexyz-send-credit.nix { inherit pkgs; };
in credit.overrideAttrs (old: {
  pname = "sexyz-send-credit-eof-candidate";
  buildPhase = builtins.replaceStrings
    [ ''make CC="$CC" -j"$NIX_BUILD_CORES"'' ]
    [ ''python3 ${../tools/patch-sexyz-eof-position.py} "$PWD"
        make CC="$CC" -j"$NIX_BUILD_CORES"'' ]
    old.buildPhase;
  installPhase = old.installPhase + ''
    cp eof-position-manifest.json "$out/share/sexyz-source/"
  '';
  meta = old.meta // {
    description = "Pinned isolated SEXYZ finite-credit and EOF-position sender candidate";
  };
})
