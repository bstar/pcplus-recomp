#!/usr/bin/env python3
"""Normal and retained native-input exit, including the ordinary ASPECT CLI."""
import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
from build_notice_input_exit import ROOT,OUT,sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    m=json.loads((OUT/'manifest.json').read_text());assert not m['original_inputs']
    for n,h in m['sources'].items():
        assert sha(ROOT/n)==h;target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    sys.path.insert(0,str(ROOT/'src/aspect'));from compiler import compile_source
    source='proc main\nrun "ABSENT.COM"\nendproc\n';cases=[]
    for mode in ['C','H','A']:
        folder=out/mode;folder.mkdir()
        for n,h in m['products'].items():assert sha(OUT/n)==h;shutil.copyfile(OUT/n,folder/n)
        (folder/'HOLD.ASP').write_text(source);(folder/'HOLD.ASX').write_bytes(compile_source(source))
        cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{folder}"
c:
NIPAR {mode} >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
'''
        (folder/'dosbox.conf').write_text(cfg)
        with (folder/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=folder,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=35)
        text=(folder/'OUTPUT.TXT').read_text(errors='replace') if (folder/'OUTPUT.TXT').exists() else ''
        summary=re.search(r'^INPUT EXIT '+mode+r' checks=(\d+) failures=0 status=(\d+)\s*$',text,re.M)
        checks=dict(emulator_exit=r.returncode==0,DOS_pass=(folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),self_checks=bool(summary) and int(summary[1])>=7 and int(summary[2])==(77 if mode=='C' else 778) and 'FAIL ' not in text)
        case=dict(mode=mode,passed=all(checks.values()),checks=checks,assertions=int(summary[1]) if summary else None,status=int(summary[2]) if summary else None,artifacts={x.name:sha(x) for x in folder.iterdir() if x.is_file()})
        (folder/'result.json').write_text(json.dumps(case,indent=2)+'\n');cases.append(case);print(mode,'PASS' if case['passed'] else text,flush=True)
    assert all(sha(ROOT/n)==h for n,h in m['sources'].items())
    result=dict(passed=all(c['passed'] for c in cases),cases=cases,sources=m['sources'],products=m['products'],checker_sha256=sha(Path(__file__)),
        scope=m['scope']+' The parent restores the known driver snapshot and INT0 afterward; retained allocations remain until the private DOS VM ends.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
