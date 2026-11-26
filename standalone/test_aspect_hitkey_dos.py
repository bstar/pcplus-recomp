#!/usr/bin/env python3
"""Actual DOS HITKEY VM lifetimes, explicit peek fixtures and real BIOS rings."""
import argparse,json,os,re,subprocess
from pathlib import Path
import test_aspect_script_files_dos as base
from build_aspect_runtime import ROOT,ASM
from compiler import compile_source
from check_aspect_keyboard import expected
sha=base.sha
DECL='integer first,second,before,after\nlong wide\n'
BODY='first=hitkey\nsecond=hitkey\nwide=hitkey\n'
SOURCES={
 'GLOBAL':DECL+'proc main\nset keys on\nstrcmp "A" "B"\nbefore=failure\n'+BODY+'after=failure\nendproc\n',
 'LOCAL':DECL+'proc main\ninteger a,b\nlong c\nset keys on\na=hitkey\nb=hitkey\nc=hitkey\nfirst=a\nsecond=b\nwide=c\nendproc\n',
 'PARAM':DECL+'proc main\nlong temp\nset keys on\ntemp=hitkey\ncall worker with hitkey hitkey temp\nendproc\nproc worker\nintparm a\nintparm b\nlongparm c\nfirst=a\nsecond=b\nwide=c\nendproc\n',
 'REG':DECL+'proc main\nset keys on\nitoa hitkey s9\natoi s9 first\nsecond=hitkey\nwide=hitkey\nendproc\n',
 'SIX':DECL+'proc main\nset keys on\n'+''.join(f'fopen {i} "STREAM.BIN" "rb"\n' for i in range(6))+BODY+'endproc\n',
 'CHAIN1':'proc main\nexecute "CHAIN2"\nendproc\n',
 'CHAIN2':DECL+'proc main\nset keys on\n'+BODY+'endproc\n',
 'WHEN':DECL+'proc main\nset keys on\nwhen 0 "A" call worker\ntransmit "READY"\nwaitfor "END" 1\ntransmit "DONE"\nendproc\nproc worker\n'+BODY+'transmit "HIT"\nendproc\n',
 'CLI':'integer value\nstring result_text\nproc main\nset keys on\nvalue=hitkey\nitoa value result_text\nfopen 0 "HITKEY.LOG" "wb"\nfputs 0 result_text\nfclose 0\nendproc\n',
 'OFF':'integer saved\nproc main\nsaved=1234\nsaved=hitkey\nendproc\n'}
CASES=[n for n in SOURCES if n not in ('CHAIN2','CLI','OFF')]
RAW=[0,1,0x1e41,0x3920,0x0e08,0x0e7f,0x4800,0x4de0,0xe041,0x3729,0x372a,0x7fff,0x8000,0xff00,0xffff]
# Empty availability deliberately carries a nonzero garbage AX fixture.
VECTORS=[(0,0xdead,0)]+[(1,r,expected(r or 0x100)) for r in RAW]
C=base.C.split('static void run(')[0]+r'''
#include <i86.h>
#include "hitkey.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
extern unsigned runtime_keyboard_mode;
static const unsigned vectors[][3]={VECTORS};
static void run(const char *path,unsigned available,unsigned raw,unsigned value){
 unsigned result,i,flags=cpu_flags();void (__interrupt __far *vector)(void)=_dos_getvect(0);
 current=path;++cases;runtime_hitkey_fixture(1,available,raw);
 if(!strcmp(path,"WHEN.ASX")){runtime_serial_fixture((const unsigned char *)"AEND",4,(const unsigned char *)"READY",5,1,0UL,1UL);runtime_receive_fixture(0,1);}
 result=aspect_runtime_run(path,2000);
 if(cases<=7)printf("HITKEYCASE %s result%u value%u expected%u\n",path,result,runtime_integer_b[0],value);
 if(!strcmp(path,"WHEN.ASX")){ck(runtime_serial_tx_size==12&&!memcmp(runtime_serial_tx,"READYHITDONE",12));runtime_serial_fixture_disable();}
 ck(!result);ck(runtime_hitkey_fixture_peeks==3);ck(runtime_integer_b[0]==value&&runtime_integer_b[1]==value);
 ck(runtime_longs[0]==(unsigned long)(long)(int)value);
 ck(_dos_getvect(0)==vector);ck((cpu_flags()&0x600)==(flags&0x600));
 ck(!runtime_script_file_live&&!runtime_live&&!runtime_find_live&&!runtime_file.handle&&!runtime_abi_bad);
 for(i=0;i<6;++i)ck(!runtime_script_file_slots[i]);
 if(!strcmp(path,"GLOBAL.ASX"))ck(runtime_integer_b[2]==65535U&&runtime_integer_b[3]==65535U);
 if(!strcmp(path,"SIX.ASX"))ck(runtime_script_file_peak==6&&runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
 if(!strcmp(path,"CHAIN1.ASX"))ck(runtime_cleanup_count==2);
}
static void bios(void){
 volatile unsigned __far *bda=(volatile unsigned __far *)MK_FP(0x40,0);
 unsigned saved[18],mode,oldmode=runtime_keyboard_mode,flags=cpu_flags(),i,start=checks;
 current="real-BIOS-nonconsuming";runtime_hitkey_fixture(0,0,0);
 _disable();saved[0]=bda[13];saved[1]=bda[14];for(i=0;i<16;++i)saved[i+2]=bda[15+i];
 for(mode=0;mode<=0x10;mode+=0x10){
  runtime_keyboard_mode=mode;bda[13]=0x1e;bda[14]=0x20;bda[15]=0x1e41;
  if(flags&0x200)_enable();
  ck(!runtime_hitkey_refresh()&&runtime_hitkey_value==0x41);ck(!runtime_hitkey_refresh()&&runtime_hitkey_value==0x41);
  ck(bda[13]==0x1e&&bda[14]==0x20&&bda[15]==0x1e41);
  _disable();bda[14]=0x1e;if(flags&0x200)_enable();
  ck(!runtime_hitkey_refresh()&&!runtime_hitkey_value);ck(bda[13]==bda[14]);_disable();
 }
 bda[13]=saved[0];bda[14]=saved[1];for(i=0;i<16;++i)bda[15+i]=saved[i+2];
 runtime_keyboard_mode=oldmode;if(flags&0x200)_enable();
 ck((cpu_flags()&0x600)==(flags&0x600));printf("HITKEY_BIOS %u checks\n",checks-start);
}
int main(void){
 unsigned cycle,i,far_count=0,far_after_count=0,near_count,near_after_count;
 WARMUP
 current="baseline";ck(compiler_far_heap_snapshot(far_before,128,&far_count)==0);near_count=near_snapshot(near_before);jft(jft_before);
 for(cycle=0;cycle<32;++cycle){unsigned index=cycle%16;CALLS}
 bios();current="final";jft(jft_after);ck(!memcmp(jft_before,jft_after,20));
 ck(compiler_far_heap_snapshot(far_after,128,&far_after_count)==0);ck(far_count==far_after_count);
 for(i=0;i<far_count&&i<far_after_count;++i)ck(far_before[i]._pentry==far_after[i]._pentry&&far_before[i]._size==far_after[i]._size);
 near_after_count=near_snapshot(near_after);ck(near_count==near_after_count);
 for(i=0;i<near_count&&i<near_after_count;++i)ck(near_before[i]._pentry==near_after[i]._pentry&&near_before[i]._size==near_after[i]._size);
 printf("HITKEY_VM %u cases %u checks %u failures\n",cases,checks,failures);return failures?1:0;
}
'''

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('component-dir','compiler-dir','runner-dir','disabled-component-dir','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir();drive=out/'drive';drive.mkdir()
 sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(Path(base.__file__).relative_to(ROOT)):sha(Path(base.__file__)), 'standalone/check_aspect_keyboard.py':sha(ROOT/'standalone/check_aspect_keyboard.py')}
 for folder,leaf in [(a.component_dir,'EXECUTE.EXE'),(a.compiler_dir,'ASPCOMP.EXE'),(a.runner_dir,'ASPECT.EXE')]:
  m=json.loads((folder/'manifest.json').read_text());assert m.get('original_inputs',[])==[] and sha(folder/leaf)==m['binary_sha256']
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
  if leaf!='EXECUTE.EXE':(drive/leaf).write_bytes((folder/leaf).read_bytes())
 for n,s in SOURCES.items():compile_source(s);(drive/(n+'.ASP')).write_bytes(s.replace('\n','\r\n').encode('cp437'))
 (drive/'STREAM.BIN').write_bytes(b'preserve-hitkey-stream')
 calls=''.join('run("'+n+'.ASX",vectors[index][0],vectors[index][1],vectors[index][2]);' for n in CASES)
 warm=''.join('run("'+n+'.ASX",1,0x1e41,0x41);' for n in CASES)
 program=C.replace('VECTORS',','.join('{'+','.join(str(v) for v in row)+'}' for row in VECTORS)).replace('WARMUP',warm).replace('CALLS',calls)
 (out/'hitkey_driver.c').write_text(program)
 cs=['runtime.c','environment_runtime.c','script_file_runtime.c','file_info_runtime.c','file_times_runtime.c','enumeration_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c','hitkey.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fe='+str(drive/'HITKEY.EXE'),str(out/'hitkey_driver.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/n) for n in cs],*[str(a.component_dir.resolve()/(n+'.obj')) for n in [*[n for n,_,_ in ASM],'hitkey']]],cwd=out,check=True)
 disabled=a.disabled_component_dir.resolve();dm=json.loads((disabled/'manifest.json').read_text());assert not dm['experimental_hitkey']
 for n,h in dm['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 (out/'disabled.c').write_text('#include <stdio.h>\n#include "runtime.h"\n#include "script_file_runtime.h"\nint main(void){unsigned result=aspect_runtime_run("OFF.ASX",1000);printf("HITKEY_DISABLED error%u saved%u\\n",result,runtime_integer_b[0]);return result!=3||runtime_integer_b[0]!=1234||runtime_live||runtime_script_file_live;}\n')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-fe='+str(drive/'DISABLED.EXE'),str(out/'disabled.c'),*[str(ROOT/'src/aspect'/n) for n in cs if n!='hitkey.c'],*[str(disabled/(n+'.obj')) for n,_,_ in ASM]],cwd=out,check=True)
 batch=['@echo off']
 for n in SOURCES:batch+=['ASPCOMP '+n+'.ASP >'+n+'.CMP','if errorlevel 1 goto failed']
 batch+=['ASPECT CLI.ASP >CLI.LOG','if errorlevel 1 goto failed','HITKEY >RESULT.TXT','if errorlevel 1 goto failed','DISABLED >OFF.LOG','if errorlevel 1 goto failed','echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done','exit']
 (drive/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=120)
 output=(drive/'RESULT.TXT').read_text() if (drive/'RESULT.TXT').exists() else 'No VM result; inspect compiler logs'
 assert (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),output
 match=re.search(r'HITKEY_VM (\d+) cases (\d+) checks 0 failures',output);assert match,output
 assert 'HITKEY_BIOS 11 checks' in output and (drive/'HITKEY.LOG').read_bytes()==b'0'
 assert (drive/'OFF.LOG').read_text().strip()=='HITKEY_DISABLED error3 saved1234'
 for n,s in SOURCES.items():assert (drive/(n+'.ASX')).read_bytes()==compile_source(s),n
 assert (drive/'STREAM.BIN').read_bytes()==b'preserve-hitkey-stream'
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 r=dict(passed=True,cases=int(match[1]),checks=int(match[2]),real_BIOS_checks=11,disabled_feature_guard=True,disabled_cases=1,fixture_vectors=VECTORS,sources=sources,original_inputs=[],artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},scope=__doc__+' Explicit diagnostic peek fixtures cover signed fullword results, repeated reads under the native KEYS ON keyboard-disable word, unchanged comparison, globals/locals/parameters/string-register conversion, six held streams, WHEN CALL and EXECUTE with repeated heap/JFT/INT0/FLAGS/ABI cleanup. Direct tests use actual DOSBox standard/enhanced BIOS rings without consuming the queued key and restore their exact initial state. Production standalone CLI runs against empty actual BIOS; feature-disabled bridge rejects before replacing saved1234. Parent RPC/mouse producer and physical hardware remain separate.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(match[0])

if __name__=='__main__':main()
