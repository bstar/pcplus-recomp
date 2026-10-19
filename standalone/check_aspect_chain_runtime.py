#!/usr/bin/env python3
"""Actual DOS script replacement with real files, far heap and shared VM state."""
import json,os,subprocess,sys
from pathlib import Path
from build_aspect_runtime import ROOT,OUT as COMPONENT,ASM,sha,main as build
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
OUT=ROOT/'build/aspect-chain-runtime'
SOURCES={
 'CSTART': 'integer value,saved\nstring payload\nproc main\nvalue=42\npayload="old allocation"\nset break 1234\nset msg_crlf off\nexecute "cend"\nvalue=99\nendproc\n',
 'CEND': 'integer value,saved\nstring payload\nproc main\nfetch break saved\nmessage payload\nmessage "END"\nendproc\n',
 'CFAR': 'string target\nproc main\ntarget="cend.asx"\nexecute target\nmessage "BAD"\nendproc\n',
 'CLOCAL': 'proc main\ncall worker\nendproc\nproc worker\nstring target\ntarget="cgate.asx"\nexecute target\nmessage "BAD"\nendproc\n',
 'CGATE': 'integer gate\nproc main\nfetch rxdata gate\nendproc\n',
 'CWHEN': 'proc main\nwhen 0 "X" call worker\nexecute "cgate"\nendproc\nproc worker\nmessage "STALE"\nendproc\n',
 'CEMPTY': 'string payload\nproc main\npayload="owned"\nexecute ""\nmessage "BAD"\nendproc\n',
 'CMISS': 'string payload\nproc main\npayload="owned"\nexecute "absent"\nendproc\n',
 'CBAD': 'string payload\nproc main\npayload="owned"\nexecute "bad"\nendproc\n',
 'CASP': 'proc main\nexecute "source.asp"\nendproc\n',
 'CDEVICE': 'proc main\nexecute "CON"\nendproc\n',
 'CNAME': 'proc main\nexecute "bad.exe"\nendproc\n',
 'CSELF': 'string payload\nproc main\npayload="self"\nexecute "cself"\nendproc\n',
 'CONE': 'string a,b\nproc main\na="one"\nexecute "ctwo"\nendproc\n',
 'CTWO': 'string a\nproc main\na="two"\nexecute "cthree"\nendproc\n',
 'CTHREE': 'string a,b,c\nproc main\nmessage "three"\nendproc\n',
 'CFAIL': 'proc main\nexecute "cthree"\nendproc\n',
 'CBANK': 'integer number\nlong wide\nproc main\nnumber=123\nwide=1234567L\nexecute "cbank2"\nendproc\n',
 'CQUEUE': 'proc main\nset rxdata on\ntransmit "GO"\nexecute "cqueue2"\nendproc\n',
 'CQUEUE2': 'integer got,gate\nproc main\nfetch rxdata gate\ncomgetc got\nendproc\n',
 'CBANK2': 'integer number\nlong wide\nproc main\nnumber=number+1\nwide=wide+1L\nendproc\n',
}
# Expectations established from native command/reset/ownership rules before run.
CASES=[
 dict(name='CSTART',error=0,peak=1,cleanup=2,close=2,integer0=42,integer1=1234,output=b'END',string0=b''),
 dict(name='CFAR',error=0,peak=1,cleanup=2,close=2,integer1=350,output=b'\r\nEND\r\n',string0=b''),
 dict(name='CLOCAL',error=0,peak=0,cleanup=2,close=2,integer0=0,output=b''),
 dict(name='CWHEN',error=0,peak=0,cleanup=2,close=2,integer0=0,output=b''),
 dict(name='CEMPTY',error=0,peak=1,cleanup=1,close=1,output=b'',string0=b'owned'),
 dict(name='CMISS',error=1,peak=1,cleanup=1,close=1,output=b''),
 dict(name='CBAD',error=2,peak=1,cleanup=1,close=1,output=b''),
 dict(name='CASP',error=3,peak=0,cleanup=1,close=1,output=b''),
 dict(name='CDEVICE',error=1,peak=0,cleanup=1,close=1,output=b''),
 dict(name='CNAME',error=7,peak=0,cleanup=1,close=1,native=102,output=b''),
 dict(name='CSELF',error=6,peak=1,limit=40,output=b''),
 dict(name='CONE',error=0,peak=3,cleanup=3,close=3,output=b'three\r\n',string0=b''),
 dict(name='CFAIL',error=8,peak=1,cleanup=2,close=2,fail_after=1,output=b''),
 dict(name='CTRUNC',error=5,peak=0,cleanup=1,close=1,output=b''),
 dict(name='CQUEUE',error=0,peak=0,cleanup=2,close=2,integer0=90,integer1=1,output=b''),
 dict(name='CBANK',error=0,peak=0,cleanup=2,close=2,integer0=124,long0=1234568,output=b''),
]
C=r'''
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "runtime.h"
#include "file_io.h"
#include "when_runtime.h"
#include "serial_runtime.h"
extern aspect_file runtime_file;
extern unsigned runtime_string_count,runtime_wait_gate,runtime_depth;
static unsigned cases,checks,failures;
static const char *current;
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL %s check%u error%u opcode%u step%u\n",current,checks,runtime_error,runtime_last_opcode,runtime_steps);}}
static void run(const char *path,unsigned limit,unsigned error,unsigned peak,unsigned fail_after){
 unsigned result,i;void (__interrupt __far *old)(void)=_dos_getvect(0);
 current=path;++cases;runtime_fail_after=fail_after;
 runtime_serial_fixture_disable();
 if(!strcmp(path,"CWHEN.ASX"))runtime_serial_fixture(0,0,0,0,1,0,1);
 if(!strcmp(path,"CQUEUE.ASX"))runtime_serial_fixture((const unsigned char *)"Z",1,(const unsigned char *)"GO",2,1,0,1);
 result=aspect_runtime_run(path,limit);
 ck(result==error);ck(runtime_peak_live==peak);ck(runtime_live==0);
 ck(runtime_file.handle==0);ck(runtime_string_count==0);ck(runtime_depth==0);
 ck(runtime_wait_gate==0);ck(runtime_abi_bad==0);ck(_dos_getvect(0)==old);
 ck(runtime_when_disconnect_armed==0);
 for(i=0;i<3;++i)ck(runtime_when_records[84+i*86]==0&&runtime_when_records[85+i*86]==0);
 printf("CASE %s error%u steps%u peak%u cleanup%u close%u\n",path,result,runtime_steps,runtime_peak_live,runtime_cleanup_count,runtime_close_count);
}
static void output(const unsigned char *value,unsigned count){ck(runtime_console_output_size==count);ck(!memcmp(runtime_console_output,value,count));}
int main(void){
'''
def literal(raw):return '"'+''.join('\\x%02x'%b for b in raw)+'"'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 # Shared component objects are rebuilt once, before this diagnostic reads them.
 with (OUT/'build.log').open('w') as log:
  from contextlib import redirect_stdout
  with redirect_stdout(log):build()
 program=C
 fixtures={}
 for name,source in SOURCES.items():
  wire=compile_source(source);(OUT/(name+'.ASX')).write_bytes(wire)
  fixtures[name]=dict(source=source,asx_sha256=sha(OUT/(name+'.ASX')))
 (OUT/'CTRUNC.ASX').write_bytes(b'\x00\xcf\xcb')
 (OUT/'BAD.ASX').write_bytes(b'\x81');(OUT/'ABSENT.ASX').unlink(missing_ok=True)
 for case in CASES:
  program+=' run("%s.ASX",%u,%u,%u,%u);\n'%(case['name'],case.get('limit',1000),case['error'],case['peak'],case.get('fail_after',65535))
  for key,symbol in [('cleanup','runtime_cleanup_count'),('close','runtime_close_count'),('integer0','runtime_integer_b[0]'),('integer1','runtime_integer_b[1]'),('long0','runtime_longs[0]'),('native','runtime_native_error_code')]:
   if key in case:program+=' ck(%s==%uUL);\n'%(symbol,case[key])
  program+=' output((const unsigned char *)%s,%u);\n'%(literal(case['output']),len(case['output']))
  if 'string0' in case:program+=' ck(!strcmp((char *)runtime_string_snapshot[0],%s));\n'%literal(case['string0'])
  if case['name']=='CSELF':program+=' ck(runtime_steps==40);ck(runtime_cleanup_count==runtime_close_count);ck(runtime_close_count>1);\n'
 program+=' printf("CHAIN %u cases %u checks %u failures\\n",cases,checks,failures);return failures?1:0;}\n'
 (OUT/'harness.c').write_text(program)
 cs=['runtime.c','environment_runtime.c','script_file_runtime.c','file_info_runtime.c','file_times_runtime.c','enumeration_runtime.c','file_io.c','script_path.c','serial_runtime.c','receive_runtime.c','directory_runtime.c','when_runtime.c','set_runtime.c','find_runtime.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dASPECT_RUNTIME_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-fm=CHAIN.map','-fe=CHAIN.EXE',str(OUT/'harness.c'),*[str(ROOT/'src/aspect'/p) for p in cs],*[str(COMPONENT/(name+'.obj')) for name,_,_ in ASM]],cwd=OUT,check=True)
 conf=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nCHAIN >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
 (OUT/'dosbox.conf').write_text(conf)
 for name in ['PASS.TXT','FAIL.TXT','RESULT.TXT']:(OUT/name).unlink(missing_ok=True)
 with (OUT/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 result=(OUT/'RESULT.TXT').read_text();print(result)
 assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),result
 assert f'CHAIN {len(CASES)} cases ' in result and '0 failures' in result,result
 report=dict(passed=True,DOS_summary=result.strip().splitlines()[-1],binary_sha256=sha(OUT/'CHAIN.EXE'),
  runtime_manifest_sha256=sha(COMPONENT/'manifest.json'),checker_sha256=sha(Path(__file__)),result_sha256=sha(OUT/'RESULT.TXT'),fixtures=fixtures,
  cases=[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in case.items()} for case in CASES],original_inputs=[],
  scope='Actual source-built DOS interpreter, files, far allocations and native999 restart. Diagnostic transport and no-renderer end policy. ASP compilation and parent label refresh remain open.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
