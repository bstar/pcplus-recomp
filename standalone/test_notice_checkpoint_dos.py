#!/usr/bin/env python3
"""Verify bank-local recovery and fail-stop behavior on an actual 8086 DOS guest."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    out=parser.parse_args().output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    base=ROOT/'build/notice-checkpoint'
    manifest=json.loads((base/'manifest.json').read_text())
    assert manifest['original_inputs']==[]
    assert all(sha(ROOT/p)==h for p,h in manifest['sources'].items())
    assert sha(base/'CHECK.EXE')==manifest['binary_sha256']
    symbols={name:(int(seg,16),int(offset,16)) for seg,offset,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+(\w+)\s*$',(base/'CHECK.map').read_text(),re.M|re.I)}
    bank=symbols['_notice_checkpoint_call'][0]
    assert all(symbols[name][0]==bank for name in ['_notice_checkpoint_abort','_notice_checkpoint_active','_notice_call_native','_notice_checkpoint_probe'])
    assert symbols['_notice_checkpoint_peer'][0]!=bank
    with tempfile.TemporaryDirectory(prefix='pcplus-notice-checkpoint-') as name:
        stage=Path(name)
        for path in manifest['sources']:
            dest=stage/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,dest)
        with (out/'source-build.log').open('w') as log:
            subprocess.run(['python3',str(stage/'standalone/build_notice_checkpoint.py')],cwd=stage,stdout=log,stderr=log,check=True)
        assert sha(stage/'build/notice-checkpoint/CHECK.EXE')==manifest['binary_sha256']
    shutil.copy2(base/'CHECK.EXE',out/'CHECK.EXE')
    config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
c:
CHECK >OUTPUT.TXT
if errorlevel 1 goto failed
CHECK INVALID
if errorlevel 128 goto failed
if errorlevel 127 goto passed
:failed
echo FAIL>FAIL.TXT
exit
:passed
echo PASS>PASS.TXT
exit
'''
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=45)
    text=(out/'OUTPUT.TXT').read_text() if (out/'OUTPUT.TXT').exists() else ''
    checks=dict(emulator_exit=process.returncode==0,DOS_exit=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),probe=text.strip()=='CHECKPOINT PASS 2048 calls 2048 far callbacks',binary_unchanged=sha(out/'CHECK.EXE')==manifest['binary_sha256'])
    result=dict(passed=all(checks.values()),checks=checks,bank_segment=bank,callback_segment=symbols['_notice_checkpoint_peer'][0],binary_sha256=manifest['binary_sha256'],inputs={**manifest['sources'],str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str((base/'manifest.json').relative_to(ROOT)):sha(base/'manifest.json')},captures_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()},scope='2048 native calls across sixteen normal/abort/nested/deep x IF0/1 x DF0/1 combinations. Foreign-CS far bridge calls a near callback. Recovery checks SP, BP/BX/SI/DI, DS/ES, IF/DF, typed return and inactive frame; inactive abort must terminate DOS with127. Fresh four-source build reproduces executable. Not PROGRAM integration or arbitrary nonlocal-fault acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,output=text)))
    assert result['passed']
if __name__=='__main__':main()
