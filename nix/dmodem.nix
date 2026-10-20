{ nixpkgs, system }:
let
  pkgs = import nixpkgs { inherit system; };
  i386 = pkgs.pkgsi686Linux;
  rev = "b1752e4d0039e0cff72735924e03aa99922723a8";
  upstream = path: hash: pkgs.fetchurl {
    url = "https://raw.githubusercontent.com/synexo/synthmodem/${rev}/${path}";
    sha256 = hash;
  };
  headers = {
    "modem.h" = "dbba0e001943c171291ac65459f88c160eb8c769db2644f88eaf4a2afa8d41ae";
    "modem_defs.h" = "dc7e0a41f1f7d49680b61092237012cbb9d961f21b513aa9d2781cf1dfed8fd5";
    "modem_homolog.h" = "140057f5f6647ca5fe0bee4505243039feadfb7d1eabb4de19e9cd0d6dea1415";
    "modem_dp.h" = "81ce5f6da0218881d5a7e254e5a84b4941ac69413b375552648786a795ba504c";
    "modem_timer.h" = "dcc2c46f643743ea6d5f2afc5a283d077a00cb02fb8cadacc3b85afd06e2ae97";
  };
  source = pkgs.runCommand "synthmodem-dmodem-source-${rev}" {} ''
    mkdir -p "$out/slmodemd"
    cp ${upstream "vm/d-modem/d-modem.c" "c2e76759d9529bf467a918e128c5b3e15b4eaff0077d32bdc896a54e36a478a1"} "$out/d-modem.c"
    ${pkgs.lib.concatStringsSep "\n" (pkgs.lib.mapAttrsToList (name: hash:
      "cp ${upstream "vm/slmodemd/${name}" hash} \"$out/slmodemd/${name}\"") headers)}
  '';
  pjproject = i386.stdenv.mkDerivation {
    pname = "pcplus-pjproject-i386";
    version = "2.15.1";
    src = upstream "vm/sources/pjproject-2.15.1.tar.gz" "8f3bd99caf003f96ed8038b8a36031eb9d8cd9eaea1eaff7e01c2eef6bd55706";
    nativeBuildInputs = [ pkgs.pkg-config ];
    configureFlags = [ "--disable-video" "--disable-sound" "--disable-ssl"
      "--disable-sdl" "--disable-ffmpeg" "--disable-v4l2" "--disable-openh264"
      "--disable-libyuv" "--disable-libwebrtc" ];
    preConfigure = ''
      touch pjlib/include/pj/config_site.h
      export CFLAGS="-O2 -std=gnu11"
      export CXXFLAGS="-O2 -std=gnu++17"
      # PJSIP uses LD to link executables, so it needs the compiler driver.
      export LD="$CC"
    '';
    enableParallelBuilding = true;
    buildPhase = ''
      runHook preBuild
      make dep
      make -j"$NIX_BUILD_CORES"
      runHook postBuild
    '';
  };
  build = noDiscard: i386.stdenv.mkDerivation {
    pname = "pcplus-dmodem-${if noDiscard then "no-discard" else "baseline"}-i386";
    version = "${rev}";
    src = source;
    nativeBuildInputs = [ pkgs.pkg-config ];
    buildInputs = [ pjproject i386.glibc.static ];
    dontConfigure = true;
    postPatch = pkgs.lib.optionalString noDiscard ''
      substituteInPlace d-modem.c --replace-fail \
        'med_cfg.jb_init = 40;' \
        'med_cfg.jb_init = 40; med_cfg.jb_discard_algo = PJMEDIA_JB_DISCARD_NONE;'
    '';
    buildPhase = ''
      runHook preBuild
      $CC -std=gnu11 -O2 -Wall -I. -Islmodemd \
        $(pkg-config --static --cflags libpjproject) \
        -o d-modem d-modem.c -static $(pkg-config --static --libs libpjproject)
      runHook postBuild
    '';
    installPhase = ''
      mkdir -p "$out/bin" "$out/share/pcplus-dmodem"
      cp d-modem "$out/bin/"
      cp d-modem.c "$out/share/pcplus-dmodem/"
      cp -r slmodemd "$out/share/pcplus-dmodem/"
    '';
  };
  jitterCheck = i386.stdenv.mkDerivation {
    pname = "pcplus-jitter-policy-check-i386";
    version = "2.15.1";
    dontUnpack = true;
    dontConfigure = true;
    nativeBuildInputs = [ pkgs.pkg-config ];
    buildInputs = [ pjproject i386.glibc.static ];
    buildPhase = ''
      $CC -std=gnu11 -O2 -Wall -Wextra -Werror \
        $(pkg-config --static --cflags libpjproject) \
        ${../lab/bbs/jitter_policy_check.c} -o jitter-check \
        -static $(pkg-config --static --libs libpjproject)
      ./jitter-check
    '';
    installPhase = ''
      mkdir -p "$out/bin"
      cp jitter-check "$out/bin/"
    '';
  };
in { baseline = build false; candidate = build true; jitter-check = jitterCheck; inherit pjproject; }
