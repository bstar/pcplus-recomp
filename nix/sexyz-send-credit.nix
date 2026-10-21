{ pkgs }:
let
  baseline = import ./sexyz-receive-finish.nix { inherit pkgs; candidate = false; };
in baseline.overrideAttrs (old: {
  pname = "sexyz-send-credit-candidate";
  buildPhase = builtins.replaceStrings
    [ ''make CC="$CC" -j"$NIX_BUILD_CORES"'' ]
    [ ''python3 ${../tools/patch-sexyz-send-credit.py} "$PWD"
        make CC="$CC" -j"$NIX_BUILD_CORES"'' ]
    old.buildPhase;
  installPhase = old.installPhase + ''
    cp send-credit-manifest.json "$out/share/sexyz-source/"
  '';
  meta = old.meta // {
    description = "Pinned isolated SEXYZ sender candidate respecting finite receive credit";
  };
})
