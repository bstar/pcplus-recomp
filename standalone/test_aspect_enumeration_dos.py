#!/usr/bin/env python3
"""Actual DOS file searches, builtin snapshots, DTA ownership and VM lifetimes."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
import test_aspect_script_files_dos as base
from build_aspect_runtime import ROOT,ASM,OUT as COMPONENT
from compiler import compile_source
sha=base.sha
DECL='''integer count,done,text_found,first_found
long total,first_size
string filename,basename,ext,attrs,filedate,filetime,last,saved,stale
'''
SOURCES={
'ENUM':DECL+'''proc main
findnext
first_found=found
findfirst "FILES\\*.ZIP"
while found
count+=1
total+=$FSIZE
if count==1
filename=$FILENAME
basename=$FNAME
ext=$FEXT
attrs=$FATTR
filedate=$FDATE
filetime=$FTIME
first_size=$FSIZE
endif
last=$FILENAME
find "ABC" "Z"
text_found=found
findnext
endwhile
done=found
endproc
''',
'NONE':DECL+'''proc main
findfirst "FILES\\ALPHA.ZIP"
saved=$FILENAME
findfirst "FILES\\MISSING.*"
done=found
stale=$FILENAME
total=$FSIZE
endproc
''',
'FLAGS':DECL+'''proc main
findfirst "FILES\\*.HID" "h"
first_found=found
filename=$FILENAME
attrs=$FATTR
total=$FSIZE
findnext
done=found
endproc
''',
'DIRECT':DECL+'''proc main
findfirst "FILES\\SUB" "D"
first_found=found
filename=$FILENAME
basename=$FNAME
ext=$FEXT
attrs=$FATTR
findnext
done=found
endproc
''',
'RAW':DECL+'''proc main
findfirst "FILES\\ALPHA.ZIP" ""
first_found=found
filename=$FILENAME
basename=$FNAME
ext=$FEXT
filedate=$FDATE
filetime=$FTIME
endproc
''',
'REPLACE':DECL+'''proc main
findfirst "FILES\\*.ZIP"
findfirst "FILES\\*.HID" "H"
filename=$FILENAME
findnext
done=found
endproc
''',
'CHAIN1':DECL+'''proc main
findfirst "FILES\\*.ZIP"
if found
count=1
total=$FSIZE
execute "CHAIN2"
endif
endproc
''',
'CHAIN2':DECL+'''proc main
findnext
if found
count+=1
total+=$FSIZE
endif
findnext
done=found
endproc
''',
'BADATTR':'''proc main
findfirst "FILES\\*.ZIP" "?"
endproc
''',
'LONGMASK':DECL+'proc main\nfindfirst \"'+'A'*80+'\"\ndone=found\nendproc\n',
'CLISRC':'''proc main
findfirst "FILES\\*.ZIP"
if found
message $FILENAME
message "ENUM READY"
endif
endproc
''',
}
CASES=[('ENUM',0),('NONE',0),('FLAGS',0),('DIRECT',0),('RAW',0),('REPLACE',0),('CHAIN1',0),('BADATTR',7),('TRUNC',5),('LONGMASK',0)]
C=base.C.split('static void run(')[0].replace('#include "script_file_runtime.h"','#include "script_file_runtime.h"\n#include "file_info_runtime.h"\n#include "enumeration_runtime.h"')+r'''
#include <fcntl.h>
extern unsigned runtime_enum_first(unsigned),runtime_enum_next(unsigned);
extern void enum_fix_result(void);
extern unsigned char enum_mask[81],enum_line[44],enum_dta[43],enum_filename[13],enum_attr,enum_attributes[7];
extern unsigned enum_extension;
static unsigned char sentinel[64],null_before[32],null_after[32];
static void __far *get_dta(void){union REGS in,out;struct SREGS seg;in.h.ah=0x2f;intdosx(&in,&out,&seg);return MK_FP(seg.es,out.x.bx);}
static void set_dta(void __far *p){union REGS in,out;struct SREGS seg;segread(&seg);seg.ds=FP_SEG(p);in.x.dx=FP_OFF(p);in.h.ah=0x1a;intdosx(&in,&out,&seg);}
static void stamp(const char *path,unsigned attr){int h;ck(_dos_setfileattr(path,0)==0);ck(_dos_open(path,O_RDWR,&h)==0);ck(_dos_setftime(h,(13<<9)|(3<<5)|7,(13<<11)|(45<<5))==0);ck(_dos_close(h)==0);ck(_dos_setfileattr(path,attr)==0);}
static void backend(void){struct find_t foreign,copy;void __far *previous=get_dta();struct SREGS seg;
 current="backend";runtime_enumeration_reset();memset(sentinel,0x6b,sizeof(sentinel));set_dta(sentinel);
 ck(runtime_enum_next(1)==0&&get_dta()==(void __far *)sentinel);
 strcpy((char *)enum_mask,"FILES\\*.ZIP");ck(runtime_enum_first(1)==1);ck(get_dta()==(void __far *)sentinel);
 ck(_dos_findfirst("FILES\\*.HID",2,&foreign)==0);memcpy(&copy,&foreign,sizeof(copy));ck(get_dta()==(void __far *)&foreign);
 ck(runtime_enum_next(1)==1);ck(get_dta()==(void __far *)&foreign);ck(!memcmp(&foreign,&copy,sizeof(copy)));
 ck(runtime_enum_next(1)==0&&get_dta()==(void __far *)&foreign);
 /* Original volume fixup writes through null when a label has no dot.
  * Exercise the actual linked runtime admission guard without a fake kernel. */
 memset(enum_line,0,44);memcpy(enum_line,"VOLUME      ",12);strcpy((char *)enum_filename,"VOLUME");enum_attr=8;
 segread(&seg);_fmemcpy(null_before,MK_FP(seg.ds,0),32);enum_fix_result();_fmemcpy(null_after,MK_FP(seg.ds,0),32);
 ck(!memcmp(null_before,null_after,32));ck(!strcmp((char *)enum_line,"VOLUME"));ck(!strcmp((char *)enum_filename,"VOLUME"));ck(!strcmp((char *)enum_attributes,"V"));ck(!*(char *)enum_extension);
 set_dta(previous);runtime_enumeration_reset();
}
static void run(const char *path,unsigned expected){unsigned result,i,flags=cpu_flags();void (__interrupt __far *vector)(void)=_dos_getvect(0);current=path;++cases;
 memset(sentinel,0x6b,sizeof(sentinel));set_dta(sentinel);
 result=aspect_runtime_run(path,2000);ck(result==expected);ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(get_dta()==(void __far *)sentinel);for(i=0;i<64;++i)ck(sentinel[i]==0x6b);
 ck(!runtime_file_info_live&&!runtime_script_file_live&&!runtime_live&&!runtime_find_live&&!runtime_file.handle&&!runtime_abi_bad);
 if(!strcmp(path,"ENUM.ASX")){
  ck(runtime_integer_b[0]==2&&runtime_integer_b[1]==0&&runtime_integer_b[2]==0&&runtime_integer_b[3]==0);ck(runtime_longs[0]==70004UL);
  ck(!strcmp((char *)runtime_string_snapshot[2],"ZIP"));ck(!strcmp((char *)runtime_string_snapshot[4],"3-07-93"));ck(!strcmp((char *)runtime_string_snapshot[5],"13:45"));
  if(!strcmp((char *)runtime_string_snapshot[0],"ALPHA.ZIP")){ck(!strcmp((char *)runtime_string_snapshot[1],"ALPHA"));ck(runtime_longs[1]==70001UL);ck(strchr((char *)runtime_string_snapshot[3],'R')!=0);ck(!strcmp((char *)runtime_string_snapshot[6],"BETA.ZIP"));}
  else{ck(!strcmp((char *)runtime_string_snapshot[0],"BETA.ZIP"));ck(!strcmp((char *)runtime_string_snapshot[1],"BETA"));ck(runtime_longs[1]==3);ck(!strcmp((char *)runtime_string_snapshot[6],"ALPHA.ZIP"));}
 }else if(!strcmp(path,"NONE.ASX")){
  ck(runtime_integer_b[1]==0&&runtime_longs[0]==70001UL);ck(!strcmp((char *)runtime_string_snapshot[7],"ALPHA.ZIP"));ck(!strcmp((char *)runtime_string_snapshot[8],"ALPHA.ZIP"));
 }else if(!strcmp(path,"FLAGS.ASX")){
  ck(runtime_integer_b[3]==1&&runtime_integer_b[1]==0&&runtime_longs[0]==5);ck(!strcmp((char *)runtime_string_snapshot[0],"SECRET.HID"));ck(strchr((char *)runtime_string_snapshot[3],'H')!=0);
 }else if(!strcmp(path,"DIRECT.ASX")){
  ck(runtime_integer_b[3]==1&&runtime_integer_b[1]==0);ck(!strcmp((char *)runtime_string_snapshot[0],"SUB"));ck(!strcmp((char *)runtime_string_snapshot[1],"SUB"));ck(!runtime_string_snapshot[2][0]);ck(strchr((char *)runtime_string_snapshot[3],'D')!=0);
 }else if(!strcmp(path,"RAW.ASX")){
  ck(runtime_integer_b[3]==1);ck(!strcmp((char *)runtime_string_snapshot[0],"ALPHA.ZIP"));ck(!strcmp((char *)runtime_string_snapshot[1],"ALPHA"));ck(!strcmp((char *)runtime_string_snapshot[2],"ZIP"));ck(!runtime_string_snapshot[4][0]&&!runtime_string_snapshot[5][0]);
 }else if(!strcmp(path,"REPLACE.ASX")){ck(!strcmp((char *)runtime_string_snapshot[0],"SECRET.HID"));ck(runtime_integer_b[1]==0);}
 else if(!strcmp(path,"LONGMASK.ASX")){ck(runtime_integer_b[1]==0);ck(strlen((char *)enum_mask)==80);}
 else if(!strcmp(path,"CHAIN1.ASX"))ck(runtime_integer_b[0]==2&&runtime_integer_b[1]==0&&runtime_longs[0]==70004UL);
 printf("CASE %s error%u DTA-preserved\n",path,result);
}
int main(void){unsigned cycle,far_count=0,far_after_count=0,near_count,near_after_count,i;void __far *previous=get_dta();
 current="stamp";stamp("FILES\\ALPHA.ZIP",1);stamp("FILES\\BETA.ZIP",0);stamp("FILES\\SECRET.HID",2);backend();
'''
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
 out=ROOT/'build/aspect-enumeration-dos'/args.label;out.mkdir(parents=True,exist_ok=False);stage=out/'drive';stage.mkdir()
 binary=ROOT/'build/aspect-runner/ASPECT.EXE';compiler=ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'
 before={str(p.relative_to(ROOT)):sha(p) for p in (binary,compiler,Path(__file__))}
 for f in (binary,compiler):shutil.copyfile(f,stage/f.name)
 for name,source in SOURCES.items():
  compile_source(source);(stage/(name+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('cp437'))
 empty=compile_source('proc main\nfindfirst "FILES\\*.ZIP"\nendproc\n');assert empty[-2:]==b'\x00\x94';(stage/'TRUNC.ASX').write_bytes(empty[:-2])
 files=stage/'FILES';files.mkdir();(files/'SUB').mkdir()
 expected={'ALPHA.ZIP':bytes(i&255 for i in range(70001)),'BETA.ZIP':b'ZIP','SECRET.HID':b'HELLO'}
 for name,data in expected.items():(files/name).write_bytes(data)
 calls=''.join(f' run("{name}.ASX",{error});\n' for name,error in CASES)
 program=C+calls+''' current="baseline";ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<30;++cycle){
'''+calls+''' }
 current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 set_dta(previous);printf("ENUM_VM %u cases %u checks %u failures farheap%u nearheap%u DTA-JFT-preserved\\n",cases,checks,failures,far_count,near_count);return failures?1:0;}
'''
 (out/'harness.c').write_text(program)
 cs=['runtime.c','script_file_runtime.c','file_info_runtime.c','file_times_runtime.c','enumeration_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm='+str(out/'ENUMVM.map'),'-fe='+str(stage/'ENUMVM.EXE'),str(out/'harness.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/n) for n in cs],*[str(COMPONENT/(name+'.obj')) for name,_,_ in ASM]],cwd=out,check=True)
 batch=['@echo off']
 for name in SOURCES:
  if name!='CLISRC':batch += [f'ASPCOMP {name}.ASP >{name}.CMP','if errorlevel 1 goto failed']
 batch+=['ASPECT CLISRC.ASP >CLI.LOG','if errorlevel 1 goto failed','ENUMVM >RESULT.TXT','if errorlevel 1 goto failed','echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (stage/'RUN.BAT').write_text('\n'.join(batch)+'\n');(out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{stage}"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=120)
 output=(stage/'RESULT.TXT').read_text() if (stage/'RESULT.TXT').exists() else 'Inspect compiler/CLI logs'
 assert (stage/'PASS.TXT').exists() and not (stage/'FAIL.TXT').exists(),output
 summary=re.search(r'^ENUM_VM (\d+) cases (\d+) checks 0 failures farheap(\d+) nearheap(\d+) DTA-JFT-preserved$',output,re.M);assert summary,output
 for name,source in SOURCES.items():assert (stage/(name+'.ASX')).read_bytes()==compile_source(source),name
 assert b'ENUM READY' in (stage/'CLI.LOG').read_bytes()
 for name,data in expected.items():assert (files/name).read_bytes()==data,name
 assert before=={p:sha(ROOT/p) for p in before}
 report=dict(passed=True,cases=int(summary[1]),assertions=int(summary[2]),same_process_rounds=31,DOS_summary=summary[0],runner_sha256=sha(binary),compiler_sha256=sha(compiler),checker_sha256=sha(Path(__file__)),reused_harness_sha256=sha(Path(base.__file__)),harness_sha256=sha(out/'harness.c'),result_sha256=sha(stage/'RESULT.TXT'),fixtures=SOURCES,original_inputs=[],scope='Actual8086 DOS compiler, production ASP CLI and full native VM. File enumeration/builtins,readonly/hidden/directory/empty flags,shared FIND status,no-match stale results,search replacement and EXECUTE continuity. Foreign DTA and contents preserved across kernel calls,unrelated CRT find_t context unchanged,volume no-dot null-write guard. Repeated near/far heap,JFT,INT0,FLAGS,ABI cleanup and unchanged file bytes. No physical hardware or complete language claim.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report['DOS_summary'])
if __name__=='__main__':main()
