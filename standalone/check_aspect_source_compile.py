#!/usr/bin/env python3
"""Real production interpreter/compiler EXEC, namespace and fault isolation."""
import json,os,shutil,subprocess,sys
from pathlib import Path
from build_aspect_runner import ROOT,sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
OUT=ROOT/'build/aspect-source-compile'
HARNESS=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
static unsigned checks,failures,cases;
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL check%u\n",checks);}}
static void run(const char *name,const char *path,unsigned expected){
 int fd,err,save,saveerr,result;char output[16];unsigned psp;
 void (__interrupt __far *zero)(void),(__interrupt __far *brk)(void),(__interrupt __far *critical)(void);
 union REGS inregs,outregs;inregs.h.ah=0x62;intdos(&inregs,&outregs);psp=outregs.x.bx;
 zero=_dos_getvect(0);brk=_dos_getvect(0x23);critical=_dos_getvect(0x24);fflush(stdout);
 sprintf(output,"%s.OUT",name);fd=open(output,O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 sprintf(output,"%s.ERR",name);err=open(output,O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
 ck(fd>=0&&err>=0);save=dup(1);saveerr=dup(2);ck(save>=0&&saveerr>=0);
 ck(dup2(fd,1)==0&&dup2(err,2)==0);close(fd);close(err);
 result=spawnl(P_WAIT,"ASPECT.EXE","ASPECT",path,(char *)0);
 ck(dup2(save,1)==0&&dup2(saveerr,2)==0);close(save);close(saveerr);
 ck(result==expected);ck(_dos_getvect(0)==zero);ck(_dos_getvect(0x23)==brk);ck(_dos_getvect(0x24)==critical);
 inregs.h.ah=0x62;intdos(&inregs,&outregs);ck(outregs.x.bx==psp);++cases;
 printf("SOURCE %s exit%d expected%u\n",name,result,expected);
}
int main(void){
 putenv("PCPLUS=C:\\LIB");
'''

def main():
 OUT.mkdir(exist_ok=True);folder=OUT/'tests';folder.mkdir(exist_ok=True)
 for leaf,path in [('ASPECT.EXE','aspect-runner/ASPECT.EXE'),('ASPCOMP.EXE','aspect-compiler-dos/ASPCOMP.EXE')]:shutil.copyfile(ROOT/'build'/path,folder/leaf)
 (folder/'LIB').mkdir(exist_ok=True);(folder/'SUB').mkdir(exist_ok=True);(folder/'DIR.ASP').mkdir(exist_ok=True)
 definitions=[('DIRECT','DIRECT.ASP','proc main\nmessage "direct"\nendproc\n',b'direct\r\n'),
              ('DEFAULT','DEFAULT.ASX','proc main\nmessage "fallback"\nendproc\n',b'fallback\r\n'),
              ('NOEXT','NOEXT','proc main\nmessage "no extension"\nendproc\n',b'no extension\r\n'),
              ('PCONLY','PCONLY.ASX','proc main\nmessage "PCPLUS source"\nendproc\n',b'PCPLUS source\r\n'),
              ('QUALIFY','SUB\\QUALIFY.ASP','proc main\nmessage "subdirectory"\nendproc\n',b'subdirectory\r\n')]
 program=HARNESS;expected={};sources={}
 for name,path,source,out in definitions:
  relative=('LIB/'+name if name=='PCONLY' else 'SUB/'+name if name=='QUALIFY' else name)
  (folder/(relative+'.ASP')).write_bytes(source.encode('cp437'));(folder/(relative+'.ASX')).unlink(missing_ok=True);sources[relative]=source
  program+=f' run("{name}",{json.dumps(path)},0);\n';expected[name]=out
 relative='SUB/'+'/'.join(['ABCDEFGH']*7)+'/LONGFILE';long_source='proc main\nmessage "long path"\nendproc\n'
 (folder/relative).parent.mkdir(parents=True,exist_ok=True);(folder/(relative+'.ASP')).write_text(long_source);(folder/(relative+'.ASX')).unlink(missing_ok=True)
 long_path=(relative+'.ASP').replace('/','\\');assert len(long_path)==79
 program+=f' run("LONGPATH",{json.dumps(long_path)},0);\n';expected['LONGPATH']=b'long path\r\n';sources[relative]=long_source
 old=compile_source('proc main\nmessage "OLD"\nendproc\n')
 good='proc main\nmessage "NEW"\nendproc\n'
 for name in ('EXIST','BADHEAD','BAD','PCPREF','ABSENT','BROKEN'):
  (folder/(name+'.ASX')).unlink(missing_ok=True)
 (folder/'EXIST.ASX').write_bytes(old);(folder/'EXIST.ASP').write_text('INVALID');program+=' run("EXIST","EXIST.ASX",0);\n';expected['EXIST']=b'OLD\r\n'
 (folder/'BADHEAD.ASX').write_bytes(b'\x81');(folder/'BADHEAD.ASP').write_text(good);program+=' run("BADHEAD","BADHEAD.ASX",2);\n';expected['BADHEAD']=b''
 (folder/'BAD.ASX').write_bytes(old);(folder/'BAD.ASP').write_text('proc main\nunknown\nendproc\n');program+=' run("BAD","BAD.ASP",5);\n'
 (folder/'PCPREF.ASP').write_text('INVALID');(folder/'LIB/PCPREF.ASX').write_bytes(old);program+=' run("PCPREF","PCPREF.ASX",0);\n';expected['PCPREF']=b'OLD\r\n'
 for name,path in [('ABSENT','ABSENT.ASX'),('DEVICE','CON.ASP'),('DIR','DIR.ASP')]:program+=f' run("{name}","{path}",{64 if name=="DEVICE" else 1});\n';expected[name]=b''
 program+=' ck(rename("ASPCOMP.EXE","SAVED.EXE")==0);run("NOCOMP","DIRECT.ASP",1);ck(rename("SAVED.EXE","ASPCOMP.EXE")==0);\n';expected['NOCOMP']=b''
 chain='integer value,saved\nstring filename\nproc main\nvalue=42\nset break 1234\nfilename="END.ASP"\nexecute filename\nmessage "BAD"\nendproc\n'
 end='integer value,saved\nstring payload\nproc main\nfetch break saved\nif value==42 && saved==1234\nmessage "state retained"\nendif\nmessage payload\nendproc\n'
 (folder/'CHAIN.ASX').write_bytes(compile_source(chain));(folder/'END.ASP').write_text(end);(folder/'END.ASX').unlink(missing_ok=True);sources['END']=end
 program+=' run("CHAIN","CHAIN.ASX",0);\n';expected['CHAIN']=b'state retained\r\n\r\n'
 # A large-model child deliberately faults with DS!=SS. Its inherited neutral
 # vector must terminate that PSP, then the interpreter must return normally.
 fault=r'''#include <stdio.h>
#include <dos.h>
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify exact [ax];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify exact [ax];
static void fault(void);
#pragma aux fault = "mov ax,ds" "add ax,16" "mov ds,ax" "xor ax,ax" "div ax" modify exact [ax dx];
int main(void){FILE *f;unsigned values[2];values[0]=data_segment()+16;values[1]=stack_segment();f=fopen("FAULTCTX.BIN","wb");if(!f)return 98;fwrite(values,2,2,f);fclose(f);fault();return 97;}
'''
 (folder/'fault.c').write_text(fault)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k4096','-fe=FAULT.EXE',str(folder/'fault.c')],cwd=folder,check=True)
 program+=' ck(rename("ASPCOMP.EXE","SAVED.EXE")==0);ck(rename("FAULT.EXE","ASPCOMP.EXE")==0);run("FAULT","DIRECT.ASP",12);ck(rename("ASPCOMP.EXE","FAULT.EXE")==0);ck(rename("SAVED.EXE","ASPCOMP.EXE")==0);\n';expected['FAULT']=b''
 arithmetic='integer a,b,result\nproc main\na=-32768\nb=-1\nresult=a/b\nendproc\n'
 leak_bytes=compile_source(arithmetic);(folder/'LEAK.ASP').write_text(arithmetic);(folder/'LEAK.ASX').unlink(missing_ok=True)
 leak=r'''#include <stdio.h>
#include <string.h>
#include <dos.h>
static void badterminate(void);
#pragma aux badterminate = "mov ax,0x4c63" "int 0x21" modify exact [ax];
static void __interrupt __far leaked(void){badterminate();}
static void terminate(void);
#pragma aux terminate = "mov ax,0x4c00" "int 0x21" modify exact [ax];
static unsigned char data[]={BYTES};
int main(int argc,char **argv){char target[128];FILE *f;if(argc!=2)return 96;strcpy(target,argv[1]);target[strlen(target)-1]='X';f=fopen(target,"wb");if(!f)return 95;if(fwrite(data,1,sizeof(data),f)!=sizeof(data)||fclose(f))return 94;_dos_setvect(0,leaked);terminate();return 97;}
'''.replace('BYTES',','.join(str(b) for b in leak_bytes))
 (folder/'leak.c').write_text(leak)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k4096','-fe=LEAKER.EXE',str(folder/'leak.c')],cwd=folder,check=True)
 program+=' ck(rename("ASPCOMP.EXE","SAVED.EXE")==0);ck(rename("LEAKER.EXE","ASPCOMP.EXE")==0);run("LEAK","LEAK.ASP",12);ck(rename("ASPCOMP.EXE","LEAKER.EXE")==0);ck(rename("SAVED.EXE","ASPCOMP.EXE")==0);\n';expected['LEAK']=b''
 (folder/'CANCEL.ASP').write_text(good);(folder/'CANCEL.ASX').unlink(missing_ok=True)
 program+=' _disable();*(unsigned __far *)MK_FP(0x40,0x1a)=0x1e;*(unsigned __far *)MK_FP(0x40,0x1c)=0x20;*(unsigned __far *)MK_FP(0x40,0x1e)=0x011b;_enable();run("CANCEL","CANCEL.ASP",13);\n';expected['CANCEL']=b''
 cancel=r'''#include <dos.h>
#include <process.h>
int main(int argc,char **argv){int result;if(argc!=2)return 64;result=spawnl(P_WAIT,"SAVED.EXE","ASPCOMP",argv[1],(char *)0);_disable();*(unsigned __far *)MK_FP(0x40,0x1a)=0x1e;*(unsigned __far *)MK_FP(0x40,0x1c)=0x20;*(unsigned __far *)MK_FP(0x40,0x1e)=0x011b;_enable();return result;}
'''
 (folder/'cancel.c').write_text(cancel);(folder/'AFTER.ASP').write_text(good);(folder/'AFTER.ASX').unlink(missing_ok=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k4096','-fe=CANCEL.EXE',str(folder/'cancel.c')],cwd=folder,check=True)
 program+=' ck(rename("ASPCOMP.EXE","SAVED.EXE")==0);ck(rename("CANCEL.EXE","ASPCOMP.EXE")==0);run("AFTER","AFTER.ASP",13);ck(rename("ASPCOMP.EXE","CANCEL.EXE")==0);ck(rename("SAVED.EXE","ASPCOMP.EXE")==0);\n';expected['AFTER']=b''
 cycle_start='integer counter\nproc main\ncounter=0\nexecute "LOOP.ASP"\nendproc\n'
 cycle='integer counter\nstring payload\nproc main\npayload="owned"\ncounter=counter+1\nif counter<20\nexecute "LOOP.ASP"\nendif\nitoa counter payload\nmessage payload\nendproc\n'
 (folder/'CYCLES.ASX').write_bytes(compile_source(cycle_start));(folder/'LOOP.ASP').write_text(cycle);(folder/'LOOP.ASX').unlink(missing_ok=True)
 multi=r'''#include <stdio.h>
#include <process.h>
int main(int argc,char **argv){FILE *f;unsigned count=0;if(argc!=2)return 64;f=fopen("COMPCNT.BIN","rb");if(f){if(fread(&count,2,1,f)!=1){fclose(f);return 95;}fclose(f);}++count;f=fopen("COMPCNT.BIN","wb");if(!f)return 96;if(fwrite(&count,2,1,f)!=1||fclose(f))return 97;return spawnl(P_WAIT,"SAVED.EXE","ASPCOMP",argv[1],(char *)0);}
'''
 (folder/'multi.c').write_text(multi);(folder/'COMPCNT.BIN').unlink(missing_ok=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k4096','-fe=MULTI.EXE',str(folder/'multi.c')],cwd=folder,check=True)
 program+=' ck(rename("ASPCOMP.EXE","SAVED.EXE")==0);ck(rename("MULTI.EXE","ASPCOMP.EXE")==0);run("CYCLES","CYCLES.ASX",0);ck(rename("ASPCOMP.EXE","MULTI.EXE")==0);ck(rename("SAVED.EXE","ASPCOMP.EXE")==0);\n';expected['CYCLES']=b'20\r\n';sources['LOOP']=cycle
 cp_source='proc main\nmessage "CP437 source"\nendproc\n'
 # Create OEM names through real DOS calls rather than assuming a host Unicode
 # filename mapping. Dump the generated ASX into an ASCII report carrier.
 program+=' {FILE *f=fopen("LIB\\\\\\x82.ASP","wb");ck(f!=0);if(f){fputs('+json.dumps(cp_source)+',f);ck(fclose(f)==0);}}\n'
 program+=' run("PC437","\\x82.ASP",0);\n';expected['PC437']=b'CP437 source\r\n'
 program+=' {FILE *f=fopen("LIB\\\\\\x82.ASX","rb"),*out=fopen("PC437.BIN","wb");int c;ck(f!=0&&out!=0);if(f&&out){while((c=fgetc(f))!=EOF)fputc(c,out);ck(fclose(f)==0&&fclose(out)==0);}}\n'
 program+=' {static unsigned char old[]={'+','.join(str(n) for n in old)+'};FILE *f=fopen("LIB\\\\\\x87.ASX","wb");ck(f!=0);if(f){ck(fwrite(old,1,sizeof(old),f)==sizeof(old));ck(fclose(f)==0);}}\n'
 program+=' run("PC437X","\\x87.ASX",0);\n';expected['PC437X']=b'OLD\r\n'
 program+=' printf("SOURCE_EXEC %u cases %u checks %u failures\\n",cases,checks,failures);return failures?1:0;}\n'
 (folder/'harness.c').write_text(program)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-fe=SOURCET.EXE',str(folder/'harness.c')],cwd=folder,check=True)
 config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{folder}"\nc:\nSOURCET >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
 (folder/'dosbox.conf').write_text(config)
 for n in ('PASS.TXT','FAIL.TXT','RESULT.TXT'):(folder/n).unlink(missing_ok=True)
 with (folder/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=90)
 result=(folder/'RESULT.TXT').read_text();print(result)
 assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),result
 for name,output in expected.items():assert (folder/(name+'.OUT')).read_bytes()==output,(name,(folder/(name+'.OUT')).read_bytes())
 assert b'compile error' in (folder/'BAD.OUT').read_bytes()
 assert (folder/'BAD.ASX').read_bytes()==old and (folder/'BADHEAD.ASX').read_bytes()==b'\x81'
 assert (folder/'LEAK.ASX').read_bytes()==leak_bytes
 assert not (folder/'CANCEL.ASX').exists() and (folder/'AFTER.ASX').read_bytes()==compile_source(good)
 assert (folder/'COMPCNT.BIN').read_bytes()==b'\x14\0'
 assert (folder/'PC437.BIN').read_bytes()==compile_source(cp_source)
 for leaf,source in sources.items():assert (folder/(leaf+'.ASX')).read_bytes()==compile_source(source)
 raw=(folder/'FAULTCTX.BIN').read_bytes();assert len(raw)==4 and raw[:2]!=raw[2:],raw.hex()
 assert not list(folder.rglob('LPC*.LOG'))
 report=dict(passed=True,runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),compiler_sha256=sha(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'),checker_sha256=sha(Path(__file__)),DOS_summary=result.strip().splitlines()[-1],fault_context_hex=raw.hex(),recompilation_cycles=20,test_inputs={n:sha(folder/n) for n in ('harness.c','fault.c','FAULT.EXE','leak.c','LEAKER.EXE','cancel.c','CANCEL.EXE','multi.c','MULTI.EXE','COMPCNT.BIN','PC437.BIN')},original_inputs=[],scope='Actual production interpreter automatically compiles ASP/missing-ASX with original namespace/old-ASX rules, preserves chain state, caller PSP/INT0/23/24 and files, survives a foreign-DS compiler CPU fault and a leaked INT0 vector, cancels before/after compiler EXEC, and completes20 counted real compiler replacements in one invocation. UART/renderer/BBS composition remains separately required.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
