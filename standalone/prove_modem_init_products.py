#!/usr/bin/env python3
"""Rebuild normal/mouse terminal and DOS compiler from admitted source only."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);fresh=out/'source';sources={};products={}
    for directory,binary in [('terminal','TERMINAL.EXE'),('terminal-mouse','TERMINAL.EXE'),('aspect-compiler-dos','ASPCOMP.EXE')]:
        m=read(ROOT/'build'/directory/'manifest.json');assert sha(ROOT/'build'/directory/binary)==m['binary_sha256'];products[directory+'/'+binary]=m['binary_sha256']
        for name,digest in m['sources'].items():assert name not in sources or sources[name]==digest;sources[name]=digest
    for name,digest in sources.items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build','analysis','original','originals','install')
        assert path.suffix.lower() not in ('.exe','.com','.obj','.bin','.img','.db') and sha(ROOT/name)==digest
        target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    for index,args in enumerate([['standalone/build_terminal.py'],['standalone/build_terminal.py','--mouse'],['standalone/build_aspect_compiler_dos.py']]):
        with (out/f'build-{index}.log').open('w') as log:subprocess.run([sys.executable,*args],cwd=fresh,stdout=log,stderr=log,check=True,timeout=180)
    for name,digest in products.items():assert sha(fresh/'build'/name)==sha(ROOT/'build'/name)==digest
    for name,digest in sources.items():assert sha(fresh/name)==sha(ROOT/name)==digest
    report=dict(passed=True,products=products,sources=sources,original_inputs=[],checker_sha256=sha(Path(__file__)),scope=__doc__+' Fresh directory contains only declared source inputs and tool-generated outputs. Three products only; the full application and physical hardware requirements remain open.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,products=3,source_files=len(sources))))


if __name__=='__main__':main()
