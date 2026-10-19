#!/usr/bin/env python3
"""Actual 8086 DOS child RPC lifecycle fixture; no parser/query emulation.

The endpoint is deliberately only a BEGIN/EMIT/END and callback ABI oracle.
Actual parent renderer composition is independently tested by the parent suite.
"""
import hashlib,json,os,shutil,socket,struct,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-render-client-dos'
sys.path.insert(0,str(ROOT/'src/aspect'));from compiler import compile_source
ASM=r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _endpoint_offset,_endpoint_segment,_endpoint_result,_endpoint_read,_endpoint_config
_endpoint_offset: mov ax,endpoint
 ret
_endpoint_segment: mov ax,cs
 ret
_endpoint_config:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [cs:reject_begin],ax
 pop bp
 ret
_endpoint_result:
 push bp
 mov bp,sp
 push bx
 mov bx,[bp+4]
 shl bx,1
 mov ax,[cs:results+bx]
 pop bx
 pop bp
 ret
_endpoint_read:
 push bp
 mov bp,sp
 push bx
 mov bx,[bp+4]
 xor ax,ax
 mov al,[cs:bytes+bx]
 pop bx
 pop bp
 ret
endpoint:
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 cmp ax,0
 je .begin
 cmp ax,1
 je .emit
 cmp ax,2
 je .end
 cmp ax,4
 je .policy
 cmp ax,7
 je .keyboard_policy
 cmp ax,6
 je .label
 mov ax,10
 jmp .return
.label:
 xor si,si
.label_byte:
 mov bx,si
 mov ax,7
 call far [cs:callback]
 cmp ax,255
 ja .bad
 or ax,ax
 jz .label_done
 inc si
 cmp si,13
 jb .label_byte
 jmp .bad
.label_done:
 xor ax,ax
 jmp .return
.policy:
 or bx,bx
 jnz .bad
 mov ax,6
 mov bx,350
 call far [cs:callback]
 jmp .return
.keyboard_policy:
 or bx,bx
 jnz .bad
 mov ax,8
 xor bx,bx
 call far [cs:callback]
 jmp .return
.begin:
 inc word [cs:results]
 cmp word [cs:reject_begin],1
 je .denied
 cmp word [bx],0x5243
 jne .bad
 cmp word [bx+2],5
 jne .bad
 cmp word [bx+4],0x7123
 jne .bad
 mov ax,[bx+6]
 mov [cs:callback],ax
 mov ax,[bx+8]
 mov [cs:callback+2],ax
 xor ax,ax
 jmp .return
.denied: mov ax,14
 jmp .return
.emit:
 inc word [cs:results+2]
 mov si,[cs:results+6]
 cmp si,512
 jae .bad
 mov [cs:bytes+si],bl
 inc word [cs:results+6]
 cmp word [cs:reject_begin],3
 jne .okay
 cmp bl,'A'
 jne .okay
 cmp word [cs:results+16],0
 jne .okay
 ; One explicit fixture byte requests actual callback operations. No escape
 ; sequence recognizer, terminal parser or generated reply is present here.
 mov ax,5
 xor bx,bx
 call far [cs:callback]
 mov [cs:results+8],ax
 mov ax,1
 call far [cs:callback]
 mov [cs:results+10],ax
 mov ax,5
 call far [cs:callback]
 mov [cs:results+12],ax
 mov ax,2
 mov bx,'R'
 call far [cs:callback]
 mov [cs:results+14],ax
 ; IF=0 and DF=1 must survive the far callback exactly. POLL performs no
 ; DOS operation and actual child code restores the original parent frame.
 pushf
 cli
 std
 mov ax,3
 call far [cs:callback]
 pushf
 pop dx
 and dx,0x600
 cmp dx,0x400
 jne .flag_bad
 inc word [cs:results+16]
.flag_bad:
 popf
 mov ax,4
 call far [cs:callback]
 mov [cs:results+18],ax
.okay: xor ax,ax
 jmp .return
.end: inc word [cs:results+4]
 xor ax,ax
 jmp .return
.bad: mov ax,10
.return:
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 popf
 retf
callback: dw 0,0
reject_begin: dw 0
results: times 10 dw 0
bytes: times 512 db 0
SEGMENT _DATA public class=DATA use16
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack class=STACK use16
GROUP DGROUP _DATA _BSS STACK
'''
DRIVER=r'''
#include <dos.h>
#include <conio.h>
#include <process.h>
#include <stdio.h>
#include <string.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#include "serial_handoff.h"
static aspect_serial_handoff_v4 descriptor;
static struct {unsigned before;unsigned char bytes[4096];unsigned after;} ring;
extern unsigned __cdecl endpoint_offset(void),endpoint_segment(void),endpoint_result(unsigned),endpoint_read(unsigned);
extern void __cdecl endpoint_config(unsigned);
static void hardware(unsigned *s){unsigned char l=inp(0x3fb);s[0]=l;s[1]=inp(0x3f9);s[2]=inp(0x3fc);s[3]=inp(0x21);outp(0x3fb,l|128);s[4]=inp(0x3f8);s[5]=inp(0x3f9);outp(0x3fb,l);}
int main(int argc,char **argv){
 unsigned psp,ds,i,mcr,mode=0,before[6],after[6],ok,rc;char option[32];FILE *f;
 union REGS r,s;int o,e,oo,ee;void (__interrupt __far *vec)(void);
 unsigned char mcbcopy[5],__far *mcb;
 if(argc>1)mode=(unsigned)(argv[1][0]-'0');
 r.h.ah=0x62;intdos(&r,&s);psp=s.x.bx;ds=FP_SEG((void __far *)&descriptor);
 mcb=(unsigned char __far *)MK_FP(psp-1,0);for(i=0;i<5;++i)mcbcopy[i]=mcb[i];
 descriptor.base.base.magic=ASIO_MAGIC;descriptor.base.base.version=4;descriptor.base.base.size=48;
 descriptor.base.base.parent_psp=psp;descriptor.base.base.parent_ds=ds;descriptor.base.base.ring=(unsigned)ring.bytes;descriptor.base.base.capacity=4096;
 ring.before=0x1357;ring.after=0x2468;ring.bytes[0]='Z';descriptor.base.base.count=1;
 if(mode==3){ring.bytes[0]='A';ring.bytes[1]='Z';descriptor.base.base.count=2;}
 descriptor.render_offset=endpoint_offset();descriptor.render_segment=endpoint_segment();descriptor.render_token=0x7123;descriptor.render_version=ASPECT_RENDER_CAP_VERSION;
 if(mode==2)descriptor.render_token=0;
 descriptor.base.base.guard=psp^ds^(unsigned)ring.bytes^ASIO_GUARD^descriptor.base.base.count^descriptor.render_offset^descriptor.render_segment^descriptor.render_token^descriptor.render_version;
 endpoint_config(mode);sprintf(option,"/S1:0003:03:N:%04X:%04X",ds,(unsigned)&descriptor);
 mcr=inp(0x3fc);outp(0x3fc,mcr|1);hardware(before);vec=_dos_getvect(12);
 o=open("OUT.BIN",O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);e=open("ERR.BIN",O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);oo=dup(1);ee=dup(2);dup2(o,1);dup2(e,2);close(o);close(e);
 rc=spawnl(P_WAIT,"ASPECT.EXE","ASPECT","CASE.ASX",option,(char *)0);
 dup2(oo,1);dup2(ee,2);close(oo);close(ee);
 hardware(after);ok=!memcmp(before,after,sizeof(before))&&vec==_dos_getvect(12)&&ring.before==0x1357&&ring.after==0x2468;
 for(i=0;i<5;++i)if(mcbcopy[i]!=mcb[i])ok=0;
 outp(0x3fc,mcr);
 f=fopen("RESULT.BIN","wb");if(!f)return 91;
 fwrite(&rc,2,1,f);fwrite(&ok,2,1,f);fwrite(&descriptor,1,48,f);
 for(i=0;i<10;++i){unsigned value=endpoint_result(i);fwrite(&value,2,1,f);}
 for(i=0;i<endpoint_result(3);++i)fputc(endpoint_read(i),f);fclose(f);
 return ok?0:92;
}
'''
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);binary=ROOT/'build/aspect-runner/ASPECT.EXE';digest=sha(binary)
 (OUT/'parent.c').write_text(DRIVER);(OUT/'endpoint.asm').write_text(ASM)
 subprocess.run(['nasm','-fobj',str(OUT/'endpoint.asm'),'-o',str(OUT/'endpoint.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-I'+str(ROOT/'src/aspect'),'-fe=PARENT.EXE',str(OUT/'parent.c'),str(OUT/'endpoint.obj')],cwd=OUT,check=True)
 cases=[]
 for name,mode,source,expected in [
  ('message',0,'proc main\nmessage "HELLO"\nendproc\n',0),
  ('callback',3,'integer value\nproc main\ncomgetc value\npause 2\nendproc\n',0),
  ('error-render',0,'proc main\nmessage "BEFORE"\nendproc\n',1),
  ('denied',1,'proc main\nmessage "NEVER"\nendproc\n',14),
  ('invalid-token',2,'proc main\nmessage "NEVER"\nendproc\n',14)]:
  folder=OUT/name;folder.mkdir(exist_ok=True)
  for n in ['RESULT.BIN','OUT.BIN','ERR.BIN','PASS.TXT','FAIL.TXT']:(folder/n).unlink(missing_ok=True)
  shutil.copyfile(binary,folder/'ASPECT.EXE');shutil.copyfile(OUT/'PARENT.EXE',folder/'PARENT.EXE')
  (folder/'CASE.ASX').write_bytes(compile_source(source))
  if name=='error-render':(folder/'CASE.ASX').unlink()
  server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(12);wire=bytearray();stop=threading.Event();errors=[]
  def peer():
   try:
    c,_=server.accept()
    with c:
     c.settimeout(.05)
     while not stop.is_set():
      try:
       b=c.recv(4096)
       if not b:break
       wire.extend(b)
      except socket.timeout:pass
   except OSError as e:
    if not stop.is_set():errors.append(str(e))
  t=threading.Thread(target=peer,daemon=True);t.start()
  config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[serial]\nserial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1\nserial2=disabled\nserial3=disabled\nserial4=disabled\n[autoexec]\n@echo off\nmount c "{folder}"\nc:\nPARENT {mode}\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n'''
  (folder/'dosbox.conf').write_text(config)
  try:
   with (folder/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=20,check=True)
  finally:
   t.join(.2);stop.set();server.close();t.join(2)
  (folder/'wire.bin').write_bytes(wire)
  assert not errors,errors
  data=(folder/'RESULT.BIN').read_bytes();rc,ok=struct.unpack_from('<2H',data);lease=struct.unpack_from('<I22H',data,4);results=struct.unpack_from('<10H',data,52);emitted=data[72:]
  stdout=(folder/'OUT.BIN').read_bytes();stderr=(folder/'ERR.BIN').read_bytes()
  checks={'exit':rc==expected,'hardware-vector-PIC-MCB-ring':ok==1,'DOS-pass':(folder/'PASS.TXT').exists()}
  if mode in (0,3):
   checks.update(begin=results[0]==1,end=results[2]==1,stderr_empty=not stderr,stdout_empty=not stdout,handback=lease[10]==1 and lease[8]==0)
   if name=='callback':checks.update(raw_unread_raw=results[4:7]==(90,0,90),send_poll_error=results[7:10]==(0,1,0),wire=bytes(wire)==b'R',message=emitted==b'A')
   elif name=='message':checks['native_idle_then_message']=emitted==b'ZHELLO\r\n'
   else:checks['bounded_error']=emitted.startswith(b'ASPECT: cannot open script (error 1,') and emitted.endswith(b')\r\n') and len(emitted)<192
  elif mode==1:checks.update(begin=results[0]==1,noemit=results[1]==0,end=results[2]==0,restored_handback=lease[10]==1 and lease[8]==4)
  else:checks.update(noRPC=results[:3]==(0,0,0),not_adopted=lease[10]==0)
  result=dict(case=name,checks=checks,passed=all(checks.values()),exit=rc,results=results,emitted_hex=emitted.hex(),wire_hex=wire.hex())
  cases.append(result);print(json.dumps(result),flush=True)
 report=dict(binary_sha256=digest,checker_sha256=sha(__file__),manifest_sha256=sha(ROOT/'build/aspect-runner/manifest.json'),original_inputs=[],regression_history=[{'path':'build/aspect-render-client-history/label-cap4-pacing-limit-diagnosis','reason':'Both pre-label and label builds hit bounded pacing5 at unconstrained max cycles during native end-wait. Fixed12000 is an explicit supported clock fixture; one-shot callback stimulus prevents error rendering from replacing first results.'},{'path':'build/aspect-render-client-history/pre-WHEN-idle-C9-fixture','reason':'Old MESSAGE callback fixture assumed no native8E20 idle drain; frozenWHEN integration correctly drained preloadZ before MESSAGE.'}],cases=cases,passed=all(c['passed'] for c in cases),limitations=['Lifecycle/callback endpoint fixture only; not a terminal parser, query recognizer or full parent engine proof. COMGETC C9 bypasses native idle drain to expose the queuedZ to callback read/unread/read; plain MESSAGE expects native idle leadZ first.','Actual DOSBox-X 8086 COM1 virtual UART and loopback only; native hardware untested.'])
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert sha(binary)==digest;assert report['passed']
if __name__=='__main__':main()
