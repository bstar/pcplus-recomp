#!/usr/bin/env python3
"""DOS compiler and actual VM: queries/rename, six streams and mid-command faults."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
import test_aspect_script_files_dos as base
from build_aspect_runtime import ROOT,ASM,OUT as COMPONENT
from compiler import compile_source
sha=base.sha
SOURCES={
 'INFO':'''integer exists,sized,missing,notfile,moved,oldgone,missingmove,conflict,restored
long size,retained,renamed
proc main
retained=123456L
isfile "DATA.BIN"
exists=failure
getfsize "DATA.BIN" size
sized=failure
getfsize "ABSENT.BIN" retained
missing=failure
isfile "ABSENT.BIN"
notfile=failure
rename "DATA.BIN" "RENAMED.BIN"
moved=failure
isfile "DATA.BIN"
oldgone=failure
getfsize "RENAMED.BIN" renamed
rename "ABSENT.BIN" "NOFILE.BIN"
missingmove=failure
rename "RENAMED.BIN" "EXISTS.BIN"
conflict=failure
rename "RENAMED.BIN" "DATA.BIN"
restored=failure
endproc
''',
 'SIXINFO':'''integer result
long size
proc main
'''+''.join(f'fopen {i} "DATA.BIN" "rb"\n' for i in range(6))+'''isfile "DATA.BIN"
result=failure
getfsize "DATA.BIN" size
endproc
''',
 'BADDEST':'''long size
proc main
getfsize "DATA.BIN" size
endproc
''',
 'LOCAL':'''integer result
long size
proc main
call worker with "DATA.BIN" 0L
endproc
proc worker
strparm path
longparm value
getfsize path value
if failure
result=1
endif
size=value
endproc
''',
 'CLISRC':'''long size
proc main
getfsize "DATA.BIN" size
if success
isfile "DATA.BIN"
if success
message "FILE INFO READY"
endif
endif
endproc
''',
}
CASES=[('INFO',0),('SIXINFO',0),('LOCAL',0),('BADOP',7),('TRUNC',5)]
C=base.C.split('static void run(')[0].replace('#include "script_file_runtime.h"','#include "script_file_runtime.h"\n#include "file_info_runtime.h"')+r'''
static void run(const char *path,unsigned expected){unsigned result,i,flags=cpu_flags();void (__interrupt __far *vector)(void)=_dos_getvect(0);current=path;++cases;
 result=aspect_runtime_run(path,1000);ck(result==expected);ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(runtime_file_info_live==0&&runtime_script_file_live==0&&runtime_live==0&&runtime_find_live==0&&runtime_file.handle==0&&runtime_abi_bad==0);
 if(!strcmp(path,"INFO.ASX")){
  static const unsigned expected_values[]={0,0,1,1,0,1,2,5,0};
  for(i=0;i<9;++i)ck(runtime_integer_b[i]==expected_values[i]);
  ck(runtime_longs[0]==70001UL&&runtime_longs[1]==123456UL&&runtime_longs[2]==70001UL);
 }else if(!strcmp(path,"SIXINFO.ASX")){
  ck(runtime_integer_b[0]==0&&runtime_longs[0]==70001UL);ck(runtime_script_file_peak==6);
  ck(runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
 }else if(!strcmp(path,"LOCAL.ASX"))ck(runtime_integer_b[0]==0&&runtime_longs[0]==70001UL);
 printf("CASE %s error%u temp%u files%u/%u\n",path,result,runtime_file_info_live,runtime_script_file_open_calls,runtime_script_file_close_calls);
}
int main(void){unsigned cycle,far_count=0,far_after_count=0,near_count,near_after_count,i;
'''
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
 out=ROOT/'build/aspect-file-info-dos'/args.label;out.mkdir(parents=True,exist_ok=False);stage=out/'drive';stage.mkdir()
 binary=ROOT/'build/aspect-runner/ASPECT.EXE';compiler=ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'
 before={str(p.relative_to(ROOT)):sha(p) for p in (binary,compiler,Path(__file__))}
 for f in (binary,compiler):shutil.copyfile(f,stage/f.name)
 for name,source in SOURCES.items():
  compile_source(source)
  (stage/(name+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('cp437'))
 valid=compile_source(SOURCES['BADDEST']);assert valid[-3:]==b'\x8e\x00\x94'
 (stage/'BADOP.ASX').write_bytes(valid[:-3]+b'\xff\x00\x94')
 (stage/'TRUNC.ASX').write_bytes(valid[:-3])
 data=bytes(i&255 for i in range(70001));(stage/'DATA.BIN').write_bytes(data);(stage/'EXISTS.BIN').write_bytes(b'preserved')
 calls=''.join(f' run("{name}.ASX",{error});\n' for name,error in CASES)
 program=C+calls+''' current="baseline";ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<30;++cycle){
'''+calls+''' }
 current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("INFO_VM %u cases %u checks %u failures farheap%u nearheap%u JFT-preserved\\n",cases,checks,failures,far_count,near_count);return failures?1:0;}
'''
 (out/'harness.c').write_text(program)
 cs=['runtime.c','environment_runtime.c','script_file_runtime.c','file_info_runtime.c','file_times_runtime.c','enumeration_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm='+str(out/'INFOVM.map'),'-fe='+str(stage/'INFOVM.EXE'),str(out/'harness.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/n) for n in cs],*[str(COMPONENT/(name+'.obj')) for name,_,_ in ASM]],cwd=out,check=True)
 batch=['@echo off']
 for name in SOURCES:
  if name!='CLISRC':batch += [f'ASPCOMP {name}.ASP >{name}.CMP','if errorlevel 1 goto failed']
 batch+=['ASPECT CLISRC.ASP >CLI.LOG','if errorlevel 1 goto failed','INFOVM >RESULT.TXT','if errorlevel 1 goto failed','echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (stage/'RUN.BAT').write_text('\n'.join(batch)+'\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{stage}"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=100)
 output=(stage/'RESULT.TXT').read_text() if (stage/'RESULT.TXT').exists() else 'Inspect compiler/CLI logs'
 assert (stage/'PASS.TXT').exists() and not (stage/'FAIL.TXT').exists(),output
 summary=re.search(r'^INFO_VM (\d+) cases (\d+) checks 0 failures farheap(\d+) nearheap(\d+) JFT-preserved$',output,re.M);assert summary,output
 for name,source in SOURCES.items():assert (stage/(name+'.ASX')).read_bytes()==compile_source(source),name
 assert b'FILE INFO READY' in (stage/'CLI.LOG').read_bytes()
 assert (stage/'DATA.BIN').read_bytes()==data and (stage/'EXISTS.BIN').read_bytes()==b'preserved'
 assert not (stage/'RENAMED.BIN').exists() and not (stage/'NOFILE.BIN').exists()
 assert before=={p:sha(ROOT/p) for p in before}
 report=dict(passed=True,cases=int(summary[1]),assertions=int(summary[2]),same_process_rounds=31,DOS_summary=summary[0],runner_sha256=sha(binary),compiler_sha256=sha(compiler),checker_sha256=sha(Path(__file__)),reused_harness_sha256=sha(Path(base.__file__)),harness_sha256=sha(out/'harness.c'),result_sha256=sha(stage/'RESULT.TXT'),fixtures=SOURCES,original_inputs=[],scope='Actual8086 DOS compiler, production ASP CLI child and actual full VM/stdio/native rename. Missing/existing files,70001 bytes, unchanged failed-size destination, raw rename errors2/5, retained files, parameter destination and all six numbered streams. Mid-command operand/read faults after fopen; repeated near/far heap/JFT/INT0/FLAGS/ABI cleanup. No physical modem or whole-language claim.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report['DOS_summary'])
if __name__=='__main__':main()
