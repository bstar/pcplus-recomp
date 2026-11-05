#!/usr/bin/env python3
"""Actual DOS direct-COMSPEC component probe before application UART startup."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['diagnostic_gateway_probe'] and sha(binary)==m['binary_sha256']
 out.mkdir(parents=True);package=out/'package';package.mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE')
 cases=[]
 for name,comspec,path,status,dos,child,keys in [
  ('qualified','D:\\SHELL.COM','',0,0,37,''),('bare-PATH','SHELL.COM','D:\\BIN',0,0,37,''),
  ('extension','D:\\SHELL','',0,0,37,''),('changed-CWD','D:\\SHELL.COM','',0,0,37,''),
  ('missing-COMSPEC','','',5,0,0,''),('invalid-COMSPEC','D:\\MISSING.COM','',3,2,0,''),
  ('batch-COMSPEC','D:\\BAD.BAT','',6,0,0,''),
  ('batch-extension','D:\\BAD','',6,0,0,''),
  ('interactive','Z:\\COMMAND.COM','',0,0,0,'p1000 m d space W I T N E S S enter p500 c d space T A R G E T enter p500 e x i t enter')]:
  assert all(len(t)==1 or t in ('space','enter') or (t.startswith('p') and t[1:].isdigit()) for t in keys.split()),'Unsupported ADDKEY token'
  drive=out/name;drive.mkdir();(drive/'TARGET').mkdir()
  if name.startswith('batch-'):(drive/'BAD.BAT').write_bytes(b'@echo off\r\necho WRONG>D:\\BATFALL.TXT\r\n')
  source=ROOT/'standalone/gateway_shell_fixture.asm';shell=drive/'SHELL.COM'
  subprocess.run(['nasm','-fbin',*(['-DGATEWAY_CHANGE_CWD'] if name=='changed-CWD' else []),str(source),'-o',str(shell)],check=True)
  if name=='bare-PATH':(drive/'BIN').mkdir();shutil.move(shell,drive/'BIN/SHELL.COM')
  sampler=drive/'SNAP.ASM';sampler.write_text(SAMPLER)
  subprocess.run(['nasm','-fbin',str(sampler),'-o',str(drive/'SNAP.COM')],check=True)
  cfg=drive/'dosbox.conf';cfg.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=dummy
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{package}"
mount d "{drive}"
d:
set PCPLUS=
D:\\SNAP B
{'ADDKEY '+keys if keys else ''}
set PATH={path}
set COMSPEC={comspec}
C:\\TERMINAL
if errorlevel 1 goto fail
echo PASS>D:\\PASS.TXT
goto done
:fail
echo FAIL>D:\\FAIL.TXT
:done
cd>D:\\AFTERCD.TXT
D:\\SNAP A
exit
''')
  with (drive/'dosbox.log').open('w') as log:
   result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
  raw=(drive/'GWRESULT.BIN').read_bytes() if (drive/'GWRESULT.BIN').exists() else b''
  record=struct.unpack_from('<4H',raw) if len(raw)==78 else None
  wanted='D:\\TARGET' if name in ('changed-CWD','interactive') else 'D:\\'
  checks=dict(normal_exit=result.returncode==0,probe_wrote_report=len(raw)==78,
   probe_success=(drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),
   direct_result=record is not None and record[:3]==(status,dos,child),
   retained_parent=record is not None and record[3]==m['memory_layout']['retained_parent_paragraphs'],
   independent_current_path=len(raw)==78 and raw[8:76].split(b'\0',1)[0].decode('ascii')==wanted and raw[76:78]==b'\0\0',
   final_startup_CWD_restored=(drive/'AFTERCD.TXT').read_text().strip()=='D:\\',
   hardware_vectors_restored=(drive/'BEFORE.BIN').read_bytes()==(drive/'AFTER.BIN').read_bytes(),binary_unchanged=sha(package/'TERMINAL.EXE')==sha(binary))
  stub=drive/'GWSHELL.BIN'
  if name in ('qualified','bare-PATH','extension','changed-CWD'):checks['exact_empty_CR_tail']=stub.exists() and stub.read_bytes()==b'\0\r'
  else:checks['no_hidden_fallback_child']=not stub.exists()
  if name=='interactive':checks['interactive_commands_executed']=(drive/'WITNESS').is_dir()
  if name.startswith('batch-'):checks['invalid_batch_never_executed']=not (drive/'BATFALL.TXT').exists()
  case=dict(case=name,passed=all(checks.values()),checks=checks,process_result=record,current_path=wanted,dosbox_config_sha256=sha(cfg));cases.append(case)
  (drive/'result.json').write_text(json.dumps(case,indent=2)+'\n');print(name,{k:v for k,v in checks.items() if not v},flush=True);assert case['passed'],case
 sources=('standalone/test_gateway_lookup_dos.py','standalone/gateway_shell_fixture.asm','standalone/test_terminal.py')
 (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,sources={n:sha(ROOT/n) for n in sources},
  scope=__doc__+' Actual source-parent DOS EXEC, empty CR tail and child exit37; real COMMAND.COM/MD/CD/EXIT; source path-session restores startup directory. No Alt-F4 frontend or active UART/file/flow ownership acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
