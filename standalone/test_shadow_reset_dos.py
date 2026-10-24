#!/usr/bin/env python3
"""Execute actual owned native wide/narrow resets and typed rollback in DOS8086."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists()
    base=ROOT/'build/terminal-reset-shadow';manifest=json.loads((base/'manifest.json').read_text())
    assert manifest['shadow_owner']and manifest['binary_sha256']==sha(base/'RESET.EXE')
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    out.mkdir(parents=True)
    shutil.copyfile(base/'RESET.EXE',out/'RESET.EXE')
    for name in manifest['sources']:
        target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{out}"\nmount d "{out}"\nc:\nRESET >D:\\REPORT.TXT\nif errorlevel 1 goto failed\necho PASS>D:\\PASS.TXT\nexit\n:failed\necho FAIL>D:\\FAIL.TXT\nexit\n'
    (out/'dosbox.conf').write_text(config)
    timed_out=False;returncode=None
    with(out/'dosbox.log').open('w')as log:
        try:
            r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
                             stdout=log,stderr=log,timeout=45,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
            returncode=r.returncode
        except subprocess.TimeoutExpired:timed_out=True
    report=(out/'REPORT.TXT').read_text()if(out/'REPORT.TXT').exists()else''
    assert sha(out/'RESET.EXE')==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():
        assert sha(out/'inputs'/name)==digest and sha(ROOT/name)==digest,name
    passed=returncode==0 and(out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists()and report.startswith('PASS ')
    boot=struct.unpack('<4H',(out/'BOOT.BIN').read_bytes())if(out/'BOOT.BIN').exists()else None
    if passed:assert boot and boot[0]==boot[1]and(boot[3]&0x600)==0x200
    result=dict(passed=passed,cpu='8086',report=report,timed_out=timed_out,boot=boot,binary_sha256=manifest['binary_sha256'],sources={**manifest['sources'],
                'standalone/test_shadow_reset_dos.py':sha(Path(__file__))},
                scope='Actual DOS direct-memory allocation, native width/reset/geometry/clear plus guarded synchronous transaction. Faults requested by explicit diagnostic flags; no live terminal or asynchronous-fault acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(report.strip());assert passed


if __name__=='__main__':main()
