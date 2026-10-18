#!/usr/bin/env python3
"""Actual DOS strict KEY reader plus explicit synthetic DOS IO fault fixture."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/key-actions-dos';MODULE=ROOT/'src/key_mapping'
COMMON=r'''
#include "key_actions_dos.h"
#include <stdio.h>
#include <string.h>
static unsigned char selected[540],before[540];
static key_actions_dos_result result;
static unsigned checks,failures;
static void check(unsigned good,const char *label)
{++checks;if(!good)++failures;printf("%s %s\n",good?"PASS":"FAIL",label);}
static unsigned char pattern(unsigned at)
{
 unsigned slot=at/54,part=at%54;
 if(!part)return (unsigned char)(slot%4);if(part==1)return 0;
 part-=2;
 if(!part)return (unsigned char)('A'+slot);
 if(part==1 || part==3 || part==4 || part==5)return '^';
 if(part==2)return '@';if(part==6)return '~';if(part==7)return 0;
 return (unsigned char)(slot*13+part*7);
}
static unsigned correct(void)
{unsigned i;for(i=0;i<540;++i)if(selected[i]!=pattern(i))return 0;return 1;}
static void poison(void){memset(selected,0xa5,540);memcpy(before,selected,540);}
'''
REAL=COMMON+r'''
int main(void)
{
 unsigned i,good=1;
 check(key_actions_dos_read("NORMAL.KEY",selected,&result)==0 && correct() &&
 result.bytes_processed==540 && !result.dos_error && !result.close_error,"all10 raw kinds/caret/pause-shaped bytes and opaque tails exact");
 poison();check(key_actions_dos_read("ABSENT.KEY",selected,&result)==KEY_ACTIONS_DOS_OPEN && !memcmp(selected,before,540),"missing no creation or destination change");
 check(key_actions_dos_read("EMPTY.KEY",selected,&result)==KEY_ACTIONS_DOS_SIZE && !result.bytes_processed && !memcmp(selected,before,540),"empty rejected");
 check(key_actions_dos_read("SHORT.KEY",selected,&result)==KEY_ACTIONS_DOS_SIZE && result.bytes_processed==539 && !memcmp(selected,before,540),"short539 rejected");
 check(key_actions_dos_read("SUFFIX.KEY",selected,&result)==KEY_ACTIONS_DOS_SIZE && result.bytes_processed==541 && !memcmp(selected,before,540),"extra541st byte rejected");
 check(key_actions_dos_read("BADKIND.KEY",selected,&result)==KEY_ACTIONS_DOS_KIND && !memcmp(selected,before,540),"kind4 inlastrecord rejected");
 check(key_actions_dos_read("HIGHKIND.KEY",selected,&result)==KEY_ACTIONS_DOS_KIND && !memcmp(selected,before,540),"kind highbyte not silently truncated");
 check(key_actions_dos_read("BADTEXT.KEY",selected,&result)==KEY_ACTIONS_DOS_TEXT && !memcmp(selected,before,540),"last52byte string withoutNUL rejected");
 check(key_actions_dos_read("MAXTEXT.KEY",selected,0)==0 && selected[2]=='X' && selected[52]=='X' && !selected[53],"51content bytes storagevalid optionalresult");
 check(key_actions_dos_read("CARET.KEY",selected,&result)==0 && selected[2]=='^' && !selected[3],"trailingcaret storagevalid execution validation remains separate");
 poison();for(i=0;i<48;++i)if(key_actions_dos_read("BADTEXT.KEY",selected,&result)!=KEY_ACTIONS_DOS_TEXT)good=0;
 check(good && key_actions_dos_read("NORMAL.KEY",selected,&result)==0 && correct(),"48errors close handles then validload");
 printf("KEYACTION REAL %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
FAULT=COMMON+r'''
static unsigned mode,opens,closes,reads,position;
static void reset(unsigned m){mode=m;opens=closes=reads=position=0;poison();}
unsigned key_action_fault_open(const char *path,unsigned flags,int *handle)
{(void)path;(void)flags;++opens;*handle=9;return mode==1?2:0;}
unsigned key_action_fault_close(int handle)
{(void)handle;++closes;return mode==3 || mode==4?6:0;}
unsigned key_action_fault_read(int handle,void __far *buffer,unsigned size,unsigned *count)
{
 unsigned limit=540,n,i;unsigned char __far *out=(unsigned char __far *)buffer;
 (void)handle;++reads;*count=0;
 if(mode==2 || mode==4 || (mode==8 && position==540) || (mode==9 && position>=100))return 5;
 if(mode==6)limit=539;else if(mode==7)limit=541;
 n=position<limit?limit-position:0;if(n>size)n=size;
 if((mode==5 || mode==9) && n>13)n=13;
 for(i=0;i<n;++i)out[i]=pattern(position+i);
 if(mode==10 && position<=486 && position+n>486)out[486-position]=4;
 if(mode==11 && position<=487 && position+n>487)out[487-position]=1;
 if(mode==12)for(i=0;i<n;++i)if(position+i>=488)out[i]='X';
 position+=n;*count=n;return 0;
}
int main(void)
{
 unsigned i,status,want,good;key_actions_dos_result prior;char longpath[65];
 for(i=1;i<=12;++i){
  reset(i);status=key_actions_dos_read("X",selected,&result);
  want=i==1?KEY_ACTIONS_DOS_OPEN:(i==2 || i==4 || i==8 || i==9)?KEY_ACTIONS_DOS_READ:
   i==3?KEY_ACTIONS_DOS_CLOSE:(i==6 || i==7)?KEY_ACTIONS_DOS_SIZE:
   (i==10 || i==11)?KEY_ACTIONS_DOS_KIND:i==12?KEY_ACTIONS_DOS_TEXT:KEY_ACTIONS_DOS_OK;
  good=status==want && result.status==want && opens==1 && closes==(i==1?0:1);
  if(i==5)good=good && correct() && reads==43 && result.bytes_processed==540;
  else good=good && !memcmp(selected,before,540);
  if(i==3 || i==4)good=good && result.close_error==6;
  if(i==4)good=good && result.dos_error==5;
  check(good,"declared open/read/close/EOF/kind/string fault or fragmented exact load");
 }
 reset(0);memset(&result,0x77,sizeof(result));prior=result;
 check(key_actions_dos_read(0,selected,&result)==1 && !opens && !memcmp(&result,&prior,sizeof(result)),"null path before IO/resultmutation");
 check(key_actions_dos_read("",selected,&result)==1 && !opens,"empty path rejected");
 check(key_actions_dos_read("X",0,&result)==1 && !opens,"null destination rejected");
 check(key_actions_dos_read("X",(unsigned char *)0xff00,&result)==1 && !opens,"destination wrap rejected");
 check(key_actions_dos_read("X",selected,(key_actions_dos_result *)0xfffc)==1 && !opens,"result wrap rejected");
 check(key_actions_dos_read("X",selected,(key_actions_dos_result *)selected)==1 && !opens && !memcmp(selected,before,540),"result destination alias rejected");
 memcpy(selected,"X",2);memcpy(before,selected,540);
 check(key_actions_dos_read((char *)selected,selected,&result)==1 && !opens && !memcmp(selected,before,540),"path destination alias rejected");
 memcpy(&result,"X",2);prior=result;
 check(key_actions_dos_read((char *)&result,selected,&result)==1 && !opens && !memcmp(&result,&prior,sizeof(result)),"path result alias rejected");
 memset(longpath,'A',64);longpath[64]=0;
 check(key_actions_dos_read(longpath,selected,&result)==1 && !opens,"path64 rejected");
 check(key_actions_dos_read("X",selected,0)==0 && correct() && closes==1,"optionalresult no schema normalization");
 printf("KEYACTION FAULT %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
def payload():
 output=bytearray()
 for slot in range(10):
  text=bytes([65+slot,94,64,94,94,94,126,0])+bytes((slot*13+part*7)&255 for part in range(8,52))
  output+=(slot%4).to_bytes(2,'little')+text
 return bytes(output)
def main():
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'real.c').write_text(REAL);(OUT/'fault.c').write_text(FAULT)
 source=MODULE/'key_actions_dos.c'
 for stem,host,extra in [('KAREAL','real.c',[]),('KAFAULT','fault.c',['-d_dos_open=key_action_fault_open','-d_dos_read=key_action_fault_read','-d_dos_close=key_action_fault_close'])]:
  subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(MODULE),'-fm='+stem+'.map','-fe='+stem+'.EXE',*extra,str(source),str(OUT/host)],cwd=OUT,check=True)
 normal=payload();kind=bytearray(normal);kind[486]=4;high=bytearray(normal);high[487]=1;text=bytearray(normal);text[488:540]=b'X'*52;maximum=bytearray(normal);maximum[2:54]=b'X'*51+b'\0';caret=bytearray(normal);caret[2:4]=b'^\0'
 fixtures={'NORMAL.KEY':normal,'SHORT.KEY':normal[:-1],'SUFFIX.KEY':normal+b'X','EMPTY.KEY':b'','BADKIND.KEY':bytes(kind),'HIGHKIND.KEY':bytes(high),'BADTEXT.KEY':bytes(text),'MAXTEXT.KEY':bytes(maximum),'CARET.KEY':bytes(caret)}
 for name,value in fixtures.items():(OUT/name).write_bytes(value)
 before={name:hashlib.sha256(value).hexdigest() for name,value in fixtures.items()}
 for name in ['PASS.TXT','FAIL.TXT','REAL.TXT','FAULT.TXT']:(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nKAREAL >REAL.TXT\nif errorlevel 1 goto fail\nKAFAULT >FAULT.TXT\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 logs={name:(OUT/name).read_text() for name in ['REAL.TXT','FAULT.TXT'] if (OUT/name).exists()}
 for name,log in logs.items():print(name+'\n'+log)
 assert (OUT/'PASS.TXT').exists(),logs
 assert 'KEYACTION REAL 11 checks 0 failures' in logs['REAL.TXT'] and 'KEYACTION FAULT 22 checks 0 failures' in logs['FAULT.TXT']
 assert before=={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in fixtures}
 assert not (OUT/'ABSENT.KEY').exists()
 result={'passed':True,'real_DOS_checks':11,'declared_fault_checks':22,'destination_size':540,'result_size':8,'synthetic_files_unchanged':before,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(MODULE.glob('key_actions_dos*'))+[Path(__file__).resolve()]},'binary_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['KAREAL.EXE','KAFAULT.EXE']},'scope':'Actual DOS source-only strict KEY540-byte reader plus separate explicit DOS fault model. ExactEOF, close-before-commit, kinds0..3, boundedstrings, rawcaret/pause bytes and tails. No original/privateKEY, automaticcreation or actionexecution.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
