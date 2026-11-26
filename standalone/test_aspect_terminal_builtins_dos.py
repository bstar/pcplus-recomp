#!/usr/bin/env python3
"""Exercise live-WORD operand routing in the actual DOS VM with explicit inputs."""
import argparse,json,os,re,subprocess
from pathlib import Path
import test_aspect_script_files_dos as base
from build_aspect_runtime import ROOT,ASM
from compiler import compile_source
sha=base.sha
NAMES=['col','row','scrncols','scrnrows','termbold','termdim','termnorm','termrev','termuline']
GLOBALS='integer '+','.join('v'+str(i) for i in range(9))+',before,after\n'
SOURCES={
 'GLOBAL':GLOBALS+'long '+','.join('l'+str(i) for i in range(9))+'\nproc main\nstrcmp "A" "B"\nbefore=failure\n'+''.join(f'v{i}=${n}\nl{i}=${n}\n' for i,n in enumerate(NAMES))+'after=failure\nendproc\n',
 'LOCAL':GLOBALS+'proc main\ninteger '+','.join('a'+str(i) for i in range(9))+'\n'+''.join(f'a{i}=${n}\nv{i}=a{i}\n' for i,n in enumerate(NAMES))+'endproc\n',
 'PARAM':GLOBALS+'proc main\ncall worker with '+' '.join('$'+n for n in NAMES)+'\nendproc\nproc worker\n'+''.join(f'intparm a{i}\n' for i in range(9))+''.join(f'v{i}=a{i}\n' for i in range(9))+'endproc\n',
 'REG':GLOBALS+'proc main\n'+''.join(f'itoa ${n} s9\natoi s9 v{i}\n' for i,n in enumerate(NAMES))+'endproc\n',
 'SIX':GLOBALS+'proc main\n'+''.join(f'fopen {i} "STREAM.BIN" "rb"\n' for i in range(6))+''.join(f'v{i}=${n}\n' for i,n in enumerate(NAMES))+'endproc\n',
 'CHAIN1':'proc main\nexecute "CHAIN2"\nendproc\n',
 'CHAIN2':GLOBALS+'proc main\n'+''.join(f'v{i}=${n}\n' for i,n in enumerate(NAMES))+'endproc\n',
 'ABSENT':'integer saved\nproc main\nsaved=1234\nsaved=$col\nendproc\n',
 'WHEN':GLOBALS+'proc main\nwhen 0 "A" call worker\ntransmit "READY"\nwaitfor "END" 1\ntransmit "DONE"\nendproc\nproc worker\n'+''.join(f'v{i}=${n}\n' for i,n in enumerate(NAMES))+'transmit "HIT"\nendproc\n'}
C=base.C.split('static void run(')[0]+r'''
#include "terminal_builtins.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
static const unsigned boundaries[]={0,1,79,80,131,132,24,25,0xff,0x100,0x7fff,0x8000,0xff00,0xffff};
static unsigned words[9];
static void run(const char *path,unsigned absent){
 unsigned result,i,flags=cpu_flags();void (__interrupt __far *vector)(void)=_dos_getvect(0);
 current=path;++cases;runtime_terminal_fixture(absent?0:words);
 if(!strcmp(path,"WHEN.ASX")){runtime_serial_fixture((const unsigned char *)"AEND",4,(const unsigned char *)"READY",5,1,0UL,1UL);runtime_receive_fixture(0,1);}
 result=aspect_runtime_run(path,2000);
 if(!strcmp(path,"WHEN.ASX")){ck(runtime_serial_tx_size==12&&!memcmp(runtime_serial_tx,"READYHITDONE",12));runtime_serial_fixture_disable();}
 ck(result==(absent?3:0));ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(!runtime_script_file_live&&!runtime_live&&!runtime_find_live&&!runtime_file.handle&&!runtime_abi_bad);
 for(i=0;i<6;++i)ck(!runtime_script_file_slots[i]);
 if(absent){ck(runtime_integer_b[0]==1234);return;}
 for(i=0;i<9;++i)ck(runtime_integer_b[i]==words[i]);
 if(!strcmp(path,"GLOBAL.ASX")){
  ck(runtime_integer_b[9]==65535U&&runtime_integer_b[10]==65535U);
  for(i=0;i<9;++i)ck(runtime_longs[i]==(unsigned long)(long)(int)words[i]);
 }
 if(!strcmp(path,"SIX.ASX"))ck(runtime_script_file_peak==6&&runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
 if(!strcmp(path,"CHAIN1.ASX"))ck(runtime_cleanup_count==2);
}
int main(void){
 unsigned cycle,i,far_count=0,far_after_count=0,near_count,near_after_count;
 current="warmup";for(i=0;i<9;++i)words[i]=i;
 run("GLOBAL.ASX",0);run("LOCAL.ASX",0);run("PARAM.ASX",0);run("REG.ASX",0);
 run("SIX.ASX",0);run("CHAIN1.ASX",0);run("WHEN.ASX",0);run("ABSENT.ASX",1);
 ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<28;++cycle){
  for(i=0;i<9;++i)words[i]=boundaries[(cycle+i)%14];
  run("GLOBAL.ASX",0);run("LOCAL.ASX",0);run("PARAM.ASX",0);run("REG.ASX",0);
  run("SIX.ASX",0);run("CHAIN1.ASX",0);run("WHEN.ASX",0);run("ABSENT.ASX",1);
  current="direct-refresh";runtime_terminal_fixture(words);
  for(i=0;i<9;++i){runtime_terminal_values[i]=0x4321;ck(!runtime_terminal_refresh(i?i+11:0));ck(runtime_terminal_values[i]==words[i]);}
  ck(runtime_terminal_refresh(11)==7);ck(runtime_terminal_refresh(30)==7);
  runtime_terminal_fixture(0);ck(runtime_terminal_refresh(0)==3);ck(runtime_terminal_values[0]==words[0]);
 }
 current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));
 ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);
 for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("TERMINAL_VM %u cases %u checks %u failures\n",cases,checks,failures);return failures?1:0;
}
'''

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('output','component-dir','compiler-dir'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir();drive=out/'drive';drive.mkdir()
 component=a.component_dir.resolve();compiler=a.compiler_dir.resolve()
 manifests=[json.loads((folder/'manifest.json').read_text()) for folder in (component,compiler)]
 assert manifests[0]['experimental_terminal_builtins']
 sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(Path(base.__file__).relative_to(ROOT)):sha(Path(base.__file__))}
 for m in manifests:
  assert not m['original_inputs']
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 binary=compiler/'ASPCOMP.EXE';assert sha(binary)==manifests[1]['binary_sha256'];(drive/'ASPCOMP.EXE').write_bytes(binary.read_bytes())
 for n,source in SOURCES.items():
  compile_source(source)
  (drive/(n+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('cp437'))
 (drive/'STREAM.BIN').write_bytes(b'preserve-terminal-stream');(out/'terminal.c').write_text(C)
 cs=['runtime.c','environment_runtime.c','script_file_runtime.c','file_info_runtime.c','file_times_runtime.c','enumeration_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c','terminal_builtins.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm='+str(out/'TERMINAL.map'),'-fe='+str(drive/'TBUILT.EXE'),str(out/'terminal.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/n) for n in cs],*[str(component/(n+'.obj')) for n in [*[n for n,_,_ in ASM],'terminal_builtins']]],cwd=out,check=True)
 batch=['@echo off']
 for n in SOURCES:batch+=['ASPCOMP '+n+'.ASP >'+n+'.CMP','if errorlevel 1 goto failed']
 batch+=['TBUILT >RESULT.TXT','if errorlevel 1 goto failed','echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (drive/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=120)
 output=(drive/'RESULT.TXT').read_text() if (drive/'RESULT.TXT').exists() else 'No VM result; inspect compiler logs'
 assert (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),output
 match=re.search(r'TERMINAL_VM (\d+) cases (\d+) checks 0 failures',output);assert match,output
 for n,s in SOURCES.items():assert (drive/(n+'.ASX')).read_bytes()==compile_source(s),n
 assert (drive/'STREAM.BIN').read_bytes()==b'preserve-terminal-stream'
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,cases=int(match[1]),checks=int(match[2]),model_WORD_values=[0,1,79,80,131,132,24,25,255,256,32767,32768,65280,65535],compiler_sha256=sha(binary),sources=sources,original_inputs=[],artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},scope=__doc__+' Explicit nine-WORD diagnostic fixture; no fabricated production defaults. Global/local/parameter/register values, signed long promotion, unchanged compare status, six held files, EXECUTE, WHEN CALL, refusal before destination mutation, direct refresh freshness, repeated heap/JFT/INT0/FLAGS/ABI cleanup. Parent RPC/geometry and physical acceptance require separate tests.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(match[0])

if __name__=='__main__':main()
