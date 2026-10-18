#!/usr/bin/env python3
"""Source-built DOS directory streaming IO tests; synthetic files and DOS faults."""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-dos'
COMMON=r'''
#include "directory_dos.h"
#include <stdio.h>
#include <string.h>
static directory_dos_selection selected,before;
static directory_dos_page_data page,page_before;
static directory_dos_result result;
static unsigned failures,checks;
static void check(int good,const char *label)
{ ++checks;if(!good)++failures;printf("%s %s\n",good?"PASS":"FAIL",label); }
static unsigned char pattern(unsigned at)
{
 unsigned record,index;
 if(at>=250 && at<23050){record=(at-250)/114+1;index=(at-250)%114;
  if(!index)return (unsigned char)record;if(index==1)return (unsigned char)(record>>8);}
 return (unsigned char)(at*17U+3U);
}
static int valid_record(const unsigned char *bytes,unsigned number)
{
 unsigned i,at=250+(number-1)*114;
 for(i=0;i<114;++i)if(bytes[i]!=pattern(at+i))return 0;
 return 1;
}
static int valid_header(const unsigned char *bytes)
{ unsigned i;for(i=0;i<250;++i)if(bytes[i]!=pattern(i))return 0;return 1; }
static int valid_selection(unsigned number)
{ return selected.entry_number==number && valid_header(selected.header) && valid_record(selected.record,number); }
static int valid_page(unsigned first)
{
 unsigned count=201-first,i,j;if(count>10)count=10;
 if(page.first_entry!=first || page.count!=count || !valid_header(page.header))return 0;
 for(i=0;i<count;++i)if(!valid_record(page.records[i],first+i))return 0;
 for(;i<10;++i)for(j=0;j<114;++j)if(page.records[i][j])return 0;
 return 1;
}
static void poison(void)
{ memset(&selected,0xa5,sizeof(selected));before=selected;memset(&page,0x5a,sizeof(page));page_before=page; }
'''
NORMAL=COMMON+r'''
int main(void)
{
 unsigned i,good=1;
 for(i=1;i<=200;++i){
  if(directory_dos_read("NORMAL.DIR",i,&selected,&result)!=DIRECTORY_DOS_OK ||
   result.bytes_processed!=23050 || result.dos_error || result.close_error || !valid_selection(i))good=0;
 }
 check(good,"all200 original one-based entries preserve complete raw header/record bytes");
 good=1;for(i=1;i<=200;++i){
  if(directory_dos_page("NORMAL.DIR",i,&page,&result)!=DIRECTORY_DOS_OK ||
   result.bytes_processed!=23050 || !valid_page(i))good=0;
 }
 check(good,"all200 unaligned page starts and zero-filled short final pages");
 poison();check(directory_dos_read("ABSENT.DIR",1,&selected,&result)==DIRECTORY_DOS_OPEN &&
  !memcmp(&selected,&before,sizeof(before)),"missing selected file unchanged");
 check(directory_dos_page("ABSENT.DIR",1,&page,&result)==DIRECTORY_DOS_OPEN &&
  !memcmp(&page,&page_before,sizeof(page)),"missing page file unchanged");
 for(i=0;i<48;++i){
  if(directory_dos_read("SHORT.DIR",1,&selected,&result)!=DIRECTORY_DOS_SIZE ||
   result.bytes_processed!=23049 || memcmp(&selected,&before,sizeof(before)))break;
 }
 check(i==48 && directory_dos_read("NORMAL.DIR",200,&selected,0)==DIRECTORY_DOS_OK &&
  valid_selection(200),"48 close-after-short errors then valid optional-result load");
 poison();check(directory_dos_read("LONG.DIR",1,&selected,&result)==DIRECTORY_DOS_SIZE &&
  result.bytes_processed==23051 && !memcmp(&selected,&before,sizeof(before)),"suffix rejected after selected entry fully read");
 check(directory_dos_page("SHORT.DIR",1,&page,&result)==DIRECTORY_DOS_SIZE &&
  !memcmp(&page,&page_before,sizeof(page)),"short file rejected after selected page fully read");
 check(directory_dos_page("LONG.DIR",1,&page,&result)==DIRECTORY_DOS_SIZE &&
  !memcmp(&page,&page_before,sizeof(page)),"page suffix rejected");
 check(directory_dos_read("EMPTY.DIR",1,&selected,&result)==DIRECTORY_DOS_SIZE &&
  !result.bytes_processed && !memcmp(&selected,&before,sizeof(before)),"empty file rejected");
 check(directory_dos_page("NORMAL.DIR",200,&page,0)==DIRECTORY_DOS_OK && valid_page(200),"page200 optional-result load");
 printf("DIRECTORY REAL %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
FAULT=COMMON+r'''
#include <dos.h>
static unsigned mode,opens,closes,position;
static void reset(unsigned value){mode=value;opens=closes=position=0;poison();}
unsigned directory_fault_open(const char *path,unsigned flags,int *handle)
{ (void)path;(void)flags;++opens;if(mode==1)return 2;*handle=7;return 0; }
unsigned directory_fault_close(int handle)
{ (void)handle;++closes;return mode==3 || mode==4 ? 6 : 0; }
unsigned directory_fault_read(int handle,void __far *buffer,unsigned size,unsigned *bytes)
{
 unsigned i,count,limit=23050;
 unsigned char __far *out=(unsigned char __far *)buffer;(void)handle;*bytes=0;
 if(mode==2 || mode==4 || (mode==8 && position==23050) || (mode==10 && position>=1000))return 5;
 if(mode==6)limit=23049;else if(mode==7)limit=23051;else if(mode==9)limit=249;
 count=position<limit ? limit-position : 0;if(count>size)count=size;
 if(mode==5 && count>13)count=13;
 for(i=0;i<count;++i)out[i]=pattern(position+i);
 position+=count;*bytes=count;return 0;
}
int main(void)
{
 unsigned i,status,want,good;directory_dos_result prior;
 for(i=1;i<=10;++i){
  reset(i);status=directory_dos_read("X",1,&selected,&result);
  want=i==1?DIRECTORY_DOS_OPEN:(i==2 || i==4 || i==8 || i==10)?DIRECTORY_DOS_READ:
   i==3?DIRECTORY_DOS_CLOSE:i==5?DIRECTORY_DOS_OK:DIRECTORY_DOS_SIZE;
  good=status==want && result.status==want && opens==1 && closes==(i==1?0:1);
  if(i==5)good=good && valid_selection(1) && result.bytes_processed==23050;
  else good=good && !memcmp(&selected,&before,sizeof(before));
  if(i==3 || i==4)good=good && result.close_error==6;
  if(i==4)good=good && result.dos_error==5;
  check(good,"selected IO fault or fragmented read; close/atomic/error accounting");
  reset(i);status=directory_dos_page("X",191,&page,&result);
  good=status==want && result.status==want && opens==1 && closes==(i==1?0:1);
  if(i==5)good=good && valid_page(191) && result.bytes_processed==23050;
  else good=good && !memcmp(&page,&page_before,sizeof(page));
  check(good,"page IO fault or fragmented read; no partial commit");
 }
 reset(0);memset(&result,0x77,sizeof(result));prior=result;
 check(directory_dos_read("X",0,&selected,&result)==DIRECTORY_DOS_ARGUMENT && !opens &&
  !memcmp(&result,&prior,sizeof(result)),"entry0 rejected before IO and result mutation");
 check(directory_dos_read("X",201,&selected,&result)==DIRECTORY_DOS_ARGUMENT && !opens,"entry201 rejected");
 check(directory_dos_read(0,1,&selected,&result)==DIRECTORY_DOS_ARGUMENT && !opens,"null path rejected");
 check(directory_dos_read("",1,&selected,&result)==DIRECTORY_DOS_ARGUMENT && !opens,"empty path rejected");
 check(directory_dos_read("X",1,0,&result)==DIRECTORY_DOS_ARGUMENT && !opens,"null destination rejected");
 check(directory_dos_read("X",1,(directory_dos_selection *)0xff00,&result)==DIRECTORY_DOS_ARGUMENT && !opens,"selection near-extent wrap rejected");
 check(directory_dos_page("X",1,(directory_dos_page_data *)0xff00,&result)==DIRECTORY_DOS_ARGUMENT && !opens,"page near-extent wrap rejected");
 check(directory_dos_read("X",1,&selected,(directory_dos_result *)&selected)==DIRECTORY_DOS_ARGUMENT && !opens &&
  !memcmp(&selected,&before,sizeof(before)),"selection/result overlap unchanged");
 check(directory_dos_page("X",1,&page,(directory_dos_result *)&page)==DIRECTORY_DOS_ARGUMENT && !opens &&
  !memcmp(&page,&page_before,sizeof(page)),"page/result overlap unchanged");
 check(directory_dos_page("X",1,&page,(directory_dos_result *)0xfffc)==DIRECTORY_DOS_ARGUMENT && !opens,"result near-extent wrap rejected");
 {
  char longpath[129];memset(longpath,'A',128);longpath[128]=0;
  check(directory_dos_read(longpath,1,&selected,&result)==DIRECTORY_DOS_ARGUMENT && !opens,"path longer than127 rejected");
 }
 memcpy(&selected,"X",2);before=selected;
 check(directory_dos_read((char *)&selected,1,&selected,&result)==DIRECTORY_DOS_ARGUMENT && !opens &&
  !memcmp(&selected,&before,sizeof(before)),"path/selection overlap rejected unchanged");
 memcpy(&result,"X",2);prior=result;
 check(directory_dos_page((char *)&result,1,&page,&result)==DIRECTORY_DOS_ARGUMENT && !opens &&
  !memcmp(&result,&prior,sizeof(result)),"path/result overlap rejected before initialization");
 check(directory_dos_read("X",1,&selected,0)==DIRECTORY_DOS_OK && valid_selection(1) && closes==1,"modeled optional result pointer success");
 printf("DIRECTORY FAULT %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
def payload():
 data=bytearray((i*17+3)&255 for i in range(23050))
 for entry in range(1,201):
  at=250+(entry-1)*114;data[at:at+2]=entry.to_bytes(2,'little')
 return bytes(data)
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 macros={name:int(value) for name,value in re.findall(r'^%define (DD_\w+) (\d+)$',(ROOT/'src/directory/directory_dos.inc').read_text(),re.M)}
 for name,value in {'DD_ENTRY_NUMBER':0,'DD_HEADER':2,'DD_RECORD':252,'DD_SELECTION_SIZE':366,'DD_PAGE_FIRST':0,'DD_PAGE_COUNT':2,'DD_PAGE_HEADER':4,'DD_PAGE_RECORDS':254,'DD_PAGE_CAPACITY':10,'DD_PAGE_SIZE':1394,'DD_FILE_SIZE':23050,'DD_RESULT_SIZE':8}.items():assert macros[name]==value
 (OUT/'real.c').write_text(NORMAL);(OUT/'fault.c').write_text(FAULT)
 source=ROOT/'src/directory/directory_dos.c'
 for stem,host,extra in [('DIRREAL','real.c',[]),('DIRFAULT','fault.c',['-d_dos_open=directory_fault_open','-d_dos_read=directory_fault_read','-d_dos_close=directory_fault_close'])]:
  subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/directory'),'-fm='+stem+'.map','-fe='+stem+'.EXE',*extra,str(source),str(OUT/host)],cwd=OUT,check=True)
 data=payload()
 for name,value in [('NORMAL.DIR',data),('SHORT.DIR',data[:-1]),('LONG.DIR',data+b'X'),('EMPTY.DIR',b'')]: (OUT/name).write_bytes(value)
 before={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ('NORMAL.DIR','SHORT.DIR','LONG.DIR','EMPTY.DIR')}
 for name in ('PASS.TXT','FAIL.TXT','REAL.TXT','FAULT.TXT'):(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nDIRREAL >REAL.TXT\nif errorlevel 1 goto fail\nDIRFAULT >FAULT.TXT\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=50)
 logs={name:(OUT/name).read_text() for name in ('REAL.TXT','FAULT.TXT') if (OUT/name).exists()}
 for name,log in logs.items():print(name+'\n'+log)
 assert (OUT/'PASS.TXT').exists(),logs
 assert 'DIRECTORY REAL 10 checks 0 failures' in logs['REAL.TXT']
 assert 'DIRECTORY FAULT 34 checks 0 failures' in logs['FAULT.TXT']
 assert before=={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in before}
 inputs=[source,ROOT/'src/directory/directory_dos.h',ROOT/'src/directory/directory_dos.inc',Path(__file__).resolve()]
 result={'passed':True,'selection_bytes':366,'page_bytes':1394,'real_DOS_checks':10,'injected_service_checks':34,'selected_entries_tested':200,'page_start_positions_tested':200,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'binary_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ('DIRREAL.EXE','DIRFAULT.EXE')},'synthetic_files_unchanged':before,'scope':'Actual DOS8086 streaming selected-entry/page IO with synthetic files; separate actual compiled backend has declared injected DOS open/read/close faults. No originals, private directories, semantic/UI/password display or file writes from reader.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
