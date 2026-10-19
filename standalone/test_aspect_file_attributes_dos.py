#!/usr/bin/env python3
"""Actual DOS attribute roundtrips and a native/fixed global-writeback control."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
import test_aspect_script_files_dos as base
from build_aspect_runtime import ROOT,ASM,OUT as COMPONENT
from compiler import compile_source
sha=base.sha
COMBOS=[''.join(c for i,c in enumerate('RHSA') if n&(1<<i)) for n in range(16)]
SOURCES={
'WRITEBK':'''string global_result,local_result,param_result,register_result
proc main
global_result="BEFORE"
getfattr "ATTR.DAT" global_result
call local_worker
call param_worker with "BEFORE"
getfattr "ATTR.DAT" s0
strcpy register_result s0
endproc
proc local_worker
string local_attrs
getfattr "ATTR.DAT" local_attrs
strcpy local_result local_attrs
endproc
proc param_worker
strparm attrsarg
getfattr "ATTR.DAT" attrsarg
strcpy param_result attrsarg
endproc
''',
'ROUND':'''integer set_error,get_error,missing_get,missing_set
string '''+','.join('v'+str(i) for i in range(16))+''',missing_attrs,directory_attrs
proc main
'''+''.join(f'setfattr "ATTR.DAT" "{value.lower()}"\nset_error+=failure\ngetfattr "ATTR.DAT" v{i}\nget_error+=failure\n' for i,value in enumerate(COMBOS))+'''getfattr "NOFILE.DAT" missing_attrs
missing_get=failure
setfattr "NOFILE.DAT" "R"
missing_set=failure
getfattr "FOLDER" directory_attrs
setfattr "ATTR.DAT" "rHs"
endproc
''',
'SIXATTR':'''string attrs
proc main
'''+''.join(f'fopen {i} "STREAM.BIN" "rb"\n' for i in range(6))+'''getfattr "ATTR.DAT" attrs
setfattr "ATTR.DAT" "RHS"
endproc
''',
'FINDLIVE':'''integer before,after_get,after_set,done
string attrs
proc main
findfirst "ATTR.DAT" "RHS"
before=found
getfattr "ATTR.DAT" attrs
after_get=found
setfattr "ATTR.DAT" "RHS"
after_set=found
findnext
done=found
endproc
''',
'CHAIN1':'''proc main
setfattr "ATTR.DAT" "rHs"
execute "CHAIN2"
endproc
''',
'CHAIN2':'''string attrs
proc main
getfattr "ATTR.DAT" attrs
endproc
''',
'BADDIR':'''proc main
setfattr "ATTR.DAT" "D"
endproc
''',
'BADVOL':'''proc main
setfattr "ATTR.DAT" "V"
endproc
''',
'BADCHAR':'''proc main
setfattr "ATTR.DAT" "?"
endproc
''',
'CLISRC':'''string attrs
proc main
setfattr "ATTR.DAT" "RHS"
getfattr "ATTR.DAT" attrs
strcmp attrs "RHS"
if success
message "ATTRIBUTE READY"
endif
endproc
''',
}
CASES=[('WRITEBK',0),('ROUND',0),('SIXATTR',0),('FINDLIVE',0),('CHAIN1',0),('BADDIR',7),('BADVOL',7),('BADCHAR',7),('TRUNC',5)]
C=base.C.split('static void run(')[0].replace('#include "script_file_runtime.h"','#include "script_file_runtime.h"\n#include "file_info_runtime.h"')+r'''
static void run(const char *path,unsigned expected){unsigned result,i,attrs,flags=cpu_flags();void (__interrupt __far *vector)(void)=_dos_getvect(0);current=path;++cases;
 result=aspect_runtime_run(path,2000);ck(result==expected);ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(!runtime_file_info_live&&!runtime_script_file_live&&!runtime_live&&!runtime_find_live&&!runtime_file.handle&&!runtime_abi_bad);
 ck(_dos_getfileattr("ATTR.DAT",&attrs)==0&&attrs==7);
 if(!strcmp(path,"WRITEBK.ASX")){
#ifdef ATTR_NATIVE_CONTROL
  ck(!strcmp((char *)runtime_string_snapshot[0],"BEFORE"));
#else
  ck(!strcmp((char *)runtime_string_snapshot[0],"RHS"));
#endif
  for(i=1;i<4;++i)ck(!strcmp((char *)runtime_string_snapshot[i],"RHS"));
 }else if(!strcmp(path,"ROUND.ASX")){
  static const char *values[]={VALUES};
  ck(runtime_integer_b[0]==0&&runtime_integer_b[1]==0&&runtime_integer_b[2]==1&&runtime_integer_b[3]==2);
  for(i=0;i<16;++i)ck(!strcmp((char *)runtime_string_snapshot[i],values[i]));
  ck(!strcmp((char *)runtime_string_snapshot[16],"RHSADV"));ck(strchr((char *)runtime_string_snapshot[17],'D')!=0);
 }else if(!strcmp(path,"SIXATTR.ASX")){ck(!strcmp((char *)runtime_string_snapshot[0],"RHS"));ck(runtime_script_file_peak==6&&runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);}
 else if(!strcmp(path,"FINDLIVE.ASX")){ck(runtime_integer_b[0]==1&&runtime_integer_b[1]==1&&runtime_integer_b[2]==1&&runtime_integer_b[3]==0);ck(!strcmp((char *)runtime_string_snapshot[0],"RHS"));}
 else if(!strcmp(path,"CHAIN1.ASX"))ck(!strcmp((char *)runtime_string_snapshot[0],"RHS")&&runtime_cleanup_count==2);
 else if(!strcmp(path,"BADDIR.ASX")||!strcmp(path,"BADVOL.ASX")||!strcmp(path,"BADCHAR.ASX"))ck(runtime_native_error_code==0);
 printf("CASE %s error%u globals=%s\n",path,result,runtime_string_snapshot[0]);
}
int main(void){unsigned cycle,far_count=0,far_after_count=0,near_count,near_after_count,i;
 current="setup";ck(_dos_setfileattr("ATTR.DAT",7)==0);
#ifdef ATTR_NATIVE_CONTROL
 run("WRITEBK.ASX",0);printf("NATIVE_CONTROL %u checks %u failures global=BEFORE near=RHS/RHS/RHS\n",checks,failures);return failures?1:0;
#else
'''
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
 out=ROOT/'build/aspect-file-attributes-dos'/args.label;out.mkdir(parents=True,exist_ok=False);stage=out/'drive';stage.mkdir()
 binary=ROOT/'build/aspect-runner/ASPECT.EXE';compiler=ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'
 before={str(p.relative_to(ROOT)):sha(p) for p in (binary,compiler,Path(__file__))}
 for f in (binary,compiler):shutil.copyfile(f,stage/f.name)
 for name,source in SOURCES.items():
  compile_source(source);(stage/(name+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('cp437'))
 valid=compile_source('string value\nproc main\ngetfattr "ATTR.DAT" value\nendproc\n');assert valid[-3:]==b'\x8c\x00\x94';(stage/'TRUNC.ASX').write_bytes(valid[:-3])
 (stage/'ATTR.DAT').write_bytes(b'owned-attributes');(stage/'STREAM.BIN').write_bytes(b'stream');(stage/'FOLDER').mkdir()
 calls=''.join(f' run("{name}.ASX",{error});\n' for name,error in CASES)
 program=C.replace('VALUES',','.join('"'+v+'"' for v in COMBOS))+calls+''' current="baseline";ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<30;++cycle){
'''+calls+''' }
 current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("ATTR_VM %u cases %u checks %u failures farheap%u nearheap%u JFT-preserved\\n",cases,checks,failures,far_count,near_count);return failures?1:0;
#endif
}
'''
 (out/'harness.c').write_text(program)
 cs=['runtime.c','script_file_runtime.c','file_info_runtime.c','file_times_runtime.c','enumeration_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c']
 for native in (False,True):
  name='NATIVE' if native else 'ATTRVM'
  objects=[str(ROOT/'build/aspect-file-attributes/file_attributes.obj') if native and n=='file_attributes' else str(COMPONENT/(n+'.obj')) for n,_,_ in ASM]
  subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC',*(['-dATTR_NATIVE_CONTROL','-wcd=202'] if native else []),'-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm='+str(out/(name+'.map')),'-fe='+str(stage/(name+'.EXE')),str(out/'harness.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/n) for n in cs],*objects],cwd=out,check=True)
 batch=['@echo off']
 for name in SOURCES:
  if name!='CLISRC':batch += [f'ASPCOMP {name}.ASP >{name}.CMP','if errorlevel 1 goto failed']
 batch+=['ASPECT CLISRC.ASP >CLI.LOG','if errorlevel 1 goto failed','NATIVE >NATIVE.TXT','if errorlevel 1 goto failed','ATTRVM >RESULT.TXT','if errorlevel 1 goto failed','echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (stage/'RUN.BAT').write_text('\n'.join(batch)+'\n');(out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{stage}"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=120)
 output=(stage/'RESULT.TXT').read_text() if (stage/'RESULT.TXT').exists() else 'Inspect compiler/CLI/native-control logs'
 assert (stage/'PASS.TXT').exists() and not (stage/'FAIL.TXT').exists(),output
 summary=re.search(r'^ATTR_VM (\d+) cases (\d+) checks 0 failures farheap(\d+) nearheap(\d+) JFT-preserved$',output,re.M);assert summary,output
 native_output=(stage/'NATIVE.TXT').read_text();assert re.search(r'NATIVE_CONTROL \d+ checks 0 failures global=BEFORE near=RHS/RHS/RHS',native_output)
 for name,source in SOURCES.items():assert (stage/(name+'.ASX')).read_bytes()==compile_source(source),name
 assert b'ATTRIBUTE READY' in (stage/'CLI.LOG').read_bytes()
 assert (stage/'ATTR.DAT').read_bytes()==b'owned-attributes' and (stage/'STREAM.BIN').read_bytes()==b'stream'
 assert before=={p:sha(ROOT/p) for p in before}
 report=dict(passed=True,cases=int(summary[1]),assertions=int(summary[2]),same_process_rounds=31,DOS_summary=summary[0],native_control_sha256=sha(stage/'NATIVE.EXE'),native_control_result_sha256=sha(stage/'NATIVE.TXT'),native_control_summary=native_output.strip().splitlines()[-1],native_object_sha256=sha(ROOT/'build/aspect-file-attributes/file_attributes.obj'),runtime_object_sha256=sha(COMPONENT/'file_attributes.obj'),runner_sha256=sha(binary),compiler_sha256=sha(compiler),checker_sha256=sha(Path(__file__)),reused_harness_sha256=sha(Path(base.__file__)),harness_sha256=sha(out/'harness.c'),result_sha256=sha(stage/'RESULT.TXT'),fixtures=SOURCES,original_inputs=[],scope='Actual8086 DOS compiler,production ASP CLI and real VM/DOS43. All16 RHSA masks,case/duplicate letters,missing-get RHSADV with failure1,missing-set raw2,directory getter,global/local/parameter/register destinations,six streams,shared FOUND,EXECUTE and invalid-attribute/truncated-destination aborts. Actual unmodified-native-handler control preserves BEFORE only in far global while near outputs update; maintained handler writes all. Repeated near/far heap/JFT/INT0/FLAGS/ABI cleanup and unchanged file bytes. No physical/complete-language claim.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report['DOS_summary']);print(report['native_control_summary'])
if __name__=='__main__':main()
