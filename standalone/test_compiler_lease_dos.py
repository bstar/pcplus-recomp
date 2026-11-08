#!/usr/bin/env python3
"""Experimental parent-owned DOS tail lease with real nested ASPCOMP execution.

Two actual DOS PSPs, profile-sized MCBs and byte-checked161152-byte parent tail.
No production parent/UART bridge or physical acceptance is implied.
"""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
from mz_layout import inspect
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
PARENT=r'''
#include <stdio.h>
#include <stdlib.h>
#include <dos.h>
#include <i86.h>
#include "compiler_lease.h"
extern unsigned _psp;
extern unsigned __far __cdecl lease_dos_resize(unsigned,unsigned);
extern int __cdecl aspect_compiler_exec(const char *,const char *,unsigned);
#define FULL 30107U
#define KEEP 20035U
#define TOKEN 18262U
static unsigned mismatch,rounds;
static void tail(unsigned seed,unsigned verify)
{
 unsigned seg,i;unsigned char expected;unsigned char __far *p;
 for(seg=_psp+KEEP;seg<_psp+FULL;++seg){p=MK_FP(seg,0);
  for(i=0;i<16;++i){expected=(unsigned char)(((i&1)?seg>>8:seg)^(i*17)^(seed*29));
   if(verify){if(p[i]!=expected)mismatch=1;}else p[i]=expected;
  }
 }
}
int main(void)
{
 unsigned cycle,status;int result;char args[100];FILE *log;
 void (__interrupt __far *v0)(void),(__interrupt __far *v23)(void),(__interrupt __far *v24)(void);
 log=fopen("RESULT.TXT","w");if(!log)return 1;
 fputs("START\n",log);fclose(log);log=fopen("RESULT.TXT","a");
 v0=_dos_getvect(0);v23=_dos_getvect(0x23);v24=_dos_getvect(0x24);
 if(lease_dos_resize(_psp,FULL)){fputs("RESIZE FAIL\n",log);fclose(log);return 2;}
 fputs("RESIZED\n",log);fclose(log);log=fopen("RESULT.TXT","a");
 status=compiler_lease_init(_psp,KEEP,TOKEN);
 fprintf(log,"INITIALIZED %u\n",status);fclose(log);log=fopen("RESULT.TXT","a");
 if(status){fprintf(log,"INIT FAIL %u\n",status);fclose(log);return 3;}
 for(cycle=0;cycle<3;++cycle){
  fprintf(log,"FILL %u\n",cycle);fclose(log);log=fopen("RESULT.TXT","a");tail(cycle,0);
  fputs("FILLED\n",log);fclose(log);log=fopen("RESULT.TXT","a");
  sprintf(args,"%u %u %u %u %u %u %u %u",_psp,
   FP_SEG(compiler_lease_begin),FP_OFF(compiler_lease_begin),
   FP_SEG(compiler_lease_end),FP_OFF(compiler_lease_end),
   FP_SEG(compiler_lease_info),FP_OFF(compiler_lease_info),TOKEN);
  fprintf(log,"ARGS %s\n",args);fclose(log);log=fopen("RESULT.TXT","a");
  result=aspect_compiler_exec("CLIENT.EXE",args,0);
  fprintf(log,"CHILD %u %d PHASE %u VALID %u DOS %u\n",cycle,result,
   compiler_lease_info(0),compiler_lease_info(3),compiler_lease_info(4));
  if(result || compiler_lease_info(0)!=CL_IDLE || !compiler_lease_info(3)){fclose(log);return 4;}
  tail(cycle,1);++rounds;
 }
 fprintf(log,"RESULT %u %u %u %u\n",rounds,mismatch,
  *(unsigned __far *)MK_FP(_psp-1,3),
  _dos_getvect(0)==v0 && _dos_getvect(0x23)==v23 && _dos_getvect(0x24)==v24);
 fclose(log);return mismatch?5:0;
}
'''
CLIENT=r'''
#include <stdio.h>
#include <stdlib.h>
#include <dos.h>
#include <i86.h>
#include <errno.h>
#include <fcntl.h>
#include <direct.h>
#include <string.h>
#include "compiler_lease.h"
extern unsigned _psp;
extern int __cdecl aspect_compiler_exec(const char *,const char *,unsigned);
typedef unsigned (__far __cdecl *call_fn)(unsigned,unsigned);
typedef unsigned (__far __cdecl *info_fn)(unsigned);
static unsigned current_psp(void);
#pragma aux current_psp = "mov ah,0x51" "int 0x21" "mov ax,bx" value [ax] modify [bx];
static unsigned largest(void);
#pragma aux largest = "mov bx,0xffff" "mov ah,0x48" "int 0x21" "mov ax,bx" value [ax] modify [bx];
#define CK(x) do{unsigned okay=(x);++checks;_dos_write(trace,&checks,2,&trace_count);_dos_close(trace);_dos_open("C:\\TRACE.BIN",O_WRONLY,&trace);if(!okay){failed=__LINE__;goto done;}}while(0)
int main(int argc,char **argv)
{
 unsigned parent,token,max,block=0,checks=0,failed=0,initial,loan_free,restore_error=0,trace_count,prefix=0,partial=0,startseq,j;
 unsigned char jft[20];
 void (__interrupt __far *vectors[3])(void);
 int result,trace=0;call_fn begin,end;info_fn info;char arg[16],name[24];FILE *log,*collision;
 if(argc!=9)return 60;
 parent=atoi(argv[1]);token=atoi(argv[8]);
 begin=(call_fn)MK_FP(atoi(argv[2]),atoi(argv[3]));
 end=(call_fn)MK_FP(atoi(argv[4]),atoi(argv[5]));
 info=(info_fn)MK_FP(atoi(argv[6]),atoi(argv[7]));
 if(_dos_setblock(8539,_psp,&max))return 61;
 _dos_creat("C:\\TRACE.BIN",0,&trace);
 {unsigned i;for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(_psp,0x18+i));}
 vectors[0]=_dos_getvect(0);vectors[1]=_dos_getvect(0x23);vectors[2]=_dos_getvect(0x24);
 initial=largest();loan_free=0;
 result=aspect_compiler_exec("ASPCOMP.EXE","TEST.ASP",0);
 CK(result==-1 && errno==ENOMEM);
 CK(info(0)==CL_IDLE && info(3)==1);
 CK(begin(token+1,_psp)==CL_IDENTITY);
 CK(begin(token,_psp+1)==CL_IDENTITY);
 CK(*(unsigned __far *)MK_FP(parent-1,3)==30107);
 CK(*(unsigned __far *)MK_FP(parent-1,1)==parent);
 CK(begin(token,_psp)==0);
 CK(current_psp()==_psp);
 CK(info(0)==CL_LENT && info(3)==0 && info(1)==30107 && info(2)==20035);
 CK(*(unsigned __far *)MK_FP(parent-1,3)==20035);
 CK(*(unsigned __far *)MK_FP(parent-1,1)==parent);
 CK(begin(token,_psp)==CL_STATE);
 CK(end(token+1,_psp)==CL_IDENTITY);
 loan_free=largest();CK(loan_free>4750);
 sprintf(arg,"%u",info(8));
 CK(aspect_compiler_exec("FDTEST.EXE",arg,0)==0);
 CK(aspect_compiler_exec("ASPCOMP.EXE","TEST.ASP",0)==0);
 /* Occupy the released parent's next block. Failed grow must retain backup,
  * actual smaller size and invalid-tail state until this owner retries. */
 CK(_dos_allocmem(512,&prefix)==0);
 CK(_dos_allocmem(1,&block)==0);
 CK(_dos_freemem(prefix)==0);prefix=0;
 restore_error=end(token,_psp);CK(restore_error==CL_RESTORE);
 CK(current_psp()==_psp);
 CK(info(0)==CL_LENT && !info(3) && info(4)==8);
 partial=*(unsigned __far *)MK_FP(parent-1,3);
 CK(partial>=20035 && partial<30107);

 CK(*(unsigned __far *)MK_FP(parent-1,1)==parent);
 CK(_dos_freemem(block)==0);block=0;
 CK(chdir("AWAY")==0);
 CK(end(token,_psp)==0);
 CK(current_psp()==_psp);
 {unsigned i;for(i=0;i<20;++i)CK(jft[i]==*((unsigned char __far *)MK_FP(_psp,0x18+i)));}
 CK(_dos_getvect(0)==vectors[0] && _dos_getvect(0x23)==vectors[1] && _dos_getvect(0x24)==vectors[2]);
 CK(chdir("\\")==0);
 CK(info(0)==CL_IDLE && info(3)==1);
 CK(*(unsigned __far *)MK_FP(parent-1,3)==30107);
 CK(*(unsigned __far *)MK_FP(parent-1,1)==parent);
 CK(end(token,_psp)==CL_STATE);
 startseq=info(9);
 for(j=0;j<64;++j){sprintf(name,"C:\\LPM%05X.TMP",startseq+j);collision=fopen(name,"wb");CK(collision!=0);fputc('K',collision);CK(fclose(collision)==0);}
 CK(begin(token,_psp)==CL_IO);
 CK(info(0)==CL_IDLE && info(3)==1 && info(4)==80);
 CK(*(unsigned __far *)MK_FP(parent-1,3)==30107 && *(unsigned __far *)MK_FP(parent-1,1)==parent);
 for(j=0;j<64;++j){sprintf(name,"C:\\LPM%05X.TMP",startseq+j);collision=fopen(name,"rb");CK(collision!=0);CK(fgetc(collision)=='K' && fgetc(collision)==EOF);CK(fclose(collision)==0);CK(remove(name)==0);}
 CK(current_psp()==_psp);
 {unsigned i;for(i=0;i<20;++i)CK(jft[i]==*((unsigned char __far *)MK_FP(_psp,0x18+i)));}
 done:
 _dos_close(trace);
 if(prefix)_dos_freemem(prefix);
 if(block)_dos_freemem(block);
 if(info(0)!=CL_IDLE)end(token,_psp);
 chdir("\\");
 log=fopen("C:\\CLIENT.LOG","a");if(log){fprintf(log,"CLIENT %u %u %lu %lu %u %u\n",checks,failed,(unsigned long)initial*16,(unsigned long)loan_free*16,restore_error,partial);fclose(log);}
 return failed?62:0;
}
'''
FDTEST=r'''
#include <stdlib.h>
#include <dos.h>
int main(int argc,char **argv){unsigned n;char byte;return argc==2 && _dos_read(atoi(argv[1]),&byte,1,&n)==6?0:1;}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--compiler-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads((a.compiler_dir/'manifest.json').read_text());assert sha(a.compiler_dir/'ASPCOMP.EXE')==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 sources=['src/process/compiler_lease.c','src/process/compiler_lease.h','src/process/compiler_lease_dos.asm','src/aspect/compiler_exec.asm','src/aspect/compiler.py','standalone/test_compiler_lease_dos.py','standalone/mz_layout.py']
 frozen={n:sha(ROOT/n) for n in sources};out.mkdir();(out/'AWAY').mkdir()
 (out/'parent.c').write_text(PARENT);(out/'client.c').write_text(CLIENT);(out/'fdtest.c').write_text(FDTEST)
 def run(args):
  with (out/'build.log').open('a') as log:subprocess.run(args,cwd=out,stdout=log,stderr=log,check=True)
 run(['nasm','-f','obj',str(ROOT/'src/process/compiler_lease_dos.asm'),'-o','lease_dos.obj'])
 run(['nasm','-f','obj',str(ROOT/'src/aspect/compiler_exec.asm'),'-o','exec.obj'])
 flags=['-q','-os','-bt=dos','-0','-ms','-fpc','-ecc','-s','-w4','-we','-k8192','-I'+str(ROOT/'src/process')]
 run(['wcl',*flags,'-fd=PARENT.lnk','-fm=PARENT.map','-fe=PARENT.EXE','parent.c',str(ROOT/'src/process/compiler_lease.c'),'lease_dos.obj','exec.obj'])
 with (out/'PARENT.lnk').open('a') as f:f.write('\noption packcode=0\n')
 run(['wlink','@PARENT.lnk'])
 run(['wdis','-a','-l=lease.dis','compiler_lease.o'])
 dis=(out/'lease.dis').read_text();assert not re.search(r'call\s+near ptr _lease_dos_',dis) and 'offset DGROUP:' not in dis
 text_map=(out/'PARENT.map').read_text();segments=[re.search(r'^'+n+r'\s+\S+\s+\S+\s+([0-9a-f]+):',text_map,re.M).group(1) for n in ('_TEXT','LEASE_CODE','LEASE_IO_CODE')]
 assert len(set(segments))==3,segments
 run(['wcl',*flags,'-fm=CLIENT.map','-fe=CLIENT.EXE','client.c','exec.obj'])
 run(['wcl',*flags,'-fe=FDTEST.EXE','fdtest.c'])
 layout=inspect((out/'PARENT.EXE').read_bytes());assert layout['page_minimum_including_PSP']<20035*16
 shutil.copyfile(a.compiler_dir/'ASPCOMP.EXE',out/'ASPCOMP.EXE')
 source='string value\nproc main\nget value 10\nendproc\n';(out/'TEST.ASP').write_bytes(source.encode())
 (out/'RUN.BAT').write_bytes(b'@echo off\r\nPARENT\r\nif errorlevel 1 goto fail\r\necho PASS>PASS.TXT\r\ngoto done\r\n:fail\r\necho FAIL>FAIL.TXT\r\n:done\r\nexit\r\n')
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nRUN\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=90)
 assert (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),(out/'RESULT.TXT').read_text() if (out/'RESULT.TXT').exists() else 'no parent result'
 text=(out/'RESULT.TXT').read_text();assert 'RESULT 3 0 30107 1' in text,text
 rows=[list(map(int,line.split()[1:])) for line in (out/'CLIENT.LOG').read_text().splitlines()];assert len(rows)==3 and all(r[1]==0 and r[4]==6 and 20035<=r[5]<30107 for r in rows),rows
 assert (out/'TEST.ASX').read_bytes()==compile_source(source,enable_get=True)
 assert not list(out.glob('LPM*.TMP'))
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,original_inputs=[],parent_profile_simulated=True,production_integrated=False,physical_verified=False,
  rounds=3,tail_bytes=(30107-20035)*16,parent_paragraphs=30107,retained_paragraphs=20035,client_paragraphs=8539,
  compiler_sha256=m['binary_sha256'],parent_sha256=sha(out/'PARENT.EXE'),client_sha256=sha(out/'CLIENT.EXE'),
  parent_minimum=layout,client_checks=rows,sources=frozen,result=text,scope=__doc__+' Real foreign parent MCB, no-inherit backup, exact tail bytes, real compiler, allocation obstruction/retry, repeated child invocations and vectors. DOSBox integrated DOS; no production UART/renderer/outer-loan/hardware or whole-language claim.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS compiler lease:',sum(r[0] for r in rows),'client checks;3 exact161152-byte restorations')
if __name__=='__main__':main()
