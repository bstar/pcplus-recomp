#!/usr/bin/env python3
"""Source-only DOS prefix persistence and explicit filesystem fault checks."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 sub=out/'SUB';sub.mkdir()
 directory=ROOT/'src/directory';persist=ROOT/'src/line_port/persist.c'
 common=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192']
 subprocess.run(common+['-fe=LPREAL.EXE',str(persist),str(directory/'directory_replace.c'),str(directory/'directory_replace_fs.c'),str(ROOT/'standalone/line_port_persist_real.c')],cwd=out,check=True)
 macros=['-d_dos_'+n+'=lp_'+alias for n,alias in [('getfileattr','attr'),('open','open'),('creatnew','create'),('read','read'),('write','write'),('close','close')]]
 subprocess.run(common+['-fe=LPFAULT.EXE',*macros,str(persist),str(directory/'directory_replace.c'),str(ROOT/'standalone/line_port_persist_fault.c')],cwd=out,check=True)
 data=bytes((i*17+3)&255 for i in range(1264));want=bytes(x^0x5a for x in data[:10])+data[10:]
 fixtures={'TEST.PRM':data,'SHORT.PRM':data[:-1],'LONG.PRM':data+b'X','READONLY.PRM':data}
 for name,value in fixtures.items():(sub/name).write_bytes(value)
 (out/'CHECK.BAT').write_text('@echo off\nLPREAL >REAL.TXT\nif errorlevel 1 goto bad\nLPFAULT >FAULT.TXT\nif errorlevel 1 goto bad\necho PASS>PASS.TXT\ngoto done\n:bad\necho FAIL>FAIL.TXT\n:done\nexit\n')
 conf=f'''[sdl]
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
mount c "{out}"
c:
CHECK.BAT
exit
'''
 (out/'dosbox.conf').write_text(conf)
 with (out/'dosbox.log').open('w')as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 logs={n:(out/(n+'.TXT')).read_text() for n in ('REAL','FAULT')if(out/(n+'.TXT')).exists()}
 assert (out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists(),logs
 assert (sub/'TEST.PRM').read_bytes()==want
 for name,value in fixtures.items():
  if name!='TEST.PRM':assert (sub/name).read_bytes()==value,name
 assert not any((sub/n).exists()for n in ('PCPSTG.$$$','PCPBAK.$$$','ABSENT.PRM'))
 names=['src/line_port/persist.c','src/line_port/persist.h','src/directory/directory_replace.c','src/directory/directory_replace.h','src/directory/directory_replace_fs.c','src/directory/directory_replace_fs.h','src/directory/directory_dos.h','standalone/line_port_persist_real.c','standalone/line_port_persist_fault.c','standalone/test_line_port_persist_dos.py']
 counts={n:int(re.search(r'(\d+) checks 0 failures',v)[1])for n,v in logs.items()}
 r=dict(passed=True,original_inputs=[],checks=counts,sources={n:sha(ROOT/n)for n in names},
  binaries={n:sha(out/n)for n in ('LPREAL.EXE','LPFAULT.EXE')},target_sha256=sha(sub/'TEST.PRM'),
  exact_prefix_patch=True,other_fixtures_unchanged=True,recovery_files_absent_after_success=True,
  limitations=['Actual DOSBox-X8086 with authored files; separate declared filesystem fault boundaries.',
   'Caller must supply canonical identity and exclusive file claim; terminal/UI/UART integration remains open.',
   'Replacement is not crash-atomic or externally locked; attributes/timestamps are not preserved.'])
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
 print('Prefix persistence DOS8086:',counts,'all file bytes independently checked')


if __name__=='__main__':main()
