#!/usr/bin/env python3
"""Actual8086DOS ASIOv1/v2 translation snapshots, raw IRQ and raw handback."""
import hashlib,json,os,socket,subprocess,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-serial-translation-dos'
PARENT=r'''
#include <dos.h>
#include <conio.h>
#include <process.h>
#include <stdio.h>
#include <stdlib.h>
#include "serial_handoff.h"
static aspect_serial_handoff lease;
static unsigned char ring[4096],table[256];
int main(int argc,char **argv){
 unsigned psp,ds,i,mode,version,mcr,mask;int rc;char option[32],expected[4];
 union REGS r,s;void (__interrupt __far *vector)(void);
 if(argc!=3)return 90;version=atoi(argv[1]);mode=atoi(argv[2]);
 r.h.ah=0x62;intdos(&r,&s);psp=s.x.bx;ds=FP_SEG((void __far *)&lease);
 lease.magic=ASIO_MAGIC;lease.version=version;lease.size=28;
 lease.parent_psp=psp;lease.parent_ds=ds;lease.ring=(unsigned)ring;lease.capacity=4096;
 lease.reserved0=mode==1?(unsigned)table:0;lease.reserved1=mode;
 lease.guard=psp^ds^(unsigned)ring^ASIO_GUARD^lease.reserved0^mode;
 for(i=0;i<256;++i)table[i]=(unsigned char)(i^0x55);
 sprintf(option,"/S1:0003:03:N:%04X:%04X",ds,(unsigned)&lease);
 sprintf(expected,"%u",mode);
 mcr=inp(0x3fc);outp(0x3fc,mcr|1);mask=inp(0x21);vector=_dos_getvect(12);
 rc=spawnl(P_WAIT,"PROBE.EXE","PROBE",option,expected,(char *)0);
 if(inp(0x3fc)!=(mcr|1)||inp(0x21)!=mask||_dos_getvect(12)!=vector)rc=91;
 outp(0x3fc,mcr);
 if(lease.returned!=1||lease.status||lease.count!=2||ring[0]!=255||ring[1]!=128)rc=92;
 printf("child=%d returned=%u status=%u count=%u raw=%u,%u\n",rc,lease.returned,lease.status,lease.count,ring[0],ring[1]);
 return rc;
}
'''
PROBE=r'''
#include "serial.h"
#include <stdlib.h>
int main(int argc,char **argv){
 unsigned i,c,mode,status;unsigned long start,now;
 static unsigned char raw[4]={0,0x1a,0x80,0xff};
 if(argc!=3)return 80;mode=atoi(argv[2]);status=aspect_serial_open(argv[1]);if(status)return 81;
 if(aspect_serial_translation_policy()!=mode)return 82;
 for(i=0;i<256;++i)if(aspect_serial_translate(i)!=(mode==1?(i^0x55):i))return 83;
 start=aspect_serial_ticks();
 while(aspect_serial_try_write('D')){aspect_serial_poll();if(aspect_serial_ticks()-start>72)return 84;}
 while(aspect_serial_available()<6){
  aspect_serial_poll();now=aspect_serial_ticks();if(now<start)now+=1573040UL;
  if(now-start>72)return 85;
 }
 for(i=0;i<4;++i){c=aspect_serial_read();if(c!=(mode==2?(raw[i]&127):raw[i]))return 86;}
 return aspect_serial_close();
}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'parent.c').write_text(PARENT);(OUT/'probe.c').write_text(PROBE)
 sources=[ROOT/'src/aspect/serial_backend.asm',ROOT/'reconstruction/uart/core.asm',ROOT/'src/uart/api.asm']
 objects=[]
 for i,p in enumerate(sources):
  o=OUT/f'{i}.obj';objects.append(str(o))
  subprocess.run(['nasm','-fobj','-DUART_OMF','-I'+str(ROOT/'reconstruction/uart')+'/',str(p),'-o',str(o)],check=True)
 common=['wcl','-q','-bt=dos','-0','-ms','-s','-os','-k8192','-I'+str(ROOT/'src/aspect')]
 subprocess.run(common+['-fe=PARENT.EXE',str(OUT/'parent.c')],cwd=OUT,check=True)
 subprocess.run(common+['-fe=PROBE.EXE',str(OUT/'probe.c'),str(ROOT/'src/aspect/serial.c'),*objects],cwd=OUT,check=True)
 cases=[]
 for version,mode in [(1,0),(2,0),(2,1),(2,2)]:
  folder=OUT/f'v{version}-mode{mode}';folder.mkdir(exist_ok=True)
  for n in ['PASS.TXT','FAIL.TXT']:(folder/n).unlink(missing_ok=True)
  server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(12)
  wire=bytearray();errors=[]
  def peer():
   try:
    conn,_=server.accept()
    with conn:
     conn.settimeout(12);sent=False
     while True:
      data=conn.recv(4096)
      if not data:break
      wire.extend(data)
      if b'D' in wire and not sent:conn.sendall(bytes([0,0x1a,0x80,0xff,0xff,0x80]));sent=True
   except OSError as e:errors.append(str(e))
  thread=threading.Thread(target=peer);thread.start()
  config=fr'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{OUT}"
mount d "{folder}"
c:
PARENT {version} {mode} >d:\RESULT.TXT
if errorlevel 1 goto fail
echo PASS>d:\PASS.TXT
goto done
:fail
echo FAIL>d:\FAIL.TXT
:done
exit
'''
  (folder/'dosbox.conf').write_text(config)
  with (folder/'dosbox.log').open('w') as log:
   p=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=15)
  thread.join(2);server.close()
  checks=dict(dos_pass=p.returncode==0 and (folder/'PASS.TXT').exists() and not(folder/'FAIL.TXT').exists(),wire_exact=wire==b'D',peer_clean=not errors)
  result=dict(version=version,mode=mode,passed=all(checks.values()),checks=checks,errors=errors,wire_hex=wire.hex(),result=(folder/'RESULT.TXT').read_text())
  (folder/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True);cases.append(result)
 sources += [ROOT/'src/aspect/serial.c',ROOT/'src/aspect/serial.h',ROOT/'src/aspect/serial_handoff.h',Path(__file__).resolve()]
 report=dict(passed=all(c['passed'] for c in cases),cases=cases,original_inputs=[],checker_sha256=sha(Path(__file__)),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},binaries={p.name:sha(p) for p in [OUT/'PARENT.EXE',OUT/'PROBE.EXE']},limitations=['Source-built direct owner diagnostic, not ASPECT interpreter or parent terminal composition.','COM1 virtual UART only; physical devices remain unverified.'])
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']
if __name__=='__main__':main()
