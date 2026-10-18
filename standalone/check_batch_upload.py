#!/usr/bin/env python3
"""Source-only batch owner: real DOS enumeration and linked FS fault tests."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
from dos_image import DosImage
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/batch-upload'
DRIVER=r'''
#include "batch_upload.h"
#include "batch_upload_fs.h"
#include "upload_file.h"
#include <dos.h>
#include <i86.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static unsigned char buffer[1024];
#define CHECK(x) do {if(!(x)){printf("FAIL line%d\n",__LINE__);return __LINE__;}}while(0)
#ifdef FAULT
extern unsigned choice,reads,closes,finds;
int main(int argc,char **argv)
{
 unsigned n,s;choice=argc>1?atoi(argv[1]):0;
 CHECK(batch_upload_initialize()==BU_OK);
 CHECK(batch_upload_begin("BAD/../*.BIN")==BU_ARGUMENT);
 CHECK(batch_upload_begin("CON")==BU_ARGUMENT);
 CHECK(batch_upload_begin("P*/A.BIN")==BU_ARGUMENT);
 CHECK(batch_upload_begin((char *)&batch_upload_current)==BU_ARGUMENT);
 CHECK(finds==0);
 CHECK(batch_upload_begin(choice==1?"ERR*.BIN":"*.BIN")==BU_OK);
 s=batch_upload_next();
 if(choice==1){CHECK(s==BU_ENUMERATE && batch_upload_current.dos_error==5);return 0;}
 if(choice==2){CHECK(s==BU_SOURCE && !upload_source_result.handle_open);CHECK(closes==1);return 0;}
 CHECK(s==BU_FILE);
 CHECK(batch_upload_next()==BU_BUSY);
 CHECK(batch_upload_initialize()==BU_BUSY);
 CHECK(batch_upload_begin("*.BIN")==BU_BUSY);
 CHECK(batch_upload_close()==BU_BUSY && closes==0);
 CHECK(batch_upload_read(buffer,1025,&n)==BU_ARGUMENT && reads==0);
 CHECK(batch_upload_read(buffer,2,(unsigned *)buffer)==BU_ARGUMENT && reads==0);
 CHECK(batch_upload_read(&batch_upload_current,2,&n)==BU_ARGUMENT && reads==0);
 CHECK(batch_upload_read(buffer,1,(unsigned *)&upload_source_result)==BU_ARGUMENT && reads==0);
 CHECK(batch_upload_read((void *)0xffff,2,&n)==BU_ARGUMENT && reads==0);
 s=batch_upload_read(buffer,1024,&n);
 if(choice==3 || choice==5){CHECK(s==BU_SOURCE && n==0);CHECK(batch_upload_next()==BU_BUSY);CHECK(batch_upload_abort()==BU_OK);CHECK(closes==1);return 0;}
 CHECK(s==BU_OK && n==3 && buffer[0]==0 && buffer[1]==26 && buffer[2]==255);
 CHECK(batch_upload_read(buffer,1024,&n)==BU_OK && !n);
 s=batch_upload_close();
 if(choice==4){CHECK(s==BU_RECOVERY && closes==1);CHECK(batch_upload_abort()==BU_RECOVERY);CHECK(batch_upload_initialize()==BU_RECOVERY);CHECK(closes==1);return 0;}
 CHECK(s==BU_OK && closes==1);
 CHECK(batch_upload_close()==BU_STATE && closes==1);
 CHECK(batch_upload_next()==BU_DONE);
 CHECK(batch_upload_next()==BU_DONE);
 CHECK(batch_upload_initialize()==BU_OK);
 return 0;
}
#else
static void __far *dta(void)
{union REGS in,out;struct SREGS seg;in.h.ah=0x2f;intdosx(&in,&out,&seg);return MK_FP(seg.es,out.x.bx);}
int main(void)
{
 unsigned s,n,i,files=0;unsigned long total=0,offset;struct find_t unrelated;
 void __far *saved=dta();
 CHECK(batch_upload_initialize()==BU_OK);
 CHECK(batch_upload_begin("DATA/../*.BIN")==BU_ARGUMENT);
 CHECK(batch_upload_begin("DATA/NUL.BIN")==BU_ARGUMENT);
 CHECK(batch_upload_begin("DATA/MISSING.*")==BU_OK);
 CHECK(batch_upload_next()==BU_DONE);CHECK(dta()==saved);
 CHECK(batch_upload_initialize()==BU_OK);
 CHECK(_dos_setfileattr("DATA/HIDE.BIN",_A_HIDDEN)==0);
 CHECK(_dos_setfileattr("DATA/SYS.BIN",_A_SYSTEM)==0);
 CHECK(_dos_setfileattr("DATA/READONLY.BIN",_A_RDONLY)==0);
 CHECK(batch_upload_begin("data/*.bin")==BU_OK);
 while((s=batch_upload_next())==BU_FILE){
  ++files;offset=0;CHECK(dta()==saved);
  CHECK(batch_upload_next()==BU_BUSY);
  if(batch_upload_current.size)CHECK(batch_upload_close()==BU_BUSY);
  do {
   CHECK(batch_upload_read(buffer,sizeof(buffer),&n)==BU_OK);
   if(!strcmp(batch_upload_current.name,"BIG.BIN"))for(i=0;i<n;++i)CHECK(buffer[i]==(unsigned char)(offset+i));
   offset+=n;
  }while(n);
  CHECK(offset==batch_upload_current.size);total+=offset;
  CHECK(batch_upload_close()==BU_OK);
  /* Another runtime search changes global DTA. Our continuation must survive. */
  CHECK(_dos_findfirst("DATA/BIG.BIN",0,&unrelated)==0);saved=dta();
 }
 CHECK(s==BU_DONE && files==209 && total==11730UL);
 CHECK(batch_upload_initialize()==BU_OK);
 CHECK(batch_upload_begin("DATA/EMPTY.BIN")==BU_OK);
 CHECK(batch_upload_next()==BU_FILE && !batch_upload_current.size);
 CHECK(batch_upload_close()==BU_OK);
 CHECK(batch_upload_next()==BU_DONE);
 CHECK(batch_upload_initialize()==BU_OK);
 CHECK(batch_upload_begin("ABSENT/*.BIN")==BU_OK);
 CHECK(batch_upload_next()==BU_ENUMERATE && batch_upload_current.dos_error==3);
 CHECK(batch_upload_abort()==BU_OK);
 CHECK(batch_upload_initialize()==BU_OK);
 CHECK(batch_upload_begin("DATA/BIG.BIN")==BU_OK);
 CHECK(batch_upload_next()==BU_FILE);
 CHECK(batch_upload_abort()==BU_OK);
 CHECK(batch_upload_next()==BU_STATE);
 puts("PASS209binaryemptyDTA");return 0;
}
#endif
'''
FAULT=r'''
#include "batch_upload_fs.h"
#include "upload_fs.h"
#include <string.h>
unsigned choice,reads,closes,finds;
struct find_t batch_upload_find;
unsigned batch_upload_fs_first(const char *path)
{++finds;if(choice==1)return 5;memset(&batch_upload_find,0,sizeof(batch_upload_find));strcpy(batch_upload_find.name,"A.BIN");return 0;}
unsigned batch_upload_fs_next(void){++finds;return 18;}
unsigned upload_fs_attributes(const char *p,unsigned *a){*a=0;return 0;}
unsigned upload_fs_open(const char *p,int *h){*h=7;return 0;}
unsigned upload_fs_seek_end(int h,unsigned long *n){*n=choice==2?0x80000000UL:3;return 0;}
unsigned upload_fs_rewind(int h){return 0;}
unsigned upload_fs_read(int h,void *p,unsigned n,unsigned *got)
{unsigned char *b=p;++reads;b[0]=0;b[1]=26;b[2]=255;*got=choice==3?1:3;return choice==5?5:0;}
unsigned upload_fs_close(int h){++closes;return choice==4?6:0;}
'''
def build():
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'driver.c').write_text(DRIVER);(OUT/'fault.c').write_text(FAULT)
 common=[ROOT/'src/transfer/batch_upload.c',ROOT/'src/transfer/upload_file.c']
 sources=common+[ROOT/'src/transfer/batch_upload_fs.c',ROOT/'src/transfer/upload_fs.c']
 for fault in [False,True]:
  name='BUFAULT' if fault else 'BATCH'
  subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192',
   '-i='+str(ROOT/'src/transfer'),'-fm='+name.lower()+'.map','-fe='+name+'.EXE',
   *(['-dFAULT','-wcd=303'] if fault else []),str(OUT/'driver.c'),
   *map(str,common),*([str(OUT/'fault.c')] if fault else map(str,sources[2:]))],cwd=OUT,check=True)
 return sources

def main():
 sources=build();cases=[]
 for mode in range(6):
  m=DosImage(OUT/'BUFAULT.EXE',OUT/'bufault.map')
  m.uc.mem_write(m.data_base+0xf100,str(mode).encode()+b'\0')
  m.uc.mem_write(m.data_base+0xf000,struct.pack('<3H',0,0xf100,0))
  m.uc.reg_write(UC_X86_REG_AX,2);m.uc.reg_write(UC_X86_REG_DX,0xf000)
  answer=m.call('main_',limit=5000000)
  cases.append({'case':['ownership-bounds-normal','enumeration-error-not-EOF','oversized-source-close','shrink-abort','uncertain-close-no-repeat','read-error-abort'][mode],'passed':answer==0,'return':answer})
  assert answer==0,cases[-1]
 data=OUT/'DATA';data.mkdir(exist_ok=True);(data/'DIR.BIN').mkdir(exist_ok=True)
 (data/'BIG.BIN').write_bytes(bytes(i&255 for i in range(11521)))
 for n,b in [('EMPTY.BIN',b''),('SMALL.BIN',b'\0\x1a\xff'),('READONLY.BIN',b'R'),('HIDE.BIN',b'H'),('SYS.BIN',b'S')]:
  if (data/n).exists():(data/n).chmod(0o644)
  (data/n).write_bytes(b)
 for i in range(205):(data/f'F{i:03}.BIN').write_bytes(bytes([i&255]))
 before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in data.iterdir() if p.is_file() and not p.name.startswith('.')}
 for n in ['PASS.TXT','FAIL.TXT']:(OUT/n).unlink(missing_ok=True)
 conf=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{OUT}"
c:
BATCH > DETAILS.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
 (OUT/'dosbox.conf').write_text(conf)
 with (OUT/'dosbox.log').open('w') as log:
  run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],cwd=OUT,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25)
 after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in data.iterdir() if p.is_file() and not p.name.startswith('.')}
 passed=run.returncode==0 and (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists() and before==after
 cases.append({'case':'actual8086DOS209files-binary-empty-DTA-hidden-system-readonly-abort','passed':passed,'details':(OUT/'DETAILS.TXT').read_text() if (OUT/'DETAILS.TXT').exists() else ''})
 result={'passed':all(c['passed'] for c in cases),'cases':cases,'binary_sha256':hashlib.sha256((OUT/'BATCH.EXE').read_bytes()).hexdigest(),
 'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'src/transfer/batch_upload.h',ROOT/'src/transfer/batch_upload_fs.h',ROOT/'standalone/check_batch_upload.py']},
 'watcom_DTA_evidence':'Pinned OpenWatcom bld/clib/_dos/c/finddos.c _M_I86 near-data __dos_find_first_dta/__dos_find_next_dta sets but does not restore DTA. FS wrapper savesINT21/2F and restoresINT21/1A; actualDOS verifies restoration and interleaved continuation.',
 'scope':'Actual maintained batch owner and existing upload_source code. Linked fault groups substitute only filesystem operations; actualDOS group uses realWatcom/DOS search/read/close and209owned sources. No public BBS or original/private inputs.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':
 try:status=main()
 except Exception as error:
  OUT.mkdir(parents=True,exist_ok=True)
  failure={'passed':False,'error':type(error).__name__+': '+str(error)}
  (OUT/'checks.json').write_text(json.dumps(failure,indent=2)+'\n')
  print(json.dumps(failure,indent=2));status=1
 raise SystemExit(status)
