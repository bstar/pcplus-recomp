#!/usr/bin/env python3
"""Independent production ASPECT.EXE ASIOv3 metadata/preload DOS fixtures.

Expected strings, FIFO order and mapper bytes are authored in definitions(),
before execution. Only owned synthetic records and loopback UART peers are used.
"""
import argparse,hashlib,json,os,shutil,socket,struct,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-script-directory-dos'
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
FIELDS=[('$D_LDATE',61,9),('$D_KBDFILE',95,9),('$D_METAKEY',86,9),
        ('$D_NAME',0,25),('$D_NOTE',105,9),('$D_PHONE',25,21),
        ('$D_PWORD',75,11),('$D_SCRIPT',52,9)]

def definitions():
 normal=[b'20261019',b'KEYSLOTS',b'METABIND',b'NORTH NODE',b'LASTNOTE',b'555-0100',b'SYNTHPASS',b'LOGIN']
 show='integer value\nstring displaybuf\nproc main\n'+''.join('message '+n+'\n' for n,_,_ in FIELDS)+'value = $D_ENTRY\nitoa value displaybuf\nmessage displaybuf\nendproc\n'
 def record(values):
  data=bytearray([0xe7]*114)
  for (_,offset,size),value in zip(FIELDS,values):
   assert len(value)<size and b'\0' not in value
   data[offset:offset+len(value)+1]=value+b'\0'
  return bytes(data)
 cases=[]
 def add(name,source,*,version=3,mode=0,entry=7,values=normal,preload=b'',start=0,port=1,live=b'',tx=b'',returned=b'',mapped=None,stdout=b'',namespace=None,error=0,projection=(0,0,0,0),old_count=None):
  raw=bytearray(record(values))
  if old_count is not None:struct.pack_into('<H',raw,70,old_count)
  cases.append(dict(name=name,source=source,version=version,mode=mode,entry=entry,record=bytes(raw),preload=preload,start=start,port=port,live=live,tx=tx,returned=returned,mapped=returned if mapped is None else mapped,stdout=stdout,namespace=namespace,error=error,projection=projection))
 add('METAALL',show,stdout=b'\r\n'.join(normal)+b'\r\n7\r\n')
 maximum=[bytes([0x80+i])*(size-1) for i,(_,_,size) in enumerate(FIELDS)]
 add('METAMAX',show,entry=200,values=maximum,stdout=b'\r\n'.join(maximum)+b'\r\n200\r\n')
 add('METAEMPTY',show,entry=200,values=[b'']*8,stdout=b'\r\n'*8+b'200\r\n')
 for version in [1,2,3]:
  add('NOENTRY'+str(version),show,version=version,entry=0,stdout=b'\r\n'*8+b'0\r\n')
 add('EXPLICIT', 'proc main\ntransmit $D_PWORD\nendproc\n',tx=b'SYNTHPASS')
 def waiter(needle):
  return ('proc main\nwaitfor "'+needle+'" 2\nif waitfor\ntransmit "READY^M"\n'
          'waitfor "LIVE" 2\nif waitfor\npause 1\nmessage "FOUND"\n'
          'else\nmessage "LIVE FAIL"\nendif\nelse\nmessage "PRELOAD FAIL"\nendif\nendproc\n')
 add('WRAPPED',waiter('LOGIN:'),preload=b'noiseLOGIN:OLD',start=4093,port=2,
     live=b'LIVE\xff\x80TAIL',tx=b'READY\r',returned=b'\xff\x80TAIL',stdout=b'FOUND\r\n')
 add('FULL',waiter('LOGIN:'),entry=200,preload=b'X'*4090+b'LOGIN:',start=2000,port=2,
     live=b'LIVE\xff\x80TAIL',tx=b'READY\r',returned=b'\xff\x80TAIL',stdout=b'FOUND\r\n')
 add('TABLEONCE',waiter('MATCH'),mode=1,preload=b'zATCHOLD',start=4094,
     live=b'LIVEz\xff\x80',tx=b'READY\r',returned=b'z\xff\x80',mapped=b'M\xff\x80',stdout=b'FOUND\r\n')
 add('MASK7',waiter('LOGIN:'),mode=2,preload=bytes(c|128 for c in b'LOGIN:'),start=4095,
     live=bytes(c|128 for c in b'LIVE')+b'\xff\x80z',tx=b'READY\r',returned=b'\xff\x80z',mapped=b'\x7f\0z',stdout=b'FOUND\r\n')
 add('NSONLY','proc main\nmessage "ENV FILE"\nendproc\n',namespace='environment',stdout=b'ENV FILE\r\n')
 add('NSBAD','proc main\nmessage "ENV FILE"\nendproc\n',namespace='current-bad',error=2)
 add('PROJDATE','proc main\nmessage $D_LDATE\nendproc\n',projection=(2026,10,19,1),old_count=65535,stdout=b'10/19/26\r\n')
 add('PROJZERO','proc main\nmessage $D_LDATE\nendproc\n',projection=(2000,2,29,0),old_count=123,stdout=b'02/29/00\r\n')
 return cases

DRIVER=r'''
#include <dos.h>
#include <conio.h>
#include <stdio.h>
#include <string.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#include "serial_handoff.h"
extern unsigned __cdecl parent_table(void);
extern unsigned __cdecl parent_map(unsigned);
extern void __cdecl parent_policy(unsigned);
static aspect_serial_handoff_v3 descriptor;
#define lease descriptor.base
static struct {unsigned before;unsigned char data[4096];unsigned after;} ring;
static unsigned char selected[114],original[114],mcb_before[5],mcb_after[5];
static unsigned settings[10];
static unsigned hardware_before[5],hardware_after[5];
static void hardware(unsigned base,unsigned *s){
 unsigned lcr=inp(base+3);s[0]=lcr;outp(base+3,lcr&127);s[1]=inp(base+1);
 outp(base+3,(lcr&127)|128);s[2]=inp(base);s[3]=inp(base+1);outp(base+3,lcr);s[4]=inp(base+4);
}
static unsigned load(const char *name,void *data,unsigned size){FILE *f=fopen(name,"rb");unsigned ok;if(!f)return 0;ok=fread(data,1,size,f)==size&&fgetc(f)==EOF;return fclose(f)==0&&ok;}
int main(void){
 unsigned psp,ds,i,version,mode,entry,at,count,port,base,irq,mask,mcr,vector_ok,mask_ok,mcr_ok,guard_ok,mcb_ok,hardware_ok;
 int rc,out,err,oldout,olderr;char option[32];FILE *f;union REGS r,s;
 unsigned char *table;unsigned char __far *mcb;void (__interrupt __far *vector)(void);
 if(!load("CONFIG.BIN",settings,sizeof(settings))||!load("RECORD.BIN",selected,114))return 90;
 version=settings[0];mode=settings[1];entry=settings[2];at=settings[3];count=settings[4];port=settings[5];
 if(count>4096)return 91;
 f=fopen("PRELOAD.BIN","rb");if(!f)return 92;
 for(i=0;i<count;++i)ring.data[(at+i)&4095]=(unsigned char)fgetc(f);if(fgetc(f)!=EOF)return 93;fclose(f);
 memcpy(original,selected,114);ring.before=0x1234;ring.after=0x5678;
 r.h.ah=0x62;intdos(&r,&s);psp=s.x.bx;ds=FP_SEG((void __far *)&lease);
 mcb=(unsigned char __far *)MK_FP(psp-1,0);for(i=0;i<5;++i)mcb_before[i]=mcb[i];
 lease.magic=ASIO_MAGIC;lease.version=version;lease.size=version==3?40:28;
 lease.parent_psp=psp;lease.parent_ds=ds;lease.ring=(unsigned)ring.data;lease.capacity=4096;
 lease.count=version==3?count:0;lease.status=version==3?at:0;
 table=(unsigned char *)parent_table();for(i=0;i<256;++i)table[i]=(unsigned char)i;
 if(mode==1){table['z']='M';table['M']='N';}parent_policy(mode);
 lease.reserved0=mode==1?(unsigned)table:0;lease.reserved1=mode;
 descriptor.entry=version==3?entry:0;descriptor.record=descriptor.entry?(unsigned)selected:0;
 if(version==3){descriptor.year=settings[6];descriptor.month=settings[7];descriptor.day=settings[8];descriptor.delta=settings[9];}
 lease.guard=psp^ds^(unsigned)ring.data^ASIO_GUARD;
 if(version>=2)lease.guard^=lease.reserved0^mode;
 if(version==3)lease.guard^=count^at^descriptor.entry^descriptor.record^descriptor.year^descriptor.month^descriptor.day^descriptor.delta;
 sprintf(option,"/S%u:0003:03:N:%04X:%04X",port,ds,(unsigned)&lease);
 base=port==1?0x3f8:0x2f8;irq=port==1?12:11;mcr=inp(base+4);outp(base+4,mcr|1);
 mask=inp(0x21);vector=_dos_getvect(irq);
 hardware(base,hardware_before);
 out=open("STDOUT.BIN",O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 err=open("STDERR.BIN",O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);if(out<0||err<0)return 94;
 oldout=dup(1);olderr=dup(2);if(oldout<0||olderr<0)return 95;
 if(dup2(out,1)||dup2(err,2))return 96;close(out);close(err);
 rc=spawnl(P_WAIT,"ASPECT.EXE","ASPECT","CASE.ASX",option,(char *)0);
 dup2(oldout,1);dup2(olderr,2);close(oldout);close(olderr);
 hardware(base,hardware_after);hardware_ok=!memcmp(hardware_before,hardware_after,sizeof(hardware_before));
 vector_ok=_dos_getvect(irq)==vector;mask_ok=inp(0x21)==mask;mcr_ok=inp(base+4)==(mcr|1);outp(base+4,mcr);
 guard_ok=ring.before==0x1234&&ring.after==0x5678&&!memcmp(original,selected,114);
 for(i=0;i<5;++i)mcb_after[i]=mcb[i];mcb_ok=!memcmp(mcb_before,mcb_after,5);
 f=fopen("RETURN.BIN","wb");if(!f||lease.count>4096)return 97;fwrite(ring.data,1,lease.count,f);fclose(f);
 f=fopen("MAPPED.BIN","wb");if(!f)return 97;for(i=0;i<lease.count;++i)fputc(parent_map(ring.data[i]),f);fclose(f);
 f=fopen("LEASE.BIN","wb");if(!f)return 97;fwrite(&descriptor,1,sizeof(descriptor),f);fclose(f);
 f=fopen("STATUS.TXT","w");if(!f)return 97;
 fprintf(f,"exit=%d vector=%u mask=%u mcr=%u returned=%u count=%u lease=%u guards=%u mcb=%u uart=%u\n",rc,vector_ok,mask_ok,mcr_ok,lease.returned,lease.count,lease.status,guard_ok,mcb_ok,hardware_ok);fclose(f);
 return vector_ok&&mask_ok&&mcr_ok&&hardware_ok&&guard_ok&&mcb_ok&&lease.returned==1&&lease.status==0?0:98;
}
'''
BRIDGE=r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_translate_input,terminal_translation_table,terminal_translation_enabled
extern terminal_translation_mode
global _parent_table,_parent_map,_parent_policy
_parent_table: mov ax,terminal_translation_table
 ret
_parent_map:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 and ax,[uart_rx_mask]
 call terminal_translate_input
 pop bp
 ret
_parent_policy:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [terminal_translation_mode],ax
 xor dx,dx
 cmp ax,1
 jne .not_table
 inc dx
.not_table:
 mov [terminal_translation_enabled],dx
 mov dx,255
 cmp ax,2
 jne .mask
 mov dx,127
.mask: mov [uart_rx_mask],dx
 pop bp
 ret
; Unused loader/full-parser dependencies fail explicitly if reached. The
; actual maintained terminal_translate_input body is linked without replacement.
global _xlt_live_initialize,terminal_receive_character
_xlt_live_initialize:
terminal_receive_character:
 int3
 jmp $
SEGMENT _DATA public class=DATA use16
global terminal_option_mask,terminal_translation_path,process_psp
global terminal_parser_active,terminal_configuration_values,uart_rx_mask
terminal_option_mask: dw 0
terminal_translation_path: times64 db 0
process_psp: dw 0
terminal_parser_active: dw 0
terminal_configuration_values: times44 db 0
uart_rx_mask: dw 255
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack class=STACK use16
GROUP DGROUP _DATA _BSS STACK
'''.replace('times64','times 64').replace('times44','times 44')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build_parent():
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'parent.c').write_text(DRIVER);(OUT/'mapper.asm').write_text(BRIDGE)
 # Supply an explicit DGROUP frame for this C-first diagnostic link. The
 # included real mapper body is unchanged; no replacement mapper is emitted.
 (OUT/'translation-host.asm').write_text('%include "'+str(ROOT/'src/terminal/translation.asm')+'"\nSEGMENT _BSS public class=BSS use16\nSEGMENT STACK stack class=STACK use16\nGROUP DGROUP _DATA _BSS STACK\n')
 for source,target in [(OUT/'mapper.asm',OUT/'mapper.obj'),(OUT/'translation-host.asm',OUT/'translation.obj')]:
  subprocess.run(['nasm','-fobj','-I'+str(ROOT/'src/config')+'/',str(source),'-o',str(target)],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k4096','-I'+str(ROOT/'src/aspect'),'-fe=PARENT.EXE',str(OUT/'parent.c'),str(OUT/'mapper.obj'),str(OUT/'translation.obj')],cwd=OUT,check=True)
 return OUT/'PARENT.EXE'

def run(case,binary,parent):
 folder=OUT/case['name'];folder.mkdir(exist_ok=True)
 for name in ['STATUS.TXT','STDOUT.BIN','STDERR.BIN','RETURN.BIN','MAPPED.BIN','LEASE.BIN','PASS.TXT','FAIL.TXT']:(folder/name).unlink(missing_ok=True)
 shutil.copyfile(binary,folder/'ASPECT.EXE');shutil.copyfile(parent,folder/'PARENT.EXE')
 (folder/'CASE.ASP').write_bytes(case['source'].encode('cp437'));compiled=compile_source(case['source'])
 (folder/'CASE.ASX').unlink(missing_ok=True)
 if case['namespace']:
  (folder/'LIB').mkdir(exist_ok=True);(folder/'LIB/CASE.ASX').write_bytes(compiled)
  if case['namespace']=='current-bad':(folder/'CASE.ASX').write_bytes(b'\xff') # Header must be0..128.
 else:(folder/'CASE.ASX').write_bytes(compiled)
 (folder/'CONFIG.BIN').write_bytes(struct.pack('<10H',case['version'],case['mode'],case['entry'],case['start'],len(case['preload']),case['port'],*case['projection']))
 (folder/'RECORD.BIN').write_bytes(case['record']);(folder/'PRELOAD.BIN').write_bytes(case['preload'])
 wire=bytearray();errors=[];stop=threading.Event();sent=threading.Event()
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(12)
 def peer():
  try:
   connection,_=server.accept()
   with connection:
    connection.settimeout(0.02);connection.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
    while not stop.is_set():
     if case['live'] and not sent.is_set() and b'READY\r' in wire:connection.sendall(case['live']);sent.set()
     try:
      data=connection.recv(4096)
      if not data:break
      wire.extend(data)
     except socket.timeout:pass
  except OSError as e:
   if not stop.is_set():errors.append(str(e))
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 serial='\n'.join(f'serial{n}='+('nullmodem server:127.0.0.1 port:'+str(server.getsockname()[1])+' transparent:1 rxdelay:200 txdelay:1' if n==case['port'] else 'disabled') for n in range(1,5))
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[serial]
{serial}
[autoexec]
@echo off
mount c "{folder}"
c:
{'set PCPLUS=C:'+chr(92)+'LIB' if case['namespace'] else ''}
PARENT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (folder/'dosbox.conf').write_text(config);started=time.monotonic()
 try:
  with (folder/'dosbox.log').open('w') as log:
   subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=20)
 finally:stop.set();server.close();thread.join(1)
 status=(folder/'STATUS.TXT').read_text().strip();stdout=(folder/'STDOUT.BIN').read_bytes();stderr=(folder/'STDERR.BIN').read_bytes()
 returned=(folder/'RETURN.BIN').read_bytes();mapped=(folder/'MAPPED.BIN').read_bytes()
 checks=dict(parent_DOS_pass=(folder/'PASS.TXT').exists() and not(folder/'FAIL.TXT').exists(),
  child_hardware_MCB_ASIO=status==f'exit={case["error"]} vector=1 mask=1 mcr=1 returned=1 count={len(case["returned"])} lease=0 guards=1 mcb=1 uart=1',
  exact_stdout=stdout==case['stdout'],stderr_contract=(b'invalid script header' in stderr if case['error'] else not stderr),exact_wire=bytes(wire)==case['tx'],raw_unread_FIFO=returned==case['returned'],
  actual_parent_mapper=mapped==case['mapped'],live_sent_after_preload_match=sent.is_set() if case['live'] else True,
  record_unchanged=(folder/'RECORD.BIN').read_bytes()==case['record'],no_peer_error=not errors)
 report=dict(name=case['name'],passed=all(checks.values()),checks=checks,status=status,stdout_hex=stdout.hex(),stderr_hex=stderr.hex(),tx_hex=wire.hex(),returned_hex=returned.hex(),mapped_hex=mapped.hex(),expected_stdout_hex=case['stdout'].hex(),expected_tx_hex=case['tx'].hex(),expected_returned_hex=case['returned'].hex(),expected_mapped_hex=case['mapped'].hex(),source_sha256=sha(folder/'CASE.ASP'),asx_sha256=hashlib.sha256(compiled).hexdigest(),runner_sha256=sha(folder/'ASPECT.EXE'),parent_sha256=sha(parent),descriptor_hex=(folder/'LEASE.BIN').read_bytes().hex(),seconds=round(time.monotonic()-started,3),errors=errors)
 (folder/'transmitted.bin').write_bytes(wire);(folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(case['name'],'PASS' if report['passed'] else checks,flush=True)
 return report

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--runner',type=Path,default=ROOT/'build/aspect-runner/ASPECT.EXE');parser.add_argument('--case',action='append');args=parser.parse_args()
 cases=definitions()
 if args.case:
  cases=[c for c in cases if c['name'] in args.case];assert {c['name'] for c in cases}==set(args.case)
 parent=build_parent();digest=sha(args.runner);manifest=args.runner.parent/'manifest.json';assert json.loads(manifest.read_text())['binary_sha256']==digest
 # Serialize authored expectations before the first child is executed.
 (OUT/'expectations.json').write_text(json.dumps([{k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.items()} for c in cases],indent=2)+'\n')
 results=[run(c,args.runner,parent) for c in cases]
 assert sha(args.runner)==digest and all(c['runner_sha256']==digest for c in results)
 report=dict(passed=all(c['passed'] for c in results),cases=results,original_inputs=[],runner_sha256=digest,runner_manifest_sha256=sha(manifest),checker_sha256=sha(Path(__file__)),parent_source_sha256=sha(OUT/'parent.c'),parent_mapper_source_sha256=sha(OUT/'mapper.asm'),mapper_include_sha256=sha(OUT/'translation-host.asm'),actual_mapper_source_sha256=sha(ROOT/'src/terminal/translation.asm'),handoff_header_sha256=sha(ROOT/'src/aspect/serial_handoff.h'),compiler_sha256=sha(ROOT/'src/aspect/compiler.py'),expectations_sha256=sha(OUT/'expectations.json'),scope='Actual source-built production ASPECT child under8086DOS, raw COM1/COM2 IRQ and ASIOv1/v2/v3 retained synthetic parent. Actual maintained parent translation helper linked for unread bytes. No terminal UI, physical modem, original binaries or automatic credential transmission claim.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']
if __name__=='__main__':main()
