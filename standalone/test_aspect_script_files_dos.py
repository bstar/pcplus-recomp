#!/usr/bin/env python3
"""DOS-compile file scripts, then exercise actual VM lifetimes in one process."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
from build_aspect_runtime import ROOT,ASM,OUT as COMPONENT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
OUT=ROOT/'build/aspect-script-files-dos'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
SOURCES={
'NORMAL':'''integer bytes_read,last_char,eof_before,eof_after,cleared,setting_before,setting_after
long position
string block,line1,line2
proc main
fetch fgets_crlf setting_before
set fgets_crlf ,off
fetch fgets_crlf setting_after
fopen 0 "DATA.BIN" "w+b"
fputs 0 "ABC"
fputc 0 0
fwrite 0 "XYZ" 3
ftell 0 position
fseek 0 0L 0
fread 0 block 7 bytes_read
eof 0 eof_before
fgetc 0 last_char
eof 0 eof_after
fclear 0
eof 0 cleared
fopen 1 "LINE.BIN" "wb"
fputs 1 "A"
fputc 1 13
fputc 1 10
fputs 1 "B"
fputc 1 10
fclose 1
fopen 1 "LINE.BIN" "rb"
fgets 1 line1
fgets 1 line2
fclose 1
fflush 0
endproc
''',
'ABORT':'''integer result,zero
proc main
fopen 0 "ABORT.BIN" "wb"
fputs 0 "abort"
result=1/zero
endproc
''',
'CHAIN1':'''proc main
fopen 0 "CHAIN.BIN" "w+b"
fputs 0 "first"
execute "CHAIN2"
endproc
''',
'CHAIN2':'''integer count
long position
string block
proc main
fputs 0 "second"
ftell 0 position
fseek 0 0L 0
fread 0 block 11 count
endproc
''',
'CHFAIL':'''proc main
fopen 0 "CHERR.BIN" "wb"
fputs 0 "retained"
execute "NOFILE"
endproc
''',
'RANGE':'''proc main
fopen 6 "WRONG.BIN" "wb"
endproc
''',
'COUNT':'''proc main
fopen 0 "COUNT.BIN" "wb"
fputs 0 "safe"
fwrite 0 "ABC" 81
endproc
''',
'CLOSED':'''proc main
fclose 0
endproc
''',
'OPENFAIL':'''integer result
proc main
fopen 0 "ABSENT\\NO.BIN" "rb"
result=failure
endproc
''',
'BUDGET':'''proc main
fopen 0 "BUDGET.BIN" "wb"
fputs 0 "budget"
while 1
endwhile
endproc
''',
'SIX':'''proc main
'''+''.join(f'fopen {i} "SIX{i}.BIN" "wb"\nfputs {i} "owned{i}"\n' for i in range(6))+'''endproc
''',
'PARAM':'''proc main
integer handle=3
string name="PARAM.BIN"
call worker with handle name
endproc
proc worker
intparm filehandle
strparm filename
fopen filehandle filename "wb"
fputs filehandle "parameter"
endproc
''',
'CLISRC':'''proc main
fopen 0 "CLI.BIN" "wb"
fputs 0 "source-child"
endproc
''',
}
CASES=[('NORMAL',0,1000),('ABORT',11,1000),('CHAIN1',0,1000),('CHFAIL',1,1000),('RANGE',7,1000),('COUNT',7,1000),('CLOSED',7,1000),('OPENFAIL',0,1000),('BUDGET',6,40),('SIX',0,1000),('PARAM',0,1000)]
C=r'''
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "runtime.h"
#include "file_io.h"
#include "script_file_runtime.h"
#include "find_runtime.h"
#include "compiler_heap_snapshot.h"
extern aspect_file runtime_file;
static unsigned failures,checks,cases;
static const char *current;
static struct _heapinfo far_before[128],far_after[128],near_before[128],near_after[128];
static unsigned char jft_before[20],jft_after[20];
static unsigned cpu_flags(void);
#pragma aux cpu_flags = "pushf" "pop ax" value [ax] modify exact [ax];
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL %s check%u err%u native%u live%u\n",current,checks,runtime_error,runtime_native_error_code,runtime_script_file_live);}}
static void jft(unsigned char *out){union REGS r;r.h.ah=0x51;intdos(&r,&r);_fmemcpy(out,MK_FP(r.x.bx,0x18),20);}
static unsigned near_snapshot(struct _heapinfo *entries){struct _heapinfo item;unsigned count=0;int status;item._pentry=0;while((status=_nheapwalk(&item))==_HEAPOK)if(item._useflag==_USEDENTRY){ck(count<128);if(count>=128)return count;entries[count++]=item;}ck(status==_HEAPEND||status==_HEAPEMPTY);return count;}
static void run(const char *path,unsigned expected,unsigned limit){unsigned result,i,flags=cpu_flags();void (__interrupt __far *vector)(void)=_dos_getvect(0);current=path;++cases;
 result=aspect_runtime_run(path,limit);ck(result==expected);ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(runtime_script_file_live==0&&runtime_live==0&&runtime_find_live==0&&runtime_file.handle==0&&runtime_abi_bad==0);
 for(i=0;i<6;++i)ck(runtime_script_file_slots[i]==0);
 ck(runtime_script_file_cleanup_errors==0);ck(runtime_script_file_open_calls==runtime_script_file_close_calls+(!strcmp(path,"OPENFAIL.ASX")));
 if(!strcmp(path,"NORMAL.ASX")){
  static const unsigned expected_values[]={7,65535U,0,16,0,1,0};
  for(i=0;i<7;++i)ck(runtime_integer_b[i]==expected_values[i]);ck(runtime_longs[0]==7);
  ck(!memcmp(runtime_string_snapshot[0],"ABC\0XYZ\0",8));ck(!strcmp((char *)runtime_string_snapshot[1],"A"));ck(!strcmp((char *)runtime_string_snapshot[2],"B"));ck(runtime_script_file_peak==2);
 }else if(!strcmp(path,"CHAIN1.ASX")){
  ck(runtime_integer_b[0]==11&&runtime_longs[0]==11);ck(!strcmp((char *)runtime_string_snapshot[0],"firstsecond"));ck(runtime_cleanup_count==2&&runtime_close_count==2);ck(runtime_script_file_open_calls==1&&runtime_script_file_close_calls==1);
 }else if(!strcmp(path,"OPENFAIL.ASX"))ck(runtime_integer_b[0]==1);
 else if(!strcmp(path,"CLOSED.ASX"))ck(runtime_native_error_code==4);
 else if(!strcmp(path,"SIX.ASX"))ck(runtime_script_file_peak==6);
 printf("CASE %s error%u files%u/%u\n",path,result,runtime_script_file_open_calls,runtime_script_file_close_calls);
}
int main(void){unsigned cycle,far_count=0,far_after_count=0,near_count,near_after_count,i;
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
 out=OUT/a.label;out.mkdir(parents=True,exist_ok=False);stage=out/'drive';stage.mkdir()
 binary=ROOT/'build/aspect-runner/ASPECT.EXE';compiler=ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'
 before={str(p.relative_to(ROOT)):sha(p) for p in (binary,compiler,ROOT/'src/aspect/compiler.py',Path(__file__))}
 for f in (binary,compiler):shutil.copyfile(f,stage/f.name)
 for name,source in SOURCES.items():
  compile_source(source);(stage/(name+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('cp437'))
 program=C
 for name,error,limit in CASES:program+=f' run("{name}.ASX",{error},{limit});\n'
 program+=' current="baseline";ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);\n for(cycle=0;cycle<30;++cycle){\n'
 for name,error,limit in CASES:program+=f' run("{name}.ASX",{error},{limit});\n'
 program+=''' }
 current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("FILE_VM %u cases %u checks %u failures farheap%u nearheap%u JFT-preserved\\n",cases,checks,failures,far_count,near_count);return failures?1:0;}
'''
 (out/'harness.c').write_text(program)
 cs=['runtime.c','script_file_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm='+str(out/'FILEVM.map'),'-fe='+str(stage/'FILEVM.EXE'),str(out/'harness.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/n) for n in cs],*[str(COMPONENT/(name+'.obj')) for name,_,_ in ASM]],cwd=out,check=True)
 batch=['@echo off']
 for name in SOURCES:
  if name=='CLISRC':continue
  batch += [f'ASPCOMP {name}.ASP >{name}.CMP','if errorlevel 1 goto failed']
 batch+=['ASPECT CLISRC.ASP >CLI.LOG','if errorlevel 1 goto failed','FILEVM >RESULT.TXT','if errorlevel 1 goto failed','echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (stage/'RUN.BAT').write_text('\n'.join(batch)+'\n')
 config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{stage}"\nc:\ncall RUN.BAT\nexit\n';(out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=100)
 output=(stage/'RESULT.TXT').read_text() if (stage/'RESULT.TXT').exists() else 'No VM result; inspect compiler/CLI logs'
 assert (stage/'PASS.TXT').exists() and not (stage/'FAIL.TXT').exists(),output
 summary=re.search(r'^FILE_VM (\d+) cases (\d+) checks 0 failures farheap(\d+) nearheap(\d+) JFT-preserved$',output,re.M);assert summary,output
 for name,source in SOURCES.items():assert (stage/(name+'.ASX')).read_bytes()==compile_source(source),name
 expected={'DATA.BIN':b'ABC\0XYZ','LINE.BIN':b'A\r\nB\n','ABORT.BIN':b'abort','CHAIN.BIN':b'firstsecond','CHERR.BIN':b'retained','COUNT.BIN':b'safe','BUDGET.BIN':b'budget','CLI.BIN':b'source-child','PARAM.BIN':b'parameter',**{f'SIX{i}.BIN':f'owned{i}'.encode() for i in range(6)}}
 for name,data in expected.items():assert (stage/name).read_bytes()==data,name
 assert not (stage/'WRONG.BIN').exists() and not (stage/'ABSENT').exists()
 assert before=={p:sha(ROOT/p) for p in before}
 report=dict(passed=True,cases=int(summary[1]),assertions=int(summary[2]),far_used_blocks=int(summary[3]),near_used_blocks=int(summary[4]),same_process_rounds=31,DOS_summary=summary[0],source_compiler_and_host_equal=len(SOURCES),source_cli_child_verified=True,runner_sha256=sha(binary),compiler_sha256=sha(compiler),checker_sha256=sha(Path(__file__)),inputs=before,harness_sha256=sha(out/'harness.c'),native_objects={name:sha(COMPONENT/(name+'.obj')) for name,_,_ in ASM},fixture_sources=SOURCES,files={name:dict(bytes=len(data),sha256=sha(stage/name)) for name,data in expected.items()},result_sha256=sha(stage/'RESULT.TXT'),scope='Actual DOS ASPCOMP output plus explicit ASP CLI child and full native VM/owned stdio in341 invocations within one process. Normal/divide-error/range/closed-slot/count/budget/missing-chain cleanup, successful EXECUTE with retained file slot, native global string writes and SET/FETCH tested. Near/far used heap and JFT preserved after warmup; actual user cancellation and parent handoff are separate.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report['DOS_summary'])
if __name__=='__main__':main()
