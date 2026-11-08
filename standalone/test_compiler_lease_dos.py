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
#include <string.h>
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
#ifdef COMPILER_LEASE_BANKED
 FILE *snapshot;unsigned bank=compiler_lease_info(10),offset=compiler_lease_info(11),size=compiler_lease_info(12);
 snapshot=fopen("BEFORE.BIN",verify?"rb":"wb");if(!snapshot){mismatch=1;return;}
#endif
 for(seg=_psp+KEEP;seg<_psp+FULL;++seg){p=MK_FP(seg,0);
  for(i=0;i<16;++i){expected=(unsigned char)(((i&1)?seg>>8:seg)^(i*17)^(seed*29));
#ifdef COMPILER_LEASE_BANKED
   if(verify){if(fgetc(snapshot)!=p[i])mismatch=1;}
   else {if(!((unsigned long)seg*16+i>=(unsigned long)bank*16+offset &&
              (unsigned long)seg*16+i<(unsigned long)bank*16+offset+size))p[i]=expected;
         if(fputc(p[i],snapshot)==EOF)mismatch=1;}
#else
   if(verify){if(p[i]!=expected)mismatch=1;}else p[i]=expected;
#endif
  }
 }
#ifdef COMPILER_LEASE_BANKED
 if(verify && fgetc(snapshot)!=EOF)mismatch=1;
 if(fclose(snapshot))mismatch=1;
#endif
}
int main(void)
{
 unsigned cycle,status;int result;char args[128];FILE *log;
#ifdef COMPILER_LEASE_BANKED
 extern unsigned char __far compiler_lease_storage;
#endif
 void (__interrupt __far *v0)(void),(__interrupt __far *v23)(void),(__interrupt __far *v24)(void);
 log=fopen("RESULT.TXT","w");if(!log)return 1;
 fputs("START\n",log);fclose(log);log=fopen("RESULT.TXT","a");
 v0=_dos_getvect(0);v23=_dos_getvect(0x23);v24=_dos_getvect(0x24);
 if(lease_dos_resize(_psp,FULL)){fputs("RESIZE FAIL\n",log);fclose(log);return 2;}
 fputs("RESIZED\n",log);fclose(log);log=fopen("RESULT.TXT","a");
#ifdef COMPILER_LEASE_MODULE
 {extern unsigned __far __cdecl compiler_lease_load(const char *,unsigned,unsigned);
  if(compiler_lease_load("ABSENT.OVL",_psp,TOKEN)!=CL_IO ||
     compiler_lease_load("BROKEN.OVL",_psp,TOKEN)!=CL_CORRUPT)return 6;
  status=compiler_lease_load("PCCOMP.OVL",_psp,TOKEN);
 }
#else
 status=compiler_lease_init(_psp,KEEP,TOKEN);
#endif
 fprintf(log,"INITIALIZED %u\n",status);fclose(log);log=fopen("RESULT.TXT","a");
 if(status){fprintf(log,"INIT FAIL %u\n",status);fclose(log);return 3;}
 for(cycle=0;cycle<3;++cycle){
  fprintf(log,"FILL %u\n",cycle);fclose(log);log=fopen("RESULT.TXT","a");tail(cycle,0);
  fputs("FILLED\n",log);fclose(log);log=fopen("RESULT.TXT","a");
  sprintf(args,"%u %u %u %u %u %u %u %u",_psp,
   FP_SEG(compiler_lease_begin),FP_OFF(compiler_lease_begin),
   FP_SEG(compiler_lease_end),FP_OFF(compiler_lease_end),
   FP_SEG(compiler_lease_info),FP_OFF(compiler_lease_info),TOKEN);
#ifdef COMPILER_LEASE_BANKED
  sprintf(args+strlen(args)," %u %u",FP_SEG(&compiler_lease_storage),FP_OFF(&compiler_lease_storage));
#endif
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
#ifdef COMPILER_LEASE_BANKED
 unsigned bankseg,bankoff,banksize,i,overwritten=0;unsigned char bankprefix[32];
 unsigned __far *fault_crc;
#endif
 void (__interrupt __far *vectors[3])(void);
 int result,trace=0;call_fn begin,end;info_fn info;char arg[16],name[24];FILE *log,*collision;
#ifdef COMPILER_LEASE_BANKED
 if(argc!=11)return 60;
 fault_crc=(unsigned __far *)MK_FP(atoi(argv[9]),atoi(argv[10])+16);
#else
 if(argc!=9)return 60;
#endif
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
#ifdef COMPILER_LEASE_BANKED
 bankseg=info(10);bankoff=info(11);banksize=info(12);
 CK(bankseg*16UL+bankoff==(parent+20035UL)*16 && banksize>512);
 CK(FP_SEG(begin)*16UL+FP_OFF(begin)<(parent+20035UL)*16);
 CK(FP_SEG(end)*16UL+FP_OFF(end)<(parent+20035UL)*16);
 CK(FP_SEG(info)*16UL+FP_OFF(info)<(parent+20035UL)*16);
 for(i=0;i<32;++i)bankprefix[i]=*((unsigned char __far *)MK_FP(bankseg,bankoff+i));
#endif
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
#ifdef COMPILER_LEASE_BANKED
 for(i=0;i<32;++i)if(bankprefix[i]!=*((unsigned char __far *)MK_FP(bankseg,bankoff+i)))overwritten=1;
 CK(overwritten); /* Compiler really occupied the region containing the bank. */
#endif
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
#ifdef COMPILER_LEASE_BANKED
 /* Trusted fixture fault: force checksum rejection AFTER full readback.
  * Invalid memory must remain quarantined; no call into restored bank yet. */
 *fault_crc^=1;
 CK(end(token,_psp)==CL_CORRUPT);
 CK(current_psp()==_psp);
 CK(info(0)==CL_RESTORING && !info(3) && info(8)!=65535U);
 CK(*(unsigned __far *)MK_FP(parent-1,3)==30107);
 CK(begin(token,_psp)==CL_STATE);
 *fault_crc^=1;
#endif
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
 p.add_argument('--module',action='store_true',help='Cold-load extracted code bank before trusted init; implies banked')
 p.add_argument('--banked',action='store_true',help='Place temporary code at the exact released parent boundary')
 p.add_argument('--compiler-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();a.banked=a.banked or a.module;out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads((a.compiler_dir/'manifest.json').read_text());assert sha(a.compiler_dir/'ASPCOMP.EXE')==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/compiler_lease_module.py','src/process/compiler_lease_module.asm','src/process/compiler_lease_private.h','src/process/compiler_lease_core.c','src/process/compiler_lease_bank.asm','src/process/compiler_lease.c','src/process/compiler_lease.h','src/process/compiler_lease_dos.asm','src/aspect/compiler_exec.asm','src/aspect/compiler.py','standalone/test_compiler_lease_dos.py','standalone/mz_layout.py']
 frozen={n:sha(ROOT/n) for n in sources};out.mkdir();(out/'AWAY').mkdir()
 (out/'parent.c').write_text(PARENT);(out/'client.c').write_text(CLIENT);(out/'fdtest.c').write_text(FDTEST)
 def run(args):
  with (out/'build.log').open('a') as log:subprocess.run(args,cwd=out,stdout=log,stderr=log,check=True)
 run(['nasm',*(['-DCOMPILER_LEASE_BANKED'] if a.banked else []),*(['-DCOMPILER_LEASE_MODULE'] if a.module else []),'-f','obj',str(ROOT/'src/process/compiler_lease_dos.asm'),'-o','lease_dos.obj'])
 run(['nasm','-f','obj',str(ROOT/'src/aspect/compiler_exec.asm'),'-o','exec.obj'])
 flags=['-q','-os','-bt=dos','-0','-ms','-fpc','-ecc','-s','-w4','-we','-k8192','-I'+str(ROOT/'src/process')]
 if a.banked:flags+=['-dCOMPILER_LEASE_BANKED']
 if a.module:
  flags+=['-dCOMPILER_LEASE_MODULE']
  run(['nasm','-f','obj',str(ROOT/'src/process/compiler_lease_module.asm'),'-o','module_info.obj'])
 extra=[]
 if a.banked:
  for stem,defines in [('bank_start',['-DBANK_START','-DBANK_PADDING=0']),('bank_end',[])]:
   run(['nasm','-f','obj',*defines,str(ROOT/'src/process/compiler_lease_bank.asm'),'-o',stem+'.obj'])
  extra=['bank_start.obj',str(ROOT/'src/process/compiler_lease.c'),'bank_end.obj',str(ROOT/'src/process/compiler_lease_core.c')]
 else:extra=[str(ROOT/'src/process/compiler_lease.c')]
 run(['wcl',*flags,'-fd=PARENT.lnk','-fm=PARENT.map','-fe=PARENT.EXE','parent.c',*extra,'lease_dos.obj','exec.obj',*(['module_info.obj'] if a.module else [])])
 with (out/'PARENT.lnk').open('a') as f:f.write('\noption packcode=0\n'+('order clname CODE clname FARCODE clname FAR_DATA clname BEGDATA clname DATA clname BSS clname STACK clname LEASE_PAD clname LEASE_BANK\n' if a.banked else ''))
 run(['wlink','@PARENT.lnk'])
 bank_layout={}
 if a.banked:
  def address(symbol):
   mat=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+'+symbol+r'\b',(out/'PARENT.map').read_text(),re.M)
   assert mat,symbol
   return int(mat[1],16)*16+int(mat[2],16)
  padding=20035*16-256-address('_compiler_lease_bank_start');assert padding>0 and padding<300000
  run(['nasm','-f','obj','-DBANK_START','-DBANK_PADDING='+str(padding),str(ROOT/'src/process/compiler_lease_bank.asm'),'-o','bank_start.obj'])
  run(['wlink','@PARENT.lnk'])
  start=address('_compiler_lease_bank_start');end=address('_compiler_lease_bank_end')
  assert start==20035*16-256 and start<end<(30107*16-256),(start,end)
  for symbol in ['_compiler_lease_begin','_compiler_lease_end','_compiler_lease_info','_compiler_lease_storage','_lease_dos_read','_lease_dos_resize']:
   assert address(symbol)<start,symbol
  bank_layout=dict(start_image_byte=start,end_image_byte=end,bank_bytes=end-start,padding_bytes=padding)
 module=None
 if a.module:
  from compiler_lease_module import split
  module=split(out/'PARENT.EXE',out/'PARENT.map','_compiler_lease_bank_start',keep_symbol='_compiler_lease_bank_start')
  bad=bytearray((out/'PCCOMP.OVL').read_bytes());bad[0]^=1;(out/'BROKEN.OVL').write_bytes(bad)
 run(['wdis','-a','-l=lease.dis','compiler_lease.o'])
 dis=(out/'lease.dis').read_text();assert not re.search(r'call\s+near ptr _lease_dos_',dis) and 'offset DGROUP:' not in dis
 text_map=(out/'PARENT.map').read_text();segments=[re.search(r'^'+n+r'\s+\S+\s+\S+\s+([0-9a-f]+):',text_map,re.M).group(1) for n in ('_TEXT','LEASE_BANK' if a.banked else 'LEASE_CODE','LEASE_IO_CODE')]
 assert len(set(segments))==3,segments
 run(['wcl',*flags,'-fm=CLIENT.map','-fe=CLIENT.EXE','client.c','exec.obj'])
 run(['wcl',*flags,'-fe=FDTEST.EXE','fdtest.c'])
 layout=inspect((out/'PARENT.EXE').read_bytes())
 if a.banked:
  resident={}
  for name in ['LEASE_CORE','LEASE_IO_CODE','LEASE_STORAGE']+(['LEASE_MODULE_INFO'] if a.module else []):
   mat=re.search(r'^'+name+r'\s+\S+\s+\S+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',text_map,re.M);assert mat,name
   size=int(mat[3],16);assert int(mat[1],16)*16+int(mat[2],16)+size<=bank_layout['start_image_byte']
   resident[name]=size
  bank_layout['resident_sections']=resident;bank_layout['resident_bytes']=sum(resident.values())
  assert bank_layout['resident_bytes']<3000,bank_layout
  assert layout['page_minimum_including_PSP']<30107*16
  run(['wdis','-a','-l=core.dis','compiler_lease_core.o'])
  dis=(out/'core.dis').read_text();assert not re.search(r'call\s+near ptr _(lease_dos_|compiler_lease_)',dis) and 'offset DGROUP:' not in dis
  for obj in ['lease.dis','core.dis']:
   asm=(out/obj).read_text()
   targets=re.findall(r'call\s+far ptr (\w+)',asm)
   assert all(name.startswith('_lease_dos_') or name in ('_compiler_lease_prepare','_compiler_lease_finalize','_compiler_lease_init') for name in targets),targets
 else:assert layout['page_minimum_including_PSP']<20035*16
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
  module=module,banked=a.banked,bank_layout=bank_layout,rounds=3,tail_bytes=(30107-20035)*16,parent_paragraphs=30107,retained_paragraphs=20035,client_paragraphs=8539,
  compiler_sha256=m['binary_sha256'],parent_sha256=sha(out/'PARENT.EXE'),client_sha256=sha(out/'CLIENT.EXE'),
  parent_minimum=layout,client_checks=rows,sources=frozen,result=text,scope=__doc__+' Real foreign parent MCB, no-inherit backup, exact tail bytes, real compiler, allocation obstruction/retry, repeated child invocations and vectors. DOSBox integrated DOS; no production UART/renderer/outer-loan/hardware or whole-language claim.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS compiler lease:',sum(r[0] for r in rows),'client checks;3 exact161152-byte restorations')
if __name__=='__main__':main()
