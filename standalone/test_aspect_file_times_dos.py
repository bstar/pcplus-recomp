#!/usr/bin/env python3
"""Actual DOS timestamps, source immutability and native/fixed string controls."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
import test_aspect_script_files_dos as base
from build_aspect_runtime import ROOT,ASM,OUT as COMPONENT
from compiler import compile_source
sha=base.sha
SOURCES={
'CONTROL':'''string date_result,time_result,date_input_result,time_input_result,param_result
proc main
date_result="OLD-DATE"
time_result="OLD-TIME"
getfdate "DATA.BIN" date_result
getftime "DATA.BIN" time_result
call local_worker
call param_worker with "14:06"
endproc
proc local_worker
string value="03-07-93"
setfdate "DATA.BIN" value
strcpy date_input_result value
s0="21:06"
setftime "DATA.BIN" s0
strcpy time_input_result s0
endproc
proc param_worker
strparm value
setftime "DATA.BIN" value
strcpy param_result value
endproc
''',
'BUILTIN':'''string result
proc main
setfdate "DATA.BIN" "10-07-93"
findfirst "DATA.BIN"
if found
setfdate "DATA.BIN" $FDATE
strcpy result $FDATE
endif
endproc
''',
'ROUND':'''integer errors
string future_date,old_time,new_time,retained_date,early_date,leap_date,last_date
proc main
setfdate "DATA.BIN" "12-31-79"
errors+=failure
getfdate "DATA.BIN" future_date
errors+=failure
getftime "DATA.BIN" old_time
errors+=failure
setftime "DATA.BIN" "21:06"
errors+=failure
getftime "DATA.BIN" new_time
getfdate "DATA.BIN" retained_date
setfdate "DATA.BIN" "01-01-80"
getfdate "DATA.BIN" early_date
setfdate "DATA.BIN" "02-29-00"
getfdate "DATA.BIN" leap_date
setfdate "DATA.BIN" "12-31-99"
getfdate "DATA.BIN" last_date
endproc
''',
'MISSING':'''integer d_error,t_error,sd_error,st_error
string date_result,time_result
proc main
date_result="KEEP-DATE"
time_result="KEEP-TIME"
getfdate "NOFILE.BIN" date_result
d_error=failure
getftime "NOFILE.BIN" time_result
t_error=failure
setfdate "NOFILE.BIN" "03-07-93"
sd_error=failure
setftime "NOFILE.BIN" "13:45"
st_error=failure
endproc
''',
'SIXTIME':'''string date_result,time_result
proc main
'''+''.join(f'fopen {i} "STREAM.BIN" "rb"\n' for i in range(6))+'''getfdate "DATA.BIN" date_result
getftime "DATA.BIN" time_result
setfdate "DATA.BIN" "03-07-93"
setftime "DATA.BIN" "13:45"
endproc
''',
'CHAIN1':'''proc main
setfdate "DATA.BIN" "12-31-99"
setftime "DATA.BIN" "21:06"
execute "CHAIN2"
endproc
''',
'CHAIN2':'''string date_result,time_result
proc main
getfdate "DATA.BIN" date_result
getftime "DATA.BIN" time_result
endproc
''',
'CLISRC':'''string date_result,time_result
proc main
setfdate "DATA.BIN" "03-07-93"
setftime "DATA.BIN" "13:45"
getfdate "DATA.BIN" date_result
getftime "DATA.BIN" time_result
strcmp date_result " 3-07-93"
if success
strcmp time_result "13:45"
if success
message "TIMESTAMP READY"
endif
endif
endproc
''',
}
CASES=[('CONTROL',0),('BUILTIN',0),('ROUND',0),('MISSING',0),('SIXTIME',0),('CHAIN1',0),('TRUNC',5),('BADDEST',7)]
C=base.C.split('static void run(')[0].replace('#include "script_file_runtime.h"','#include "script_file_runtime.h"\n#include "file_info_runtime.h"\n#include "file_times_runtime.h"')+r'''
#include <fcntl.h>
static void stamp(unsigned date,unsigned clock){int h;ck(_dos_open("DATA.BIN",O_RDWR,&h)==0);ck(_dos_setftime(h,date,clock)==0);ck(_dos_close(h)==0);}
static void raw_time(unsigned date,unsigned clock){int h;unsigned d,t;ck(_dos_open("DATA.BIN",O_RDONLY,&h)==0);ck(_dos_getftime(h,&d,&t)==0);ck(d==date&&t==clock);ck(_dos_close(h)==0);}
static void run(const char *path,unsigned expected){unsigned result,i,flags=cpu_flags();void (__interrupt __far *vector)(void)=_dos_getvect(0);current=path;++cases;stamp((13<<9)|(3<<5)|7,(13<<11)|(45<<5)|29);
 result=aspect_runtime_run(path,2000);ck(result==expected);ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(!runtime_file_times_live&&!runtime_file_info_live&&!runtime_script_file_live&&!runtime_live&&!runtime_find_live&&!runtime_file.handle&&!runtime_abi_bad);
 if(!strcmp(path,"CONTROL.ASX")){
#ifdef TIME_NATIVE_CONTROL
  static const char *values[]={"OLD-DATE","OLD-TIME","03","21","14"};
#else
  static const char *values[]={" 3-07-93","13:45","03-07-93","21:06","14:06"};
#endif
  for(i=0;i<5;++i)ck(!strcmp((char *)runtime_string_snapshot[i],values[i]));
  raw_time((13<<9)|(3<<5)|7,(14<<11)|(6<<5));
 }else if(!strcmp(path,"BUILTIN.ASX")){
#ifdef TIME_NATIVE_CONTROL
  ck(!strcmp((char *)runtime_string_snapshot[0],"10"));
#else
  ck(!strcmp((char *)runtime_string_snapshot[0],"10-07-93"));
#endif
  raw_time((13<<9)|(10<<5)|7,(13<<11)|(45<<5)|29);
 }else if(!strcmp(path,"ROUND.ASX")){
  static const char *values[]={"12-31-79","13:45","21:06","12-31-79"," 1-01-80"," 2-29-00","12-31-99"};
  ck(runtime_integer_b[0]==0);for(i=0;i<7;++i)ck(!strcmp((char *)runtime_string_snapshot[i],values[i]));
  raw_time((19<<9)|(12<<5)|31,(21<<11)|(6<<5));
 }else if(!strcmp(path,"MISSING.ASX")){
  for(i=0;i<4;++i)ck(runtime_integer_b[i]==1);
  ck(!strcmp((char *)runtime_string_snapshot[0],"KEEP-DATE"));ck(!strcmp((char *)runtime_string_snapshot[1],"KEEP-TIME"));
 }else if(!strcmp(path,"SIXTIME.ASX")){
  ck(!strcmp((char *)runtime_string_snapshot[0]," 3-07-93")&&!strcmp((char *)runtime_string_snapshot[1],"13:45"));ck(runtime_script_file_peak==6&&runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
 }else if(!strcmp(path,"CHAIN1.ASX")){
  ck(!strcmp((char *)runtime_string_snapshot[0],"12-31-99")&&!strcmp((char *)runtime_string_snapshot[1],"21:06"));ck(runtime_cleanup_count==2);
 }
 printf("CASE %s error%u temporary%u\n",path,result,runtime_file_times_live);
}
int main(void){unsigned cycle,far_count=0,far_after_count=0,near_count,near_after_count,i;
#ifdef TIME_NATIVE_CONTROL
 run("CONTROL.ASX",0);run("BUILTIN.ASX",0);printf("NATIVE_TIME_CONTROL %u checks %u failures global=OLD inputs=truncated\n",checks,failures);return failures?1:0;
#else
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
 out=ROOT/'build/aspect-file-times-dos'/a.label;out.mkdir(parents=True,exist_ok=False);stage=out/'drive';stage.mkdir()
 binary=ROOT/'build/aspect-runner/ASPECT.EXE';compiler=ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE';before={str(p.relative_to(ROOT)):sha(p) for p in (binary,compiler,Path(__file__))}
 for f in (binary,compiler):shutil.copyfile(f,stage/f.name)
 for name,source in SOURCES.items():compile_source(source);(stage/(name+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('cp437'))
 valid=compile_source('string value\nproc main\ngetfdate "DATA.BIN" value\nendproc\n');assert valid[-3:]==b'\x8c\x00\x94'
 (stage/'TRUNC.ASX').write_bytes(valid[:-3]);(stage/'BADDEST.ASX').write_bytes(valid[:-3]+b'\xff\x00\x94')
 (stage/'DATA.BIN').write_bytes(b'unchanged-timestamp-data');(stage/'STREAM.BIN').write_bytes(b'stream')
 calls=''.join(f' run("{name}.ASX",{error});\n' for name,error in CASES)
 program=C+calls+''' current="baseline";ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<30;++cycle){
'''+calls+''' }
 current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("TIME_VM %u cases %u checks %u failures farheap%u nearheap%u JFT-preserved\\n",cases,checks,failures,far_count,near_count);return failures?1:0;
#endif
}
'''
 (out/'harness.c').write_text(program)
 cs=['runtime.c','script_file_runtime.c','file_info_runtime.c','file_times_runtime.c','enumeration_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c']
 for native in (False,True):
  name='NATIVE' if native else 'TIMEVM';objects=[str(ROOT/'build/aspect-file-times/file_times.obj') if native and n=='file_times' else str(COMPONENT/(n+'.obj')) for n,_,_ in ASM]
  subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC',*(['-dTIME_NATIVE_CONTROL','-wcd=202'] if native else []),'-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm='+str(out/(name+'.map')),'-fe='+str(stage/(name+'.EXE')),str(out/'harness.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/n) for n in cs],*objects],cwd=out,check=True)
 batch=['@echo off']
 for name in SOURCES:
  if name!='CLISRC':batch += [f'ASPCOMP {name}.ASP >{name}.CMP','if errorlevel 1 goto failed']
 batch+=['ASPECT CLISRC.ASP >CLI.LOG','if errorlevel 1 goto failed','NATIVE >NATIVE.TXT','if errorlevel 1 goto failed','TIMEVM >RESULT.TXT','if errorlevel 1 goto failed','echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (stage/'RUN.BAT').write_text('\n'.join(batch)+'\n');(out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{stage}"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=120)
 output=(stage/'RESULT.TXT').read_text() if (stage/'RESULT.TXT').exists() else 'Inspect compiler/CLI/native-control logs'
 assert (stage/'PASS.TXT').exists() and not (stage/'FAIL.TXT').exists(),output
 summary=re.search(r'^TIME_VM (\d+) cases (\d+) checks 0 failures farheap(\d+) nearheap(\d+) JFT-preserved$',output,re.M);assert summary,output
 native=(stage/'NATIVE.TXT').read_text();assert re.search(r'NATIVE_TIME_CONTROL \d+ checks 0 failures global=OLD inputs=truncated',native)
 for name,source in SOURCES.items():assert (stage/(name+'.ASX')).read_bytes()==compile_source(source),name
 assert b'TIMESTAMP READY' in (stage/'CLI.LOG').read_bytes()
 assert (stage/'DATA.BIN').read_bytes()==b'unchanged-timestamp-data' and (stage/'STREAM.BIN').read_bytes()==b'stream'
 assert before=={p:sha(ROOT/p) for p in before}
 report=dict(passed=True,cases=int(summary[1]),assertions=int(summary[2]),same_process_rounds=31,DOS_summary=summary[0],native_control_sha256=sha(stage/'NATIVE.EXE'),native_control_result_sha256=sha(stage/'NATIVE.TXT'),native_control_summary=native.strip().splitlines()[-1],native_object_sha256=sha(ROOT/'build/aspect-file-times/file_times.obj'),runtime_object_sha256=sha(COMPONENT/'file_times.obj'),runner_sha256=sha(binary),compiler_sha256=sha(compiler),checker_sha256=sha(Path(__file__)),reused_harness_sha256=sha(Path(base.__file__)),harness_sha256=sha(out/'harness.c'),result_sha256=sha(stage/'RESULT.TXT'),fixtures=SOURCES,original_inputs=[],scope='Actual8086 DOS compiler,production ASP CLI and real VM/DOS57 with source-owned native FILE prefix. Date pivot1980/1999/2000/2079,leap date,opposite-field/seconds preservation and time second truncation;far getter writeback and immutable local/register/parameter/readonly-builtin setters. Real native core control retains old globals and truncates near inputs. Missing paths,all six streams,EXECUTE,late destination faults and repeated heap/JFT/INT0/FLAGS/ABI cleanup. File bytes unchanged. Open-only native comparison/error policy retained;physical/filesystem-wide validation remains open.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report['DOS_summary']);print(report['native_control_summary'])
if __name__=='__main__':main()
