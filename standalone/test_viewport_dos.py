#!/usr/bin/env python3
"""Reproduce both viewport controls and reset composition, then run maintained DOS copies."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists()
    base=ROOT/'build/viewport';manifest=json.loads((base/'manifest.json').read_text())
    joined=ROOT/'build/terminal-reset-viewport';reset=json.loads((joined/'manifest.json').read_text())
    sources={**manifest['sources'],**reset['sources']};fresh=out/'source'
    for name,digest in sources.items():
        assert sha(ROOT/name)==digest,name
        target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    assert not(fresh/'build').exists()
    with(out/'source-build.log').open('w')as log:
        for command in [[sys.executable,'standalone/build_viewport.py'],[sys.executable,'standalone/build_terminal_reset.py','--viewport']]:
            subprocess.run(command,cwd=fresh,stdout=log,stderr=log,check=True,timeout=60)
    products={}
    for name,digest in manifest['products'].items():
        path='build/viewport/'+name;assert sha(ROOT/path)==sha(fresh/path)==digest;products[path]=digest
    path='build/terminal-reset-viewport/RESET.EXE'
    assert sha(ROOT/path)==sha(fresh/path)==reset['binary_sha256'];products[path]=reset['binary_sha256']
    config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{base}"\nmount d "{out}"\nc:\nVIEWPORT\nif errorlevel 1 goto failed\necho PASS>D:\\PASS.TXT\nexit\n:failed\necho FAIL>D:\\FAIL.TXT\nexit\n'
    (out/'dosbox.conf').write_text(config)
    with(out/'dosbox.log').open('w')as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
                         stdout=log,stderr=log,timeout=20,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
    assert r.returncode==0 and(out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists()
    for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest
    sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    result=dict(passed=True,cpu='8086',original_inputs=[],products=products,source_files=len(sources)-1,sources=sources,
                source_build_log_sha256=sha(out/'source-build.log'),
                scope='Two actual DOS maintained far/video copies with exact cells and DS=SS. Three source-only products reproduce byte-identically in empty tree. Native foreign-DS control is not run in DOS. No live viewport/width, allocation or physical CGA acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS DOS8086 viewport and three-product empty-tree reproduction')


if __name__=='__main__':main()
