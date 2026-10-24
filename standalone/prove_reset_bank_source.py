#!/usr/bin/env python3
"""Reproduce the private reset bank and repeat its actual IRQ workflow in a fresh tree."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();out=(args.output or ROOT/'build/reset-bank-source'/datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')).resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads((ROOT/'build/reset-bank/manifest.json').read_text())
    assert sha(ROOT/'build/reset-bank/BANK.EXE')==manifest['binary_sha256']
    sources=dict(manifest['sources'])
    for name in ['standalone/test_reset_bank_dos.py','standalone/test_terminal.py','standalone/build_terminal_reset.py',
        'reconstruction/terminal_reset/provenance.json','nix/flake.nix','nix/flake.lock','tools/dev']:
        sources[name]=sha(ROOT/name)
    fresh=out/'source'
    for name,digest in sources.items():
        path=Path(name);assert not path.is_absolute()and'..'not in path.parts
        assert path.parts[0]not in('build','analysis','original','originals','install')
        assert path.suffix.lower()not in('.exe','.obj','.img','.o','.prm','.dir','.xlt')
        assert sha(ROOT/path)==digest,name
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
    assert not(fresh/'build').exists()and not(fresh/'analysis').exists()
    with(out/'build.log').open('w')as log:
        subprocess.run([sys.executable,'standalone/build_reset_bank.py'],cwd=fresh,stdout=log,stderr=log,check=True,timeout=90)
    assert sha(fresh/'build/reset-bank/BANK.EXE')==manifest['binary_sha256']
    assert json.loads((fresh/'build/reset-bank/manifest.json').read_text())==manifest
    controls={}
    for kind,flags in [('terminal-reset',[]),('terminal-reset-viewport',['--viewport'])]:
        original=ROOT/'build'/kind/'RESET.EXE'
        with(out/(kind+'.log')).open('w')as log:
            subprocess.run([sys.executable,'standalone/build_terminal_reset.py',*flags],cwd=fresh,stdout=log,stderr=log,check=True,timeout=90)
        assert sha(fresh/'build'/kind/'RESET.EXE')==sha(original)
        controls[kind]=sha(original)
    assert controls=={'terminal-reset':'8bdd8c62707ef4c1761c734a9481cad18be991aeed3cadd6194c527f14408e32',
        'terminal-reset-viewport':'066101b9dd744d9dec029ac2160decd0a3c6505c3d4f1c787e651d4c45fa5e92'}
    with(out/'DOS.log').open('w')as log:
        subprocess.run([sys.executable,'standalone/test_reset_bank_dos.py','--output','build/reset-bank-dos/fresh'],
            cwd=fresh,stdout=log,stderr=log,check=True,timeout=45)
    report=fresh/'build/reset-bank-dos/fresh/checks.json';dos=json.loads(report.read_text())
    assert dos['passed']and all(dos['checks'].values())and dos['binary_sha256']==manifest['binary_sha256']
    for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
    result=dict(passed=True,binary_sha256=manifest['binary_sha256'],source_files=len(sources),sources=sources,
        groups=manifest['groups'],context_layout=manifest['context_layout'],controls=controls,actual_DOS_passed=True,
        DOS_report_sha256=sha(report),build_log_sha256=sha(out/'build.log'),DOS_log_sha256=sha(out/'DOS.log'),
        checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS private reset context:',len(sources),'sources, exact controls and freshDOS8086 IRQ replay')


if __name__=='__main__':main()
