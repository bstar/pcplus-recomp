{ pkgs, candidate ? true }:
pkgs.stdenv.mkDerivation {
  pname = if candidate then "sexyz-receive-finish-candidate" else "sexyz-source-baseline";
  version = "3.6-e7a8257";
  src = pkgs.fetchzip {
    url = "https://codeload.github.com/SynchronetBBS/sbbs/tar.gz/e7a825704ef5329c7ef8408749671291a85ef7f2";
    extension = "tar.gz";
    hash = "sha256-JIFoufcrtRtoyCl3ijBELzZpcZirz//G/HKoiUYuFcU=";
  };
  nativeBuildInputs = [ pkgs.python3 ];
  dontConfigure = true;
  buildPhase = ''
    runHook preBuild
    python3 ${../tools/cut-sexyz-source.py} "$PWD" "$TMPDIR/sexyz-cut"
    cd "$TMPDIR/sexyz-cut"
    ${pkgs.lib.optionalString candidate ''
      cp ${../lab/bbs/patches/sexyz-receive-finish/receive_finish.c} receive_finish.c
      cp ${../lab/bbs/patches/sexyz-receive-finish/receive_finish.h} receive_finish.h
      cp ${../src/transfer/zmodem_wire.c} zmodem_wire.c
      cp ${../src/transfer/zmodem_wire.h} zmodem_wire.h
      python3 - <<'PY'
from pathlib import Path
p=Path('sexyz.c');s=p.read_text()
needle='#include "sexyz.h"';assert s.count(needle)==1
s=s.replace(needle,needle+'\n#include "receive_finish.h"')
needle='\t\t\t\t\tcase ZFIN:\n\t\t\t\t\tcase ZCOMPL:';assert s.count(needle)==1
s=s.replace(needle,'\t\t\t\t\tcase ZFIN:\n\t\t\t\t\t\tif (!loc_receive_finish(&zm)) {\n\t\t\t\t\t\t\tlprintf(LOG_WARNING, "LoC RXFIN: closing OO unconfirmed");\n\t\t\t\t\t\t\treturn 1;\n\t\t\t\t\t\t}\n\t\t\t\t\tcase ZCOMPL:')
p.write_text(s)
p=Path('GNUmakefile');s=p.read_text();needle='OBJS = $(SRCS:.c=.o)';assert s.count(needle)==1
p.write_text(s.replace(needle,'SRCS += receive_finish.c zmodem_wire.c\n\n'+needle))
PY
    ''}
    make CC="$CC" -j"$NIX_BUILD_CORES"
    ./sexyz v
    runHook postBuild
  '';
  installPhase = ''
    mkdir -p "$out/bin" "$out/share/sexyz-source"
    cp sexyz "$out/bin/"
    cp *.c *.h GNUmakefile LICENSE source-manifest.json "$out/share/sexyz-source/"
  '';
  meta = {
    description = "Isolated pinned SEXYZ source build; optional bounded receive closing owner";
    license = pkgs.lib.licenses.gpl2Plus;
    platforms = [ "x86_64-linux" ];
  };
}
