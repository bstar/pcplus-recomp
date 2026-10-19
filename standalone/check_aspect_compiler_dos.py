#!/usr/bin/env python3
"""Complete maintained ASX grammar under8086 DOS, compared with host output."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
from build_aspect_compiler_dos import ROOT,OUT,MODULES,sha,main as build
from check_aspect_compiler_lexer import source_corpus
sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler
EDGES={
 'pruned-chain':b'proc first\ncall second\nendproc\nproc second\nmessage "unused"\nendproc\nproc main\nmessage "main"\nendproc\n',
 'dead-mutual-cycle':b'proc first\ncall second\nendproc\nproc second\ncall first\nendproc\nproc main\nexit\nendproc\n',
 'unused-invalid':b'proc first\nunknown\nendproc\nproc main\nexit\nendproc\n',
 'unused-initializer-invalid':b'proc first\ninteger a="bad"\nendproc\nproc main\nexit\nendproc\n',
 'typed-parameters':b'integer g\nlong l\nfloat f\nstring s\nproc main\ncall worker with g l f s\nendproc\nproc worker\nintparm p\nlongparm q\nfloatparm r\nstrparm z\ninteger local=1,second=2\nmessage z\nendproc\n',
 'nested-loop-exit':b'integer a\nproc main\nwhile a\nif a\nswitch a\ncase 1\nexitwhile\nendcase\ndefault\nloopwhile\nendcase\nendswitch\nelse\na=0\nendif\nendwhile\nendproc\n',
 'bytecode-over64k':b'proc main\n'+b'message "abcdefghij"\n'*6000+b'call last\nendproc\nproc last\nmessage "tail"\nendproc\n',
 'large-pruned-tail':b'proc main\nmessage "main"\nendproc\nproc removed\n'+b'message "discarded"\n'*3000+b'endproc\n',
 'conditions-over64k':b'integer i\nproc main\nif i\n'+b'message "abcdefghij"\n'*5000+b'elseif i+1\ni=2\nelse\ni=3\nendif\nendproc\n',
}
HARNESS=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <malloc.h>
#include <process.h>
#include <dos.h>
#include <io.h>
#include "compiler_program.h"
#include "compiler_heap_snapshot.h"
static unsigned checks,failures;
static struct _heapinfo before[128],after[128];
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL API check%u\n",checks);}}
static void same_heap(unsigned count){
 unsigned n=0,i;ck(compiler_far_heap_snapshot(after,128,&n)==0);ck(n==count);
 for(i=0;i<n&&i<count;++i)ck(before[i]._pentry==after[i]._pentry&&before[i]._size==after[i]._size);
}
static void ownership(void){
 FILE *input,*output;unsigned char *foreign;unsigned baseline=0;unsigned long i,calls,unit_calls;
 aspect_compiler_report report;aspect_compiler_options options;
 input=fopen("OWNER.ASP","rb");output=fopen("OWNER.ASX","w+b");ck(input!=0&&output!=0);if(!input||!output)return;
 ck(aspect_compiler_program(input,output,&report)==0);calls=report.allocation_calls;unit_calls=report.unit_allocation_calls;
 foreign=malloc(37);ck(foreign!=0);if(!foreign)return;memset(foreign,0x5a,37);
 ck(compiler_far_heap_snapshot(before,128,&baseline)==0);
 for(i=0;i<calls;++i){
  rewind(input);rewind(output);options.fail_after=i;options.unit_fail_after=ULONG_MAX;
  ck(aspect_compiler_program_options(input,output,&report,&options)==ASPECT_COMPILE_HEAP);
  ck(report.allocation_calls==i+1);ck(ftell(input)>=0&&!ferror(input));ck(ftell(output)>=0&&!ferror(output));same_heap(baseline);
 }
 for(i=0;i<unit_calls;++i){
  rewind(input);rewind(output);options.fail_after=ULONG_MAX;options.unit_fail_after=i;
  ck(aspect_compiler_program_options(input,output,&report,&options)==ASPECT_COMPILE_HEAP);
  ck(report.unit_allocation_calls==i+1);same_heap(baseline);
 }
 for(i=0;i<100;++i){rewind(input);rewind(output);ck(aspect_compiler_program(input,output,&report)==0);same_heap(baseline);}
 ck(foreign[0]==0x5a&&foreign[36]==0x5a);free(foreign);ck(fclose(input)==0);ck(fclose(output)==0);
 printf("OWNERSHIP %lu program and%lu inventory failures,100 successful cycles\n",calls,unit_calls);
 input=fopen("OWNER.ASP","r+b");ck(input!=0);if(!input)return;
 ck(aspect_compiler_program(input,input,&report)==ASPECT_COMPILE_STATE);ck(fclose(input)==0);
 input=fopen("OWNER.ASP","rb");output=fopen("OWNER.ASX","rb");ck(input!=0&&output!=0);if(!input||!output)return;
 ck(aspect_compiler_program(input,output,&report)==5&&report.output_status==ASPECT_OUTPUT_IO);
 ck(fclose(input)==0);ck(fclose(output)==0);
}
static void cli(const char *source,const char *target,unsigned expected){
 int status;if(target)status=spawnl(P_WAIT,"ASPCOMP.EXE","ASPCOMP",source,target,(char *)0);
 else status=spawnl(P_WAIT,"ASPCOMP.EXE","ASPCOMP",source,(char *)0);ck(status==expected);
}
static void publication(void){
 FILE *f;struct find_t found;
 cli("GOOD.ASP",0,0);cli("GOOD",0,0);cli("GOOD.ASP","NEW.ASX",0);
 cli("BAD.ASP",0,1);cli("BAD.ASP","PRESERVE.ASX",1);
 cli("GOOD.ASP","GOOD.ASP",64);cli("MISSING.ASP",0,1);
 cli("GOOD.ASP","DIR.ASX",2);cli("GOOD.ASP","ABSENT\\OUT.ASX",2);
 cli("GOOD.ASP","REPLACE.ASX",0);cli("BUILD.ASP",0,0);
 ck(spawnl(P_WAIT,"FAULT.EXE","FAULT","GOOD.ASP","RBKEEP.ASX",(char *)0)==2);
 ck(spawnl(P_WAIT,"FAILBACK.EXE","FAILBACK","GOOD.ASP","RBLOST.ASX",(char *)0)==2);
 ck(access("RBLOST.ASX",0)!=0);ck(access("LPC00001.BAK",0)==0);
 ck(rename("LPC00001.BAK","RBLOST.ASX")==0);
 ck(spawnl(P_WAIT,"ASPECT.EXE","ASPECT","BUILD.ASX",(char *)0)==0);
 f=fopen("PRESERVE.ASX","rb");ck(f!=0);if(f){char b[8];ck(fread(b,1,8,f)==8&&!memcmp(b,"ORIGINAL",8));ck(fclose(f)==0);}
 ck(_dos_findfirst("LPC*.TMP",_A_NORMAL,&found)!=0);ck(_dos_findfirst("LPC*.BAK",_A_NORMAL,&found)!=0);
}
int main(void){
 FILE *list,*results,*input,*output;char source[13],target[13];unsigned index=0,expected,status,failed=0;
 aspect_compiler_report report;
 list=fopen("CASES.LST","rt");results=fopen("RESULTS.TXT","wt");if(!list||!results)return 99;
 while(fscanf(list,"%12s %12s %u",source,target,&expected)==3){
  input=fopen(source,"rb");output=fopen(target,"w+b");if(!input||!output)return 98;
  status=aspect_compiler_program(input,output,&report);
  if((status!=0)!=expected){++failed;printf("FAIL %u %s status%u expected%u\n",index,source,status,expected);}
  fprintf(results,"%u %u %lu %lu %lu %lu %lu %u %u\n",index,status,report.line,report.offset,report.bytes,report.procedures,report.emitted_procedures,report.lexical_status,report.output_status);
  if(fclose(input)||fclose(output))return 97;++index;
 }
 if(fclose(results)||fclose(list))return 96;
 ownership();publication();printf("API %u checks %u failures\n",checks,failures);
 printf("PROGRAM %u cases %u failures\n",index,failed);return failed||failures?1:0;
}
'''
def main():
 build();(OUT/'checks.json').unlink(missing_ok=True);cases,fixtures=source_corpus()
 cases.extend(dict(raw=raw,references=['program:'+name]) for name,raw in EDGES.items())
 answers=[];folder=OUT/'tests';folder.mkdir(exist_ok=True);listing=[]
 for i,case in enumerate(cases):
  try:answer=dict(accepted=True,data=compiler.compile_source(case['raw'].decode('cp437')))
  except (compiler.CompileError,TypeError,OverflowError) as error:answer=dict(accepted=False,error_type=type(error).__name__,error=str(error))
  answers.append(answer);name=f'P{i:05}.ASP';target=f'P{i:05}.ASX';(folder/name).write_bytes(case['raw'])
  listing.append(f"{name} {target} {int(not answer['accepted'])}\n")
 (folder/'CASES.LST').write_text(''.join(listing));(folder/'harness.c').write_text(HARNESS)
 shutil.copyfile(OUT/'ASPCOMP.EXE',folder/'ASPCOMP.EXE')
 shutil.copyfile(ROOT/'build/aspect-runner/ASPECT.EXE',folder/'ASPECT.EXE')
 owner=b'integer i\nstring s\nproc unused\nmessage "unused"\nendproc\nproc main\ninteger n=0,m=1\nwhile n<2\nif n\ncall worker\nelse\nwhen 1 "x" call worker\nendif\nswitch n\ncase 0\nn+=1\nendcase\ndefault\nexitwhile\nendcase\nendswitch\nendwhile\nendproc\nproc worker\nmessage "worker"\nendproc\n'
 good=b'proc main\nmessage "DOS compiler"\nendproc\n'
 runtime=b'integer i\nstring s\nproc main\ni=0\nwhile i<3\nitoa i s\nmessage s\ni++\nendwhile\ncall worker\nendproc\nproc worker\nmessage "COMPILED IN DOS"\nendproc\n'
 (folder/'OWNER.ASP').write_bytes(owner);(folder/'GOOD.ASP').write_bytes(good);(folder/'BAD.ASP').write_bytes(b'proc main\nunknown\nendproc\n');(folder/'BUILD.ASP').write_bytes(runtime)
 (folder/'PRESERVE.ASX').write_bytes(b'ORIGINAL');(folder/'REPLACE.ASX').write_bytes(b'OLD'*1000);(folder/'DIR.ASX').mkdir(exist_ok=True)
 for name in ('RBKEEP.ASX','RBLOST.ASX'):(folder/name).write_bytes(b'PREVIOUS VALID OUTPUT')
 for name in ('GOOD.ASX','NEW.ASX','BAD.ASX','BUILD.ASX'):(folder/name).unlink(missing_ok=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-fpc','-ecc','-s','-w4','-we','-k32768','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm=PROGRAM.map','-fe=PROGRAM.EXE',str(folder/'harness.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/(n+'.c')) for n in MODULES]],cwd=folder,check=True)
 # Only these diagnostic CLIs replace rename. All successful operations still
 # execute the real DOS filesystem call; normal ASPCOMP links no fault hook.
 for binary,restore_failure in (('FAULT',0),('FAILBACK',1)):
  fault=folder/'fault.c';fault.write_text('#include <stdio.h>\n#include <errno.h>\nstatic unsigned calls;\nint __watcall pc_test_rename(const char *a,const char *b){++calls;if(calls==2'+('||calls==3' if restore_failure else '')+'){errno=EACCES;return -1;}return rename(a,b);}\n')
  subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-c','-fo=fault.o',str(fault)],cwd=folder,check=True)
  subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-fpc','-ecc','-s','-w4','-we','-k32768','-drename=pc_test_rename','-fe='+binary+'.EXE',*[str(ROOT/'src/aspect'/(n+'.c')) for n in MODULES],str(ROOT/'src/aspect/compiler_main.c'),'fault.o'],cwd=folder,check=True)
 for name in ('PASS.TXT','FAIL.TXT','RUN.TXT','RESULTS.TXT'):(folder/name).unlink(missing_ok=True)
 config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{folder}"\nc:\nPROGRAM >RUN.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=240)
 run=(folder/'RUN.TXT').read_text();print(run)
 rows=[list(map(int,line.split())) for line in (folder/'RESULTS.TXT').read_text().splitlines()];assert len(rows)==len(cases)
 records=[];mismatches=[]
 for i,(case,answer,row) in enumerate(zip(cases,answers,rows)):
  assert row[0]==i;data=(folder/f'P{i:05}.ASX').read_bytes();accepted=row[1]==0
  if accepted!=answer['accepted'] or (accepted and data!=answer['data']):
   mismatch=dict(index=i,references=case['references'],actual=dict(report=row,bytes=len(data),data=data[:512].hex()),expected={k:(v[:512].hex() if isinstance(v,bytes) else v) for k,v in answer.items()})
   if answer['accepted']:
    mismatch['expected_bytes']=len(answer['data']);mismatch['first_difference']=next((n for n,(a,b) in enumerate(zip(data,answer['data'])) if a!=b),min(len(data),len(answer['data'])))
   mismatches.append(mismatch)
  records.append(dict(source_sha256=hashlib.sha256(case['raw']).hexdigest(),references=case['references'],accepted=accepted,bytes=len(data),asx_sha256=hashlib.sha256(data).hexdigest(),report=row))
 (OUT/'mismatches.json').write_text(json.dumps(mismatches,indent=2)+'\n');(OUT/'cases.json').write_text(json.dumps(records,indent=2)+'\n')
 assert not mismatches,(len(mismatches),mismatches[:5])
 assert all((folder/name).read_bytes()==compiler.compile_source(good.decode('cp437')) for name in ('GOOD.ASX','NEW.ASX','REPLACE.ASX'))
 assert (folder/'GOOD.ASP').read_bytes()==good and (folder/'OWNER.ASP').read_bytes()==owner and (folder/'BUILD.ASP').read_bytes()==runtime
 assert (folder/'BUILD.ASX').read_bytes()==compiler.compile_source(runtime.decode('cp437'))
 assert (folder/'PRESERVE.ASX').read_bytes()==b'ORIGINAL' and not (folder/'BAD.ASX').exists()
 assert all((folder/name).read_bytes()==b'PREVIOUS VALID OUTPUT' for name in ('RBKEEP.ASX','RBLOST.ASX'))
 assert 'COMPILED IN DOS' in run and '\n0\n1\n2\n' in run
 assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
 report=dict(passed=True,case_count=len(cases),accepted=sum(a['accepted'] for a in answers),rejected=sum(not a['accepted'] for a in answers),binary_sha256=sha(OUT/'ASPCOMP.EXE'),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),host_compiler_sha256=sha(ROOT/'src/aspect/compiler.py'),fixture_sources=fixtures,DOS_summary=run.strip().splitlines()[-1],API_summary=next(s for s in run.splitlines() if s.startswith('API ')),ownership_summary=next(s for s in run.splitlines() if s.startswith('OWNERSHIP ')),CLI_children=11,fault_CLI_children=2,fault_binaries={n:sha(folder/n) for n in ('FAULT.EXE','FAILBACK.EXE')},runtime_child_sha256=sha(folder/'ASPECT.EXE'),runtime_asx_sha256=sha(folder/'BUILD.ASX'),case_manifest_sha256=sha(OUT/'cases.json'),reused_sources={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'standalone/check_aspect_compiler_lexer.py',ROOT/'standalone/compiler_heap_snapshot.c',ROOT/'standalone/compiler_heap_snapshot.h']},original_inputs=[],scope='Complete maintained host grammar under8086 DOS, staged CLI publication including forced rollback/restoration failures and owned fault cleanup, followed by actual execution of DOS-compiled bytecode in maintained ASPECT. Runtime source loading is validated separately; full native language expansion remains unfinished.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if isinstance(v,(str,int,bool))},indent=2))
if __name__=='__main__':main()
