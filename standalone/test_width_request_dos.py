#!/usr/bin/env python3
"""Rebuild the width adapter in an empty tree, then execute its DOS boundary observer."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists()
    base=ROOT/'build/width-request';m=json.loads((base/'manifest.json').read_text())
    assert m['original_inputs']==[]and m['binary_sha256']==sha(base/'WIDTH.EXE')
    fresh=out/'source'
    for name,digest in m['sources'].items():
        assert sha(ROOT/name)==digest
        target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    assert not(fresh/'build').exists()
    with(out/'source-build.log').open('w')as log:
        subprocess.run([sys.executable,'standalone/build_width_request.py'],cwd=fresh,stdout=log,stderr=log,check=True)
    assert sha(fresh/'build/width-request/WIDTH.EXE')==m['binary_sha256']
    assert sha(fresh/'build/width-request/baseline.bin')==m['baseline_sha256']
    config='[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\n'
    config+=f'mount c "{base}"\nmount d "{out}"\nc:\nWIDTH\nif errorlevel 1 goto failed\necho PASS>D:\\PASS.TXT\nexit\n:failed\necho FAIL>D:\\FAIL.TXT\nexit\n'
    (out/'dosbox.conf').write_text(config)
    with(out/'dosbox.log').open('w')as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
                         stdout=log,stderr=log,timeout=20,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
    assert r.returncode==0 and(out/'PASS.TXT').is_file()and not(out/'FAIL.TXT').exists()
    for name,digest in m['sources'].items():assert sha(ROOT/name)==sha(fresh/name)==digest
    assert sha(base/'WIDTH.EXE')==m['binary_sha256']
    sources=dict(m['sources']);sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    result=dict(passed=True,cpu='8086',binary_sha256=m['binary_sha256'],source_files=len(m['sources']),
                original_inputs=[],sources=sources,source_build_log_sha256=sha(out/'source-build.log'),
                scope='Two actual DOS calls through recovered adapter with synthetic reset observer; DS=SS, '
                'temporary setting, restoration and native argument cleanup. Empty-source-tree rebuild exact. '
                'No native reset implementation, viewport or 132-column application acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS DOS8086 width adapter and empty-tree reproduction')


if __name__=='__main__':main()
