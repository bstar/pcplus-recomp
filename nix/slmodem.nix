{ nixpkgs, system }:
let
  pkgs = import nixpkgs { inherit system; };
  i386 = pkgs.pkgsi686Linux;
  rev = "b1752e4d0039e0cff72735924e03aa99922723a8";
  files = builtins.fromJSON (builtins.readFile ./slmodem-sources.json);
  source = pkgs.runCommand "pcplus-slmodemd-source-${rev}" {} ''
    mkdir -p "$out"
    ${pkgs.lib.concatStringsSep "\n" (pkgs.lib.mapAttrsToList (name: hash:
      "cp ${pkgs.fetchurl { url = "https://raw.githubusercontent.com/synexo/synthmodem/${rev}/vm/slmodemd/${name}"; sha256 = hash; }} \"$out/${name}\"") files)}
  '';
  baseline = i386.stdenv.mkDerivation {
    pname = "pcplus-slmodemd-baseline-i386";
    version = rev;
    src = source;
    buildInputs = [ i386.glibc.static ];
    dontConfigure = true;
    postPatch = ''
      substituteInPlace modem_main.c --replace-fail \
        '#include <modem_debug.h>' \
        '#include <modem_debug.h>
      #include <time.h>'
    '';
    hardeningDisable = [ "pic" ];
    enableParallelBuilding = true;
    buildPhase = ''
      runHook preBuild
      make -j"$NIX_BUILD_CORES" CC="$CC" \
        CFLAGS="-O2 -g -std=gnu11 -Wall -fno-strict-aliasing -I. -DCONFIG_DEBUG_MODEM" \
        LFLAGS="-static -no-pie -lm" slmodemd
      runHook postBuild
    '';
    installPhase = ''
      mkdir -p "$out/bin"
      cp slmodemd "$out/bin/"
    '';
  };
in { inherit baseline; }
