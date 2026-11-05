#!/usr/bin/env python3
"""Actual parent capture/snapshot/monitor/history files across direct COMSPEC."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());mode=m['diagnostic_gateway_files_probe'];assert mode in ('normal','hold') and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);package=out/'package';package.mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE');cases=[]
 for name,comspec,status,dos,child,keys in [('direct','D:\\SHELL.COM',0,0,37,''),('changed-CWD','D:\\SHELL.COM',0,0,37,''),('missing','D:\\MISSING.COM',3,2,0,''),('batch','D:\\BAD.BAT',6,0,0,''),('interactive','Z:\\COMMAND.COM',0,0,0,'p1000 m d space W I T N E S S enter p500 c d space T A R G E T enter p500 e x i t enter')]:
  drive=out/name;drive.mkdir();(drive/'TARGET').mkdir();(drive/'BAD.BAT').write_bytes(b'@echo off\r\necho WRONG>D:\\BADRUN.TXT\r\n')
  subprocess.run(['nasm','-fbin',*(['-DCHANGE_CWD'] if name=='changed-CWD' else []),str(ROOT/'standalone/gateway_files_child.asm'),'-o',str(drive/'SHELL.COM')],check=True)
  (drive/'SNAP.ASM').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(drive/'SNAP.ASM'),'-o',str(drive/'SNAP.COM')],check=True)
  cfg=drive/'dosbox.conf';cfg.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
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
set PATH=
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
  with (drive/'dosbox.log').open('w') as log:process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
  raw=(drive/'GFRESULT.BIN').read_bytes() if (drive/'GFRESULT.BIN').exists() else b'';words=struct.unpack_from('<24H',raw) if len(raw)==116 else None
  flags=3 if mode=='hold' else 1;cwd='D:\\TARGET' if name in ('changed-CWD','interactive') else 'D:\\'
  checks=dict(normal_exit=process.returncode==0,probe_success=(drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),report=len(raw)==116,
   direct_result=words is not None and words[:3]==(status,dos,child) and words[4]==status,
   retained_floor=words is not None and words[3]==m['memory_layout']['retained_parent_paragraphs'],
   capture_active_hold_preserved=words is not None and words[5:7]==(flags,flags),
   no_pending_lease=words is not None and words[7:9]==(0,0),
   buffered_capture_flushed=words is not None and words[9:11]==((0 if mode=='hold' else 1),0),
   descriptors_preserved=words is not None and words[11:15]==words[15:19] and words[11:15]==(5,6,7,8),
   all_owners_closed=words is not None and words[19:23]==(65535,)*4,
   all_parent_file_bytes=all((drive/n).exists() and (drive/n).read_bytes()==b'AB' for n in ['CAPTURE.DAT','SNAP.DAT','MONITOR.DAT','HISTORY.DAT']),
   shell_CWD_preserved=words is not None and words[23]==0 and raw[48:].split(b'\0',1)[0].decode('ascii')==cwd,
   startup_CWD_restored=(drive/'AFTERCD.TXT').read_text().strip()=='D:\\',
   hardware_vectors_restored=(drive/'BEFORE.BIN').read_bytes()==(drive/'AFTER.BIN').read_bytes(),
   batch_never_run=not (drive/'BADRUN.TXT').exists(),binary_unchanged=sha(package/'TERMINAL.EXE')==sha(binary))
  if name in ('direct','changed-CWD'):
   child_report=(drive/'CHILD.BIN').read_bytes() if (drive/'CHILD.BIN').exists() else b''
   checks.update(child_cannot_write_close=len(child_report)==64 and struct.unpack('<30H',child_report[:60])==(6,)*30,child_reuses_private_slot=len(child_report)==64 and child_report[60:62]==b'\5\0',empty_CR_tail=len(child_report)==64 and child_report[62:]==b'\0\r',child_file_bytes=(drive/'OWN.DAT').read_bytes()==b'Y')
  else:checks['no_synthetic_child']=not (drive/'CHILD.BIN').exists()
  if name=='interactive':checks['real_shell_commands']=(drive/'WITNESS').is_dir()
  case=dict(case=name,mode=mode,passed=all(checks.values()),checks=checks,report_words=words);cases.append(case)
  print(name,{k:v for k,v in checks.items() if not v},flush=True);assert case['passed'],case
 sources=['standalone/test_gateway_files_dos.py','standalone/gateway_files_probe.c','standalone/gateway_files_probe.asm','standalone/gateway_files_child.asm','standalone/test_terminal.py']
 result=dict(passed=True,binary_sha256=sha(binary),cases=cases,sources={n:sha(ROOT/n) for n in sources},original_inputs=[],scope=__doc__+' Diagnostic invocation before UART startup; actual parent owners and raw DOS EXEC, four open file descriptors, held/enabled capture, real COMMAND.COM and file-position continuation. No Gateway key, active serial or physical modem acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
