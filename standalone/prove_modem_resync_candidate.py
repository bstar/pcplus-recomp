#!/usr/bin/env python3
"""Rebuild normal/mouse synchronization candidates using only admitted source files."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path
from audit_aspect_transmit_wait import ROOT, sha, read


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    candidate=a.candidate.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    sources={};products={};fresh=out/'source'
    for name in ('terminal','terminal-mouse'):
        manifest=read(candidate/'build'/name/'manifest.json');binary=candidate/'build'/name/'TERMINAL.EXE'
        assert sha(binary)==manifest['binary_sha256'];products[name]=sha(binary)
        for key,digest in manifest['sources'].items():
            assert key not in sources or sources[key]==digest;sources[key]=digest
    for name,digest in sources.items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build','analysis','original','originals','install')
        assert path.suffix.lower() not in ('.exe','.com','.obj','.bin','.img','.db')
        assert sha(candidate/path)==digest
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(candidate/path,target)
    for flags in ([],['--mouse']):
        with (out/('mouse.log' if flags else 'normal.log')).open('w') as log:
            subprocess.run([sys.executable,'standalone/build_terminal.py',*flags],cwd=fresh,stdout=log,stderr=log,check=True,timeout=180)
    for name,digest in products.items():assert sha(fresh/'build'/name/'TERMINAL.EXE')==digest
    for name,digest in sources.items():assert sha(fresh/name)==sha(candidate/name)==digest
    report=dict(passed=True,products=products,sources=sources,original_inputs=[],checker_sha256=sha(Path(__file__)),scope=__doc__+' Two products only; fresh directory has no original executables or prebuilt inputs. Full application/source and hardware requirements remain open.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,products=len(products),sources=len(sources))))


if __name__=='__main__':main()
