#!/usr/bin/env python3
"""Boot FreeDOS and exercise terminal capture on genuine BIOS-protected media."""
import argparse,hashlib,json,os,re,shutil,socket,struct,subprocess,threading,time,urllib.request,uuid,zipfile
from pathlib import Path
from test_terminal import SAMPLER,ROOT
from modem_fixtures import fixture

URL='https://download.freedos.org/1.4/FD14-FloppyEdition.zip'
ARCHIVE_SHA='45b1fa7c52dd996c3bfa5e352ffcd410781b952a6ad629f15a4c9ec4bbaefc5a'
BODY=b'KERNEL CAPTURE\r\n'
SEED=b'BASELINE\r\n'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(ro,out,binary,archive,frozen,operation):
 out.mkdir(parents=True,exist_ok=False);boot=out/'boot.img';media=out/'data.img'
 with zipfile.ZipFile(archive) as z:boot.write_bytes(z.read('144m/x86BOOT.img'))
 subprocess.run(['mformat','-i',str(media),'-C','-f','1440','::'],check=True)
 if operation=='append':
  (out/'seed.txt').write_bytes(SEED)
  subprocess.run(['mcopy','-i',str(media),str(out/'seed.txt'),'::CRIT.LOG'],check=True)
 before_media=sha(media)
 shutil.copyfile(frozen/'standalone/kernel_terminal_parent.c',out/'kernel_terminal_parent.c')
 shutil.copyfile(binary,out/'TERMINAL.EXE');(out/'TEST.PRM').write_bytes(fixture(timeout=5))
 (out/'sampler.asm').write_text(SAMPLER.replace('D:\\','A:\\'))
 subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(binary.parent/'terminal.map').read_text(),re.M|re.I)}
 layout=json.loads((binary.parent/'manifest.json').read_text())['memory_layout'];data=layout['near_relative_segment']
 seg,off=syms['terminal_trap_critical']
 defines=dict(TRAP_SEG=seg,TRAP_OFF=off,DATA_SEG=data,EXPECTED_KEEP=layout['retained_parent_paragraphs'],PHASE_OFF=syms['terminal_trap_phase'][1],CAPTURE_OFF=syms['_capture_file_result'][1],NOTICE_OFF=syms['_capture_session_notice'][1])
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
  *['-d'+n+'='+str(v) for n,v in defines.items()],'-fe=KERNPAR.EXE',str(out/'kernel_terminal_parent.c')],cwd=out,check=True)
 config='DOS=LOW\r\nFILES=30\r\nBUFFERS=20\r\nLASTDRIVE=B\r\nSHELL=A:\\FREEDOS\\BIN\\COMMAND.COM A:\\FREEDOS\\BIN /E:2048 /P=A:\\FDAUTO.BAT\r\n'
 auto=f'@echo off\r\nA:\\SNAP B\r\nA:\\KERNPAR {int(ro)} @A:\\TEST.PRM /D:CaseTest:23\r\nif errorlevel 1 goto fail\r\necho PASS>A:\\PASS.TXT\r\ngoto done\r\n:fail\r\necho FAIL>A:\\FAIL.TXT\r\n:done\r\nA:\\SNAP S\r\nA:\\SNAP A\r\nA:\\FREEDOS\\BIN\\FDAPM.COM POWEROFF\r\n'
 (out/'FDCONFIG.SYS').write_bytes(config.encode());(out/'FDAUTO.BAT').write_bytes(auto.encode())
 for n in ['FDCONFIG.SYS','FDAUTO.BAT','SNAP.COM','KERNPAR.EXE','TERMINAL.EXE','TEST.PRM']:
  subprocess.run(['mcopy','-o','-i',str(boot),str(out/n),'::'+n],check=True)
 boot_before=sha(boot)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(8)
 wire=bytearray();commands=[];errors=[];stop=threading.Event();body_sent=[];timeline=[]
 def peer():
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(.1);line=bytearray();online=False;typed=bytearray()
    while not stop.is_set():
     try:block=conn.recv(4096)
     except socket.timeout:continue
     if not block:break
     wire.extend(block)
     if online:
      typed.extend(block)
      if b'ready' in typed and not body_sent:conn.sendall(BODY);body_sent.append(True)
      continue
     for byte in block:
      if byte!=13:line.append(byte);continue
      command=bytes(line);line.clear();commands.append(command.decode('ascii','replace'));timeline.append((round(time.monotonic()-started,3),commands[-1]))
      if command==b'ATZ':conn.sendall(b'\r\nOK\r\n')
      elif command==b'ATDCaseTest:23':
       conn.sendall(b'CONNECT\r\n\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c');online=True
  except OSError as e:
   if not stop.is_set():errors.append(str(e))
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 keys='p23000 a-f1 p500 '+' '.join('B:\\CRIT.LOG')+' p1000 enter p4000 r e a d y p4000 a-x'
 cfg=f'''[sdl]
output=surface
[dosbox]
memsize=8
apmbios=true
[cpu]
core=normal
cputype=8086
cycles=fixed 20000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
imgmount a "{boot}" -t floppy
imgmount b "{media}" -t floppy{' -ro' if ro else ''}
ADDKEY {keys}
boot -l a
'''
 (out/'dosbox.conf').write_text(cfg);started=time.monotonic()
 exit_code=-1;timed_out=False
 try:
  with (out/'dosbox.log').open('w') as log:
   result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
   exit_code=result.returncode
 except subprocess.TimeoutExpired:
  timed_out=True
 finally:
  stop.set();server.close();thread.join(2)
 (out/'serial.bin').write_bytes(wire)
 for n in ['KERNPAR.BIN','TRAPWIT.BIN','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','PASS.TXT','FAIL.TXT','CFSNAP.BIN','CFEND.BIN','CAPVIEW.BIN','TERMINAL.EXE','TEST.PRM']:
  r=subprocess.run(['mcopy','-o','-i',str(boot),'::'+n,str(out/n)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if (out/'KERNPAR.BIN').exists() and (out/'KERNPAR.BIN').stat().st_size==16:parent=struct.unpack('<8H',(out/'KERNPAR.BIN').read_bytes())
 else:parent=None
 trap=struct.unpack('<31H',(out/'TRAPWIT.BIN').read_bytes()) if (out/'TRAPWIT.BIN').exists() and (out/'TRAPWIT.BIN').stat().st_size==62 else None
 content=subprocess.run(['mtype','-i',str(media),'::CRIT.LOG'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 expected_file=SEED if ro and operation=='append' else (SEED if operation=='append' else b'')+BODY
 file_ok=content.returncode!=0 if ro and operation=='create' else content.returncode==0 and content.stdout==expected_file
 checks=dict(APM_exit=not timed_out and exit_code==0,independent_DOS_parent=parent is not None and parent[0]==0xc724 and parent[4]==0,
  real_FreeDOS=parent is not None and parent[7]==0x070a,kernel_child_status=parent is not None and parent[2]==(12 if operation=='append' and ro else 16 if ro else 0),
  parent_PASS=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
  trap_owner_closed=trap is not None and trap[3]==0 and trap[4]==(2 if ro else 0),
  protected_image_unchanged=sha(media)==before_media if ro else sha(media)!=before_media,
  file_outcome=file_ok,
  actual_modem_dial=commands==['ATZ','ATDCaseTest:23'],no_peer_errors=not errors,
  actual_CPR=b'\x1b[1;16R' in wire,actual_DA=b'\x1b[?1;2c' in wire,
  hardware_restored=(out/'BEFORE.BIN').exists() and (out/'AFTER.BIN').exists() and (out/'BEFORE.BIN').stat().st_size==42 and (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes(),
  binary_unchanged=sha(out/'TERMINAL.EXE')==sha(binary),PRM_unchanged=(out/'TEST.PRM').read_bytes()==fixture(timeout=5))
 report=dict(passed=all(checks.values()),write_protected=ro,operation=operation,checks=checks,parent=parent,trap=trap,
  commands=commands,command_timeline=timeline,errors=errors,seconds=round(time.monotonic()-started,3),body_sent=bool(body_sent),
  binary_sha256=sha(binary),media_before_sha256=before_media,media_after_sha256=sha(media),
  boot_before_sha256=boot_before,boot_after_sha256=sha(boot),timed_out=timed_out,
  files={n.name:sha(n) for n in out.iterdir() if n.is_file() and n.suffix.lower()!='.img'},
  scope='Booted FreeDOS kernel and genuine BIOS write-protection failure; no synthetic INT24 or product-state injection. Loopback modem, not physical hardware.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(out.name,'PASS' if report['passed'] else report,flush=True)
 return report
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',default='kernel-'+uuid.uuid4().hex)
 p.add_argument('--operation',choices=['create','append'],default='create')
 p.add_argument('--case',choices=['writable','protected']);a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
 folder=ROOT/'build/freedos-kernel-lab'/a.label;folder.mkdir(parents=True,exist_ok=False)
 archive=ROOT/'build/freedos-kernel-lab/FD14-FloppyEdition.zip'
 if not archive.exists() or sha(archive)!=ARCHIVE_SHA:
  candidate=archive.with_name('download-'+uuid.uuid4().hex+'.zip')
  with urllib.request.urlopen(URL,timeout=45) as response:candidate.write_bytes(response.read())
  assert sha(candidate)==ARCHIVE_SHA,'FreeDOS archive does not match the pinned upstream checksum'
  candidate.replace(archive)
 assert sha(archive)==ARCHIVE_SHA
 producer=ROOT/'build/terminal-traps-probe-0/TERMINAL.EXE'
 manifest=json.loads((producer.parent/'manifest.json').read_text());assert manifest['terminal_traps'] and manifest['terminal_trap_probe']==0
 assert manifest['binary_sha256']==sha(producer)
 names=['test_kernel_critical_dos.py','kernel_terminal_parent.c','test_terminal.py','modem_fixtures.py','terminal_config_fixtures.py']
 sources={**manifest['sources'],**{'standalone/'+n:sha(ROOT/'standalone'/n) for n in names}}
 frozen=folder/'sources'
 for n,h in sources.items():
  assert sha(ROOT/n)==h,n
  target=frozen/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
 product=folder/'product';product.mkdir()
 for n in ['TERMINAL.EXE','terminal.map','manifest.json']:shutil.copyfile(producer.parent/n,product/n)
 binary=product/'TERMINAL.EXE'
 with zipfile.ZipFile(archive) as z:boot_template_sha=hashlib.sha256(z.read('144m/x86BOOT.img')).hexdigest()
 cases=[run(ro,folder/('protected' if ro else 'writable'),binary,archive,frozen,a.operation) for ro in [False,True] if a.case is None or a.case==('protected' if ro else 'writable')]
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 assert sha(producer)==manifest['binary_sha256']
 report=dict(passed=all(c['passed'] for c in cases),cases=cases,archive_url=URL,archive_sha256=ARCHIVE_SHA,
  boot_template_sha256=boot_template_sha,checker_sha256=sha(Path(__file__)),parent_source_sha256=sha(ROOT/'standalone/kernel_terminal_parent.c'),sources=sources)
 (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
