#!/usr/bin/env python3
"""Real DOS8086 path-session lifecycle, far state and explicit fault recovery."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--program',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.program.resolve();out=a.output.resolve();assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);c=out/'c';d=out/'d';c.mkdir();d.mkdir();(c/'ONE/SUB').mkdir(parents=True);(d/'TWO/SUB').mkdir(parents=True)
 (c/'AAAAAAAA/BBBBBBBB/CCCCCCCC/DDDDDDDD/EEEEEEEE/FFFFFFFF/GGGGGGGG').mkdir(parents=True)
 shutil.copyfile(binary,c/'SESSION.EXE')
 modes=[(0,'lifecycle'),(1,'verified-rollback'),(2,'quarantine-native-restore-retry'),(3,'restore-verification-retry'),(5,'bounded-query-startup-retry'),(6,'long-startup-restore')]
 expected_counts={0:25,1:19,2:25,3:20,5:28,6:26}
 commands='\n'.join(f'C:\\SESSION.EXE {mode} >C:\\CASE{mode}.TXT\nif errorlevel 1 goto failed' for mode,_ in modes)
 config=out/'dosbox.conf';config.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{c}"
mount d "{d}"
c:
{commands}
echo PASS>C:\\PASS.TXT
goto done
:failed
echo FAIL>C:\\FAIL.TXT
:done
cd>C:\\FINALCD.TXT
exit
''')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 cases=[]
 for mode,name in modes:
  file=c/f'CASE{mode}.TXT';report=file.read_text() if file.exists() else ''
  match=re.fullmatch(r'PATHSESSION mode=(\d+) checks=(\d+) failures=0 state_segment=([0-9A-F]+) data_segment=([0-9A-F]+)\s*',report)
  passed=bool(match) and int(match[1])==mode and int(match[2])==expected_counts[mode] and match[3]!=match[4]
  cases.append(dict(case=name,mode=mode,passed=passed,report=report,assertions=int(match[2]) if match else 0))
 checks=dict(all_cases=all(c['passed'] for c in cases),normal_exit=(c/'PASS.TXT').exists() and not(c/'FAIL.TXT').exists(),final_directory=(c/'FINALCD.TXT').read_text().strip().upper()=='C:\\',program_unchanged=sha(c/'SESSION.EXE')==sha(binary),sources_unchanged=all(sha(ROOT/n)==h for n,h in m['sources'].items()))
 result=dict(passed=all(checks.values()),checks=checks,cases=cases,assertions=sum(c['assertions'] for c in cases),binary_sha256=sha(binary),state_bytes=m['state_bytes'],source_map_state_vs_DGROUP=[m['state_segment'],m['DGROUP_segment']],sources=m['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Real DOSBox-X8086 CHDIR/default-drive/getcwd on owned C/D directories, mutable code-bank state observed outside DS and far calls with near stack arguments. Query-overflow/verification/native rollback/restore faults are explicit test-only boundary wrappers. No original executable, application foreground/file admission, UI, online UART or physical-machine acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
if __name__=='__main__':main()
