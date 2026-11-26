#!/usr/bin/env python3
"""DOS clock queries, writable destinations and repeated native VM cleanup."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
import test_aspect_script_files_dos as base
from build_aspect_runtime import ROOT,ASM,OUT as COMPONENT
from compiler import compile_source
sha=base.sha
BODY='date d\ntime t0 0\ntime t1 1\n'
SOURCES={
 'GLOBAL':'string d,t0,t1\ninteger before,after\nproc main\nstrcmp "A" "B"\nbefore=failure\n'+BODY+'after=failure\nendproc\n',
 'LOCAL':'string d,t0,t1\nproc main\nstring ld,lt0,lt1\ndate ld\ntime lt0 0\ntime lt1 1\nstrcpy d ld\nstrcpy t0 lt0\nstrcpy t1 lt1\nendproc\n',
 'PARAM':'string d,t0,t1\nproc main\ncall worker with "OLD" "OLD" "OLD"\nendproc\nproc worker\nstrparm a\nstrparm b\nstrparm c\ndate a\ntime b 0\ntime c 1\nstrcpy d a\nstrcpy t0 b\nstrcpy t1 c\nendproc\n',
 'REG':'string d,t0,t1\nproc main\ndate s0\nstrcpy d s0\ntime s9 0\nstrcpy t0 s9\ntime s0 1\nstrcpy t1 s0\nendproc\n',
 'SIX':'string d,t0,t1\nproc main\n'+''.join('fopen '+str(i)+' "STREAM.BIN" "rb"\n' for i in range(6))+BODY+'endproc\n',
 'CHAIN1':'proc main\nexecute "CHAIN2"\nendproc\n',
 'CHAIN2':'string d,t0,t1\nproc main\n'+BODY+'endproc\n',
 'RANGE2':'string d\nproc main\nd="OLD"\ntime d 2\nendproc\n',
 'RANGEN':'string d\nproc main\nd="OLD"\ntime d -1\nendproc\n',
 'CLI':'proc main\nstring d,t\ndate d\ntime t 1\nfopen 0 "CLOCK.LOG" "wb"\nfputs 0 d\nfputc 0 32\nfputs 0 t\nfclose 0\nendproc\n'}
CASES=[(n,7 if n.startswith('RANGE') else 0) for n in SOURCES if n not in ('CHAIN2','CLI')]+[(n,e) for n,e in [('DTRUNC',5),('DBAD',7),('TTRUNC',5),('TBAD',7)]]
BUILTIN_BODY='d=$date\nt0=$time0\nt1=$time1\n'
BUILTIN_SOURCES={
 'BGLOBAL':'string d,t0,t1\ninteger before,after\nproc main\nstrcmp "A" "B"\nbefore=failure\n'+BUILTIN_BODY+'after=failure\nendproc\n',
 'BLOCAL':'string d,t0,t1\nproc main\nstring ld,lt0,lt1\nld=$date\nlt0=$time0\nlt1=$time1\nstrcpy d ld\nstrcpy t0 lt0\nstrcpy t1 lt1\nendproc\n',
 'BPARAM':'string d,t0,t1\nproc main\ncall worker with $date $time0 $time1\nendproc\nproc worker\nstrparm a\nstrparm b\nstrparm c\nstrcpy d a\nstrcpy t0 b\nstrcpy t1 c\nendproc\n',
 'BREG':'string d,t0,t1\nproc main\ns0=$date\nstrcpy d s0\ns9=$time0\nstrcpy t0 s9\ns0=$time1\nstrcpy t1 s0\nendproc\n',
 'BSIX':'string d,t0,t1\nproc main\n'+''.join('fopen '+str(i)+' "STREAM.BIN" "rb"\n' for i in range(6))+BUILTIN_BODY+'endproc\n',
 'BCHAIN1':'proc main\nexecute "BCHAIN2"\nendproc\n',
 'BCHAIN2':'string d,t0,t1\nproc main\n'+BUILTIN_BODY+'endproc\n',
 'BMIXED':'string d,t0,t1\nproc main\ndate d\nt0=$time0\ntime t1 1\nendproc\n',
 'BALIAS':'string d,t0,t1\ninteger first,second\nproc main\n'+BUILTIN_BODY+'strcmp $time0 $time1\nfirst=success\nstrcmp $time1 $time0\nsecond=success\nendproc\n',
 'BWHEN':'string d,t0,t1\nproc main\nwhen 0 "A" call worker\ntransmit "READY"\nwaitfor "END" 1\ntransmit "DONE"\nendproc\nproc worker\n'+BUILTIN_BODY+'transmit "HIT"\nendproc\n',
 'BCOPY':'string d,t0,t1,joined\nproc main\n'+BUILTIN_BODY+'joined=$time0\nstrcat joined $time1\nendproc\n',
 'CLI':'proc main\nstring d,t\nd=$date\nt=$time1\nfopen 0 "CLOCK.LOG" "wb"\nfputs 0 d\nfputc 0 32\nfputs 0 t\nfclose 0\nendproc\n'}
C=base.C.split('static void run(')[0]+r'''
#include "serial_runtime.h"
#include "receive_runtime.h"
static unsigned long clock_now(void){struct dostime_t t;_dos_gettime(&t);return (unsigned long)t.hour*3600UL+t.minute*60U+t.second;}
static void date_now(char *out){struct dosdate_t d;_dos_getdate(&d);sprintf(out,"%02u/%02u/%02u",d.month,d.day,d.year-1900U);}
static unsigned number(const char *p){return (p[0]-'0')*10+p[1]-'0';}
static void time_value(const char *p,unsigned twelve,unsigned long first,unsigned long last){
 unsigned h,m,s;unsigned long value;
 ck(strlen(p)==(twelve?10:8));ck(p[2]==':'&&p[5]==':');
 ck(p[0]>='0'&&p[0]<='9'&&p[1]>='0'&&p[1]<='9');
 ck(p[3]>='0'&&p[3]<='9'&&p[4]>='0'&&p[4]<='9');
 ck(p[6]>='0'&&p[6]<='9'&&p[7]>='0'&&p[7]<='9');
 h=number(p);m=number(p+3);s=number(p+6);ck(m<60&&s<60);
 if(twelve){ck(h>=1&&h<=12);ck((p[8]=='A'||p[8]=='P')&&p[9]=='M');h=h%12+(p[8]=='P'?12:0);}else ck(h<24);
 value=(unsigned long)h*3600UL+m*60U+s;
 ck(first<=last?(first<=value&&value<=last):(value>=first||value<=last));
}
static void run(const char *path,unsigned expected){
 unsigned result,i,flags=cpu_flags();unsigned long first,last;char date1[16],date2[16];
 void (__interrupt __far *vector)(void)=_dos_getvect(0);current=path;++cases;
 if(!strcmp(path,"BWHEN.ASX")){runtime_serial_fixture((const unsigned char *)"AEND",4,(const unsigned char *)"READY",5,1,0UL,1UL);runtime_receive_fixture(0,1);}
 date_now(date1);first=clock_now();result=aspect_runtime_run(path,2000);last=clock_now();date_now(date2);
 if(!strcmp(path,"BWHEN.ASX")){ck(runtime_serial_tx_size==12&&!memcmp(runtime_serial_tx,"READYHITDONE",12));runtime_serial_fixture_disable();}
 if(cases<=12)printf("CLOCKCASE %s result%u date=%s expected=%s time0=%s time1=%s\n",path,result,runtime_string_snapshot[0],date1,runtime_string_snapshot[1],runtime_string_snapshot[2]);
 ck(result==expected);ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(!runtime_script_file_live&&!runtime_live&&!runtime_find_live&&!runtime_file.handle&&!runtime_abi_bad);
 for(i=0;i<6;++i)ck(!runtime_script_file_slots[i]);
 if(expected){if(!strncmp(path,"RANGE",5))ck(!strcmp((char *)runtime_string_snapshot[0],"OLD"));return;}
 ck(!strcmp((char *)runtime_string_snapshot[0],date1)||!strcmp((char *)runtime_string_snapshot[0],date2));
 time_value((char *)runtime_string_snapshot[1],1,first,last);time_value((char *)runtime_string_snapshot[2],0,first,last);
 if(!strcmp(path,"GLOBAL.ASX")||!strcmp(path,"BGLOBAL.ASX"))ck(runtime_integer_b[0]==65535U&&runtime_integer_b[1]==65535U);
 if(!strcmp(path,"SIX.ASX")||!strcmp(path,"BSIX.ASX"))ck(runtime_script_file_peak==6&&runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
 if(!strcmp(path,"CHAIN1.ASX")||!strcmp(path,"BCHAIN1.ASX"))ck(runtime_cleanup_count==2);
 if(!strcmp(path,"BALIAS.ASX"))ck(runtime_integer_b[0]==1&&runtime_integer_b[1]==1);
 if(!strcmp(path,"BCOPY.ASX")){char early[11];ck(strlen((char *)runtime_string_snapshot[3])==18);memcpy(early,runtime_string_snapshot[3],10);early[10]=0;time_value(early,1,first,last);time_value((char *)runtime_string_snapshot[3]+10,0,first,last);}
}
int main(void){unsigned cycle,i,far_count=0,far_after_count=0,near_count,near_after_count;
'''
BUILTIN_API=r'''
extern unsigned __cdecl clock_query(unsigned);
extern unsigned runtime_string_pending_near,runtime_string_scratch_pointer,runtime_string_scratch_index;
extern unsigned long runtime_string_pending_far;
static void builtin_api(void){
 unsigned start=checks,d,t0,t1;char saved_date[16],saved_time[16];
 unsigned pending=runtime_string_pending_near,scratch=runtime_string_scratch_pointer,index=runtime_string_scratch_index,comparison=runtime_string_compare_result;
 unsigned long far_pending=runtime_string_pending_far;
 current="clock-builtin-alias-API";
 runtime_string_pending_near=0x4321;runtime_string_pending_far=0x12345678UL;
 runtime_string_scratch_pointer=0x5432;runtime_string_scratch_index=6;runtime_string_compare_result=999;
 d=clock_query(8);strcpy(saved_date,(char *)d);
 t0=clock_query(20);strcpy(saved_time,(char *)t0);ck(strlen(saved_time)==10);
 t1=clock_query(21);ck(t0==t1&&t0!=d);ck(strlen((char *)t0)==8);ck(strlen(saved_time)==10);
 ck(!strcmp(saved_date,(char *)d));((char *)t1)[0]='?';
 ck(clock_query(20)==t0);ck(strlen((char *)t1)==10&&*(char *)t1>='0'&&*(char *)t1<='9');
 ck(clock_query(8)==d);ck(!strcmp(saved_date,(char *)d));
 ck(runtime_string_pending_near==0x4321&&runtime_string_pending_far==0x12345678UL);
 ck(runtime_string_scratch_pointer==0x5432&&runtime_string_scratch_index==6);
 ck(runtime_string_compare_result==999);
 runtime_string_pending_near=pending;runtime_string_pending_far=far_pending;
 runtime_string_scratch_pointer=scratch;runtime_string_scratch_index=index;runtime_string_compare_result=comparison;
 printf("CLOCK_BUILTIN_API %u checks\n",checks-start);
}
'''
QUERY_ASM='''BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _clock_query
extern aspect_string_builtin
_clock_query:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push word [bp+4]
 call aspect_string_builtin
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
'''

def main():
 global SOURCES,CASES
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--component-dir',type=Path,default=COMPONENT);p.add_argument('--runner-dir',type=Path,default=ROOT/'build/aspect-runner');p.add_argument('--compiler-dir',type=Path,default=ROOT/'build/aspect-compiler-dos');p.add_argument('--builtins',action='store_true')
 a=p.parse_args()
 for key in ('component_dir','runner_dir','compiler_dir'):setattr(a,key,getattr(a,key).resolve())
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False);drive=out/'drive';drive.mkdir()
 if a.builtins:
  SOURCES={**SOURCES,**BUILTIN_SOURCES};CASES += [(n,0) for n in BUILTIN_SOURCES if n not in ('BCHAIN2','CLI')]
 inputs=[a.runner_dir/'ASPECT.EXE',a.compiler_dir/'ASPCOMP.EXE']
 sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(Path(base.__file__).relative_to(ROOT)):sha(Path(base.__file__))}
 manifests=[]
 for folder in (a.component_dir,a.runner_dir,a.compiler_dir):
  manifest=json.loads((folder/'manifest.json').read_text());manifests.append(manifest)
  for key,h in manifest['sources'].items():assert sha(ROOT/key)==h,key;sources[key]=h
 before={str(f.relative_to(ROOT)):sha(f) for f in inputs}
 for f in inputs:shutil.copyfile(f,drive/f.name)
 for n,source in SOURCES.items():
  compile_source(source)
  (drive/(n+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('cp437'))
 for prefix,command in [('D','date d'),('T','time d 1')]:
  data=compile_source('string d\nproc main\n'+command+'\nendproc\n');at=data.index(0x1d if prefix=='D' else 0xbe,2)+1
  (drive/(prefix+'TRUNC.ASX')).write_bytes(data[:at]);(drive/(prefix+'BAD.ASX')).write_bytes(data[:at]+b'\xff\x00\x94')
 (drive/'STREAM.BIN').write_bytes(b'preserve-clock-stream')
 calls=''.join(' run("'+n+'.ASX",'+str(error)+');\n' for n,error in CASES)
 program=C+calls+r''' current="baseline";ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<30;++cycle){
'''+calls+r''' }
 current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("CLOCK_VM %u cases %u checks %u failures\n",cases,checks,failures);return failures?1:0;
}
'''
 if a.builtins:
  program=program.replace('int main(void)',BUILTIN_API+'\nint main(void)',1)
  program=program.replace(' current="final";jft',' builtin_api();\n current="final";jft',1)
 (out/'clock.c').write_text(program)
 cs=['runtime.c','environment_runtime.c','script_file_runtime.c','file_info_runtime.c','file_times_runtime.c','enumeration_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c']
 extra=[]
 for flag,name in [('experimental_directory_baud',None),('experimental_directory_fields','directory_fields'),('experimental_directory_proto','directory_proto'),('experimental_clock_builtins','clock_builtins')]:
  if manifests[0].get(flag) and name:extra.append(name)
 if a.builtins:assert manifests[0].get('experimental_clock_builtins') and manifests[1].get('experimental_clock_builtins')
 api_objects=[]
 if a.builtins:
  (out/'query.asm').write_text(QUERY_ASM)
  subprocess.run(['nasm','-fobj',str(out/'query.asm'),'-o',str(out/'query.obj')],check=True);api_objects=[str(out/'query.obj')]
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm='+str(out/'CLOCK.map'),'-fe='+str(drive/'CLOCK.EXE'),str(out/'clock.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/n) for n in cs],*[str(a.component_dir/(n+'.obj')) for n in [*[n for n,_,_ in ASM],*extra]],*api_objects],cwd=out,check=True)
 batch=['@echo off']
 for n in SOURCES:batch+=['ASPCOMP '+n+'.ASP >'+n+'.CMP','if errorlevel 1 goto failed']
 batch+=['ASPECT CLI.ASP >CLI.LOG','if errorlevel 1 goto failed','CLOCK >RESULT.TXT','if errorlevel 1 goto failed','echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (drive/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=120)
 output=(drive/'RESULT.TXT').read_text() if (drive/'RESULT.TXT').exists() else 'No VM result; inspect compiler logs';assert (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),output
 match=re.search(r'CLOCK_VM (\d+) cases (\d+) checks 0 failures',output);assert match,output
 for n,s in SOURCES.items():assert (drive/(n+'.ASX')).read_bytes()==compile_source(s),n
 assert (drive/'STREAM.BIN').read_bytes()==b'preserve-clock-stream' and re.fullmatch(rb'\d{2}/\d{2}/\d{2,3} \d{2}:\d{2}:\d{2}',(drive/'CLOCK.LOG').read_bytes())
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 assert before=={n:sha(ROOT/n) for n in before}
 if a.builtins:assert 'CLOCK_BUILTIN_API 12 checks' in output
 report=dict(passed=True,clock_builtins=a.builtins,builtin_API_checks=12 if a.builtins else 0,cases=int(match[1]),checks=int(match[2]),same_process_rounds=31,products=before,sources=sources,artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},original_inputs=[],scope=__doc__+' Actual DOS2A/2C observations bracket string outputs; no clock-setting call or physical time change. Global/local/parameter/register destinations, both formats, unchanged comparison, six streams, EXECUTE, bad operands/range/truncation, repeated heap/JFT/INT0/FLAGS/ABI cleanup and source compilation through both host and DOS compiler. Not full ASPECT/physical modem acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(match[0])
if __name__=='__main__':main()
