#!/usr/bin/env python3
"""Audit booted-kernel create/append controls and real critical-error returns."""
import argparse,hashlib,json,re,struct,subprocess,tempfile,zipfile
from pathlib import Path
from build_aspect_process import ROOT,sha

PIN='45b1fa7c52dd996c3bfa5e352ffcd410781b952a6ad629f15a4c9ec4bbaefc5a'
SEED=b'BASELINE\r\n';BODY=b'KERNEL CAPTURE\r\n'
def image_file(image,name):
 return subprocess.run(['mtype','-i',str(image),'::'+name],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def read(path):return json.loads(path.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',action='append',required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 archive=ROOT/'build/freedos-kernel-lab/FD14-FloppyEdition.zip';assert sha(archive)==PIN
 with zipfile.ZipFile(archive) as z:template=z.read('144m/x86BOOT.img')
 assert len(template)==1474560 and template[510:512]==b'\x55\xaa'
 with tempfile.TemporaryDirectory(prefix='kernel-audit-',dir=ROOT/'build/freedos-kernel-lab') as temp:
  original=Path(temp)/'upstream.img';original.write_bytes(template)
  kernel=image_file(original,'KERNEL.SYS');command=image_file(original,'FREEDOS/BIN/COMMAND.COM')
  assert kernel.returncode==command.returncode==0
  upstream=dict(kernel_sha256=hashlib.sha256(kernel.stdout).hexdigest(),command_sha256=hashlib.sha256(command.stdout).hexdigest())
 routes=[];evidence={};seen=set();binaries=set()
 for label in a.label:
  assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
  folder=ROOT/'build/freedos-kernel-lab'/label;report=read(folder/'result.json')
  assert report['passed'] and report['archive_sha256']==PIN
  assert report['boot_template_sha256']==hashlib.sha256(template).hexdigest()
  for n,h in report['sources'].items():assert sha(ROOT/n)==sha(folder/'sources'/n)==h,n
  assert report['checker_sha256']==sha(ROOT/'standalone/test_kernel_critical_dos.py')
  assert report['parent_source_sha256']==sha(ROOT/'standalone/kernel_terminal_parent.c')
  manifest=read(folder/'product/manifest.json')
  assert manifest['terminal_traps'] and manifest['terminal_trap_probe']==0
  binary=folder/'product/TERMINAL.EXE';assert sha(binary)==manifest['binary_sha256']
  assert sha(ROOT/'build/terminal-traps-probe-0/TERMINAL.EXE')==sha(binary)
  binaries.add(sha(binary))
  for case in report['cases']:
   ro=case['write_protected'];operation=case['operation'];key=(operation,ro)
   assert key not in seen;seen.add(key)
   run=folder/('protected' if ro else 'writable');assert case==read(run/'result.json')
   assert case['passed'] and all(case['checks'].values()) and not case['timed_out']
   for n,h in case['files'].items():assert sha(run/n)==h,n
   assert case['binary_sha256']==sha(binary)==sha(run/'TERMINAL.EXE')
   parent=struct.unpack('<8H',(run/'KERNPAR.BIN').read_bytes())
   trap=struct.unpack('<31H',(run/'TRAPWIT.BIN').read_bytes())
   assert list(parent)==case['parent'] and list(trap)==case['trap']
   expected_status=12 if ro and operation=='append' else 16 if ro else 0
   assert parent[0:3]==(0xc724,int(ro),expected_status) and parent[3]>=10 and parent[4]==0
   assert parent[5]==parent[6] and parent[7]==0x070a
   assert trap[0:2]==(0x5452,0) and trap[2]!=0 and trap[3:6]==(0,2 if ro else 0,0)
   assert trap[6]==trap[7]==parent[5] and trap[10]==0 and trap[30]==1
   assert trap[12:18]==trap[18:24]
   if ro:assert trap[8]&0x0800 and trap[8]&255==1 and trap[9]==0
   else:assert trap[8]==trap[9]==0
   snapshot=(run/'CFSNAP.BIN').read_bytes();assert len(snapshot)==98
   state,status,error,close_error,mode,opened,uncertain=struct.unpack_from('<7H',snapshot)
   assert snapshot[32:96].split(b'\0',1)[0]==b'B:\\CRIT.LOG'
   assert mode==(2 if operation=='append' else 1) and not close_error and not uncertain
   if ro and operation=='create':assert (state,status,error,opened)==(3,6,5,0)
   else:assert (state,status,error,opened)==(1,0,0,1)
   end=(run/'CFEND.BIN').read_bytes();assert len(end)==98 and struct.unpack_from('<H',end,96)[0]==0
   fields=struct.unpack_from('<10H3L',end)
   assert end[32:96].split(b'\0',1)[0]==b'B:\\CRIT.LOG' and fields[4]==mode
   if ro and operation=='append':
    assert fields[:4]==(4,9,6,6) and fields[5:9]==(0,1,1,1)
    assert fields[10:13]==(len(SEED),len(BODY),len(SEED)+len(BODY))
   elif ro:assert fields[:4]==(3,6,5,0) and fields[5:9]==(0,0,0,0)
   else:
    assert fields[:4]==(2,0,0,0) and fields[5:9]==(0,0,1,1)
    assert fields[10:13]==(len(SEED) if operation=='append' else 0,len(BODY),(len(SEED) if operation=='append' else 0)+len(BODY))
   assert b'B:\\CRIT.LOG' in (run/'CAPVIEW.BIN').read_bytes()
   wire=(run/'serial.bin').read_bytes()
   assert case['commands']==['ATZ','ATDCaseTest:23'] and b'\x1b[1;16R' in wire and b'\x1b[?1;2c' in wire
   if operation=='append' or not ro:assert case['body_sent'] and b'ready' in wire
   assert len((run/'BEFORE.BIN').read_bytes())==42
   assert (run/'BEFORE.BIN').read_bytes()==(run/'AFTER.BIN').read_bytes()
   assert sha(run/'data.img')==case['media_after_sha256']
   assert (case['media_before_sha256']==case['media_after_sha256'])==ro
   assert sha(run/'boot.img')==case['boot_after_sha256']
   for n,expected in [('KERNEL.SYS',upstream['kernel_sha256']),('FREEDOS/BIN/COMMAND.COM',upstream['command_sha256']),('TERMINAL.EXE',sha(binary)),('TEST.PRM',sha(run/'TEST.PRM'))]:
    result=image_file(run/'boot.img',n);assert result.returncode==0 and hashlib.sha256(result.stdout).hexdigest()==expected,n
   data=image_file(run/'data.img','CRIT.LOG')
   if ro and operation=='create':assert data.returncode!=0
   else:assert data.returncode==0 and data.stdout==(SEED if operation=='append' else b'')+(b'' if ro else BODY)
   routes.append(dict(label=label,operation=operation,write_protected=ro,DOS_status=parent[2],
    critical_AX=trap[8],critical_DI=trap[9],checks=len(case['checks']),parent_assertions=parent[3],
    capture_state=state,capture_status=status,capture_error=error,final_file_state=fields[0],
    final_file_status=fields[1],final_close_error=fields[3],logical_bytes_accepted=fields[11],media_preserved=ro))
   evidence[str(run.relative_to(ROOT))]={n:sha(run/n) for n in ['KERNPAR.BIN','TRAPWIT.BIN','CFSNAP.BIN','CFEND.BIN','CAPVIEW.BIN','BEFORE.BIN','AFTER.BIN','serial.bin','result.json','dosbox.conf']}
 assert seen=={(op,ro) for op in ['create','append'] for ro in [False,True]} and len(binaries)==1
 receipt=dict(passed=True,routes=routes,evidence=evidence,source_binary_sha256=binaries.pop(),
  archive_url='https://download.freedos.org/1.4/FD14-FloppyEdition.zip',archive_sha256=PIN,
  boot_template_sha256=hashlib.sha256(template).hexdigest(),upstream=upstream,
  auditor_sha256=sha(Path(__file__)),
  scope='Booted FreeDOS7.10 from the pinned1.4 distribution, witness-only keyboard client, actual BIOS write-protection INT24 during create/append. No synthetic critical call, kernel patch, proprietary DOS image or product-state injection. No other kernel, physical device, printer or non-Fail critical acceptance claim.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2)+'\n')
 print('Booted-kernel critical-error audit PASS:',len(routes),'routes')
if __name__=='__main__':main()
