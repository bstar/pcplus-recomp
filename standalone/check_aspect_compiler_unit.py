#!/usr/bin/env python3
"""DOS compiler first pass vs maintained host, plus real far-heap fault checks."""
import hashlib,json,os,re,shutil,struct,subprocess,sys
from pathlib import Path
from build_aspect_compiler_unit import ROOT,OUT,sha,main as build
from check_aspect_compiler_lexer import source_corpus,expected as lexical_expected
sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler
class Inventory(compiler.Compiler):
 def emitted_procedures(self):return list(self.procedures.values())
 def emit_procedures(self,procedures):pass
EDGE={
 'all-layouts':b'integer shared\nlong large\nfloat decimal\nstring name\nproc worker\nintparm a\nlongparm b\nfloatparm c\nstrparm d\ninteger local=7, second=(a+1)\nstring label="Text", other="More"\nexit\nendproc\nproc main\ninteger shared\nexit\nendproc\n',
 'late-declarations':b'proc main\nmessage "before"\ninteger later=3\nmessage "after"\nendproc\n',
 'duplicate-local-parameter':b'proc main\nintparm x\ninteger x\nendproc\n',
 'parameter-outside':b'intparm x\nproc main\nendproc\n',
 'global129':b''.join(f'integer v{i}\n'.encode() for i in range(129))+b'proc main\nendproc\n',
 'local129':b'proc main\n'+b''.join(f'integer v{i}\n'.encode() for i in range(129))+b'endproc\n',
 'parameter-word-layout-wrap':b'proc worker\n'+b''.join(f'strparm p{i}\n'.encode() for i in range(900))+b'endproc\nproc main\nendproc\n',
 'unvalidated-unused-body':b'proc worker\nunknown statement\nendproc\nproc main\nendproc\n',
 'unterminated-initializer-deferred':b'proc main\ninteger x=(1\nendproc\n',
 'maximum-procedure-name':b'proc '+b'A'*248+b'\nendproc\nproc main\nendproc\n',
}
HARNESS=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <dos.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#include "compiler_unit.h"
#include "compiler_unit_dump.h"
#include "compiler_heap_snapshot.h"
static unsigned failed,checks,cases;
static struct _heapinfo before[128],after[128];
extern unsigned __fheapbeg;
static void ck(unsigned ok){++checks;if(!ok){++failed;printf("FAIL check%u\n",checks);}}
static unsigned heap(struct _heapinfo *entries){
 struct _heapinfo h;unsigned count=0;int status;h._pentry=0;
 while((status=_nheapwalk(&h))==_HEAPOK)if(h._useflag==_USEDENTRY){ck(count<128);if(count>=128)return count;entries[count++]=h;}
 ck(status==_HEAPEND||status==_HEAPEMPTY);
 status=_nheapchk();ck(status==_HEAPOK||status==_HEAPEMPTY);
 status=compiler_far_heap_snapshot(entries,128,&count);
 ck(status==0);
 return count;
}
static void same_heap(unsigned baseline){
 unsigned n=heap(after),i;ck(n==baseline);
 for(i=0;i<n&&i<baseline;++i)ck(before[i]._pentry==after[i]._pentry && before[i]._size==after[i]._size);
}
static void ownership(void){
 FILE *f;aspect_compiler_unit unit;unsigned long calls,i;unsigned baseline,head,field,old,result,observed=0;int native_check;unsigned char *foreign;
 unsigned __far *cell;
 f=fopen("OWNER.ASP","wb");ck(f!=0);if(!f)return;
 fputs("integer global\nstring filename\nproc main\ninteger a=1,b=2\nmessage filename\ncall worker\nendproc\nproc worker\nstrparm value\nstring local\nmessage value\nendproc\n",f);ck(fclose(f)==0);
 f=fopen("OWNER.ASP","rb");ck(f!=0);if(!f)return;
 aspect_compiler_unit_init(&unit);ck(aspect_compiler_unit_load(&unit,f)==0);calls=unit.allocation_calls;
 ck(unit.loaded && unit.live_allocations>0);ck(aspect_compiler_unit_load(&unit,f)==ASPECT_COMPILE_STATE);
 aspect_compiler_unit_dispose(&unit);ck(!unit.live_allocations && !unit.allocations);
 foreign=malloc(37);ck(foreign!=0);if(!foreign){fclose(f);return;}memset(foreign,0x5a,37);
 baseline=heap(before);native_check=_fheapchk();
 head=__fheapbeg;ck(head!=0);
 if(head){
  for(field=0;field<4;++field){
   unsigned offset=field==0?16:field==1?4:field==2?22:(unsigned)((*(unsigned __far *)MK_FP(head,0)?(unsigned long)*(unsigned __far *)MK_FP(head,0):65536UL)-4);
   cell=(unsigned __far *)MK_FP(head,offset);old=*cell;
   *cell=field==0?1:field==1?head:field==2?4:0;
   observed=0;result=compiler_far_heap_snapshot(after,128,&observed);*cell=old;ck(result!=0);
  }
  observed=0;ck(compiler_far_heap_snapshot(after,0,&observed)==2);
  __fheapbeg=65535U;observed=0;result=compiler_far_heap_snapshot(after,128,&observed);__fheapbeg=head;ck(result!=0);
 }
 same_heap(baseline);
 for(i=0;i<calls;++i){
  rewind(f);aspect_compiler_unit_init(&unit);unit.fail_after=i;
  ck(aspect_compiler_unit_load(&unit,f)==ASPECT_COMPILE_HEAP);
  ck(unit.allocation_calls==i+1 && !unit.allocations && !unit.live_allocations && !unit.loaded);
  ck(!unit.globals && !unit.procedures);ck(ftell(f)>=0 && !ferror(f));
  aspect_compiler_unit_dispose(&unit);aspect_compiler_unit_dispose(&unit);same_heap(baseline);
  ck(foreign[0]==0x5a && foreign[36]==0x5a);
 }
 for(i=0;i<200;++i){
  rewind(f);aspect_compiler_unit_init(&unit);ck(aspect_compiler_unit_load(&unit,f)==0);
  ck(unit.allocation_calls==calls);aspect_compiler_unit_dispose(&unit);
 }
 same_heap(baseline);free(foreign);ck(fclose(f)==0);
 printf("CRT_HEAP native_check%d independent_used_entries%u corruption_cases6\n",native_check,baseline);
 printf("OWNERSHIP %lu injected failures and200 successful load/dispose cycles\n",calls);
}
static void cli(const char *input,const char *name,unsigned expected){
 int fd,save,result;fflush(stdout);
 fd=open(name,O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);ck(fd>=0);save=dup(1);ck(save>=0);ck(dup2(fd,1)==0);close(fd);
 if(input)result=spawnl(P_WAIT,"ASPINV.EXE","ASPINV",input,(char *)0);
 else result=spawnl(P_WAIT,"ASPINV.EXE","ASPINV",(char *)0);
 fflush(stdout);ck(dup2(save,1)==0);close(save);ck(result==expected);
}
int main(void){
 FILE *list,*output,*input;char path[13];unsigned expected;int status;
 list=fopen("CASES.LST","rt");output=fopen("UNITS.DAT","wb");if(!list||!output)return 99;
 while(fscanf(list,"%12s %u",path,&expected)==2){
  input=fopen(path,"rb");if(!input)return 98;
  status=aspect_compiler_unit_dump(input,output);ck(status==expected);ck(fclose(input)==0);++cases;
 }
 ck(fclose(list)==0);ck(fclose(output)==0);ownership();
'''
def locations(raw):
 result={};offset=0
 for number,fragment in enumerate(raw.decode('cp437').splitlines(keepends=True),1):
  text=fragment[:-2] if fragment.endswith('\r\n') else fragment[:-1] if fragment[-1:] in '\r\n\v\f\x1c\x1d\x1e' else fragment
  result[number]=(offset,text);offset+=len(fragment.encode('cp437'))
 return result

def reference(raw):
 instance=Inventory();mapping=locations(raw)
 try:instance.compile(raw.decode('cp437'))
 except compiler.CompileError as error:
  text=str(error);number=int(re.search(r'line (\d+):',text)[1]);status=2;lex=0;offset=mapping.get(number,(0,''))[0]
  if 'unrecognized text' in text or 'physical source lines over' in text:
   status=1;lex=2 if 'physical source lines over' in text else 3
   wire,_,_,_=lexical_expected(raw);n,offset,column=struct.unpack('<IIH',wire[-10:]);assert n==number
  return dict(status=status,lexical_status=lex,error_line=number,error_offset=offset)
 declarations={None:[]};current=None
 for number,(offset,text) in mapping.items():
  tokens=compiler.tokenize(text,number)
  if not tokens:continue
  if tokens[0]=='proc':current=tokens[1];declarations[current]=[]
  elif tokens[0]=='endproc':current=None
  elif tokens[0] in compiler.TYPES or tokens[0] in compiler.PARMS:declarations[current].append(dict(line=number,offset=offset))
 def symbols(items):return [dict(name=name,kind=s.kind,space={'global':0,'local':1,'param':2}[s.space],index=s.index&65535) for name,s in items.items()]
 procs=[]
 for p in instance.procedures.values():
  # Procedure location is independently found from its declaration line.
  number=next(n for n,(off,text) in mapping.items() if compiler.tokenize(text,n)==['proc',p.name])
  procs.append(dict(name=p.name,size=p.size,parameter_bytes=sum(compiler.SIZES[s.kind] for s in p.params),line=number,offset=mapping[number][0],symbols=symbols(p.symbols),declarations=declarations[p.name],initializers=[dict(line=n,offset=mapping[n][0],tokens=t,chained=bool(ch)) for n,t,ch in p.initializers],body=[dict(line=n,offset=mapping[n][0]) for n,t in p.lines]))
 return dict(status=0,lexical_status=0,error_line=0,error_offset=0,counts=instance.counts,globals=symbols(instance.globals),declarations=declarations[None],procedures=procs)

class Stream:
 def __init__(self,data):self.data=data;self.pos=0
 def take(self,n):
  assert self.pos+n<=len(self.data);v=self.data[self.pos:self.pos+n];self.pos+=n;return v
 def byte(self):return self.take(1)[0]
 def word(self):return int.from_bytes(self.take(2),'little')
 def dword(self):return int.from_bytes(self.take(4),'little')
 def name(self):return self.take(self.word()).decode('cp437')
 def symbols(self):
  result=[]
  while self.byte():
   kind,space,index=self.byte(),self.byte(),self.word();result.append(dict(name=self.name(),kind=kind,space=space,index=index))
  return result
 def ranges(self):
  result=[]
  while self.byte():result.append(dict(line=self.dword(),offset=self.dword()))
  return result
 def unit(self,raw):
  assert self.take(4)==b'AUN1';d=dict(status=self.byte(),lexical_status=self.byte(),error_line=self.dword(),error_offset=self.dword())
  if d['status']:return d
  d.update(counts=[self.word() for _ in range(4)],globals=self.symbols(),declarations=self.ranges(),procedures=[]);mapping=locations(raw)
  while self.byte():
   p=dict(name=self.name(),size=self.word(),parameter_bytes=self.dword(),line=self.dword(),offset=self.dword(),symbols=self.symbols(),declarations=self.ranges(),initializers=[],body=[])
   while self.byte():
    number,offset,first,last,chained=self.dword(),self.dword(),self.word(),self.word(),self.byte();name=self.name()
    tokens=compiler.tokenize(mapping[number][1],number)
    assert 0<=first<=last<=len(tokens)
    p['initializers'].append(dict(line=number,offset=offset,tokens=[name,'=']+tokens[first:last],chained=bool(chained)))
   while self.byte():p['body'].append(dict(line=self.dword(),offset=self.dword()))
   d['procedures'].append(p)
  return d

def main():
 build();cases,fixtures=source_corpus();known={hashlib.sha256(c['raw']).hexdigest() for c in cases}
 for name,raw in EDGE.items():
  if hashlib.sha256(raw).hexdigest() not in known:cases.append(dict(raw=raw,references=['unit-edge:'+name]))
 folder=OUT/'tests';folder.mkdir(exist_ok=True);shutil.copyfile(OUT/'ASPINV.EXE',folder/'ASPINV.EXE')
 program=HARNESS;listing='';expectations=[];selected={}
 for index,case in enumerate(cases):
  name=f'U{index:05}.ASP';(folder/name).write_bytes(case['raw']);answer=reference(case['raw']);expectations.append(answer)
  status=int(bool(answer['status']));listing+=f'{name} {status}\n'
  if status not in selected:selected[status]=(index,name)
 (folder/'CASES.LST').write_text(listing)
 for status,(index,name) in selected.items():program+=f' cli("{name}","CLI{status}.AUN",{status});\n'
 program+=' cli("ABSENT.ASP","MISSING.AUN",1);cli(0,"USAGE.AUN",64);\n'
 program+=' printf("UNIT %u cases %u checks %u failures\\n",cases,checks,failed);return failed?1:0;}\n'
 (folder/'harness.c').write_text(program)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm=UNITTEST.map','-fe=UNITTEST.EXE',str(folder/'harness.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/name) for name in ['compiler_lexer.c','compiler_unit.c','compiler_unit_dump.c']]],cwd=folder,check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k4096','-i='+str(ROOT/'standalone'),'-fm=CRTHEAP.map','-fe=CRTHEAP.EXE',str(ROOT/'standalone/compiler_crt_heap_probe.c'),str(ROOT/'standalone/compiler_heap_snapshot.c')],cwd=folder,check=True)
 for name in ['PASS.TXT','FAIL.TXT','RUN.TXT','UNITS.DAT']:(folder/name).unlink(missing_ok=True)
 config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{folder}"\nc:\nCRTHEAP >CRT.TXT\nif errorlevel 1 goto failed\nUNITTEST >RUN.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=180)
 run=(folder/'RUN.TXT').read_text();crt=(folder/'CRT.TXT').read_text().strip();assert 'independent_during0 independent_after0' in crt;print(crt);print(run)
 stream=Stream((folder/'UNITS.DAT').read_bytes());records=[]
 for index,(case,answer) in enumerate(zip(cases,expectations)):
  start=stream.pos;actual=stream.unit(case['raw'])
  if actual!=answer:
   mismatch=dict(index=index,references=case['references'],actual=actual,expected=answer)
   (OUT/'mismatch.json').write_text(json.dumps(mismatch,indent=2)+'\n');raise AssertionError((index,case['references']))
  records.append(dict(source_sha256=hashlib.sha256(case['raw']).hexdigest(),references=case['references'],status=actual['status'],output_sha256=hashlib.sha256(stream.data[start:stream.pos]).hexdigest()))
 assert stream.pos==len(stream.data)
 for status,(index,name) in selected.items():
  other=Stream((folder/f'CLI{status}.AUN').read_bytes());assert other.unit(cases[index]['raw'])==expectations[index];assert other.pos==len(other.data)
 assert (folder/'MISSING.AUN').read_bytes()==(folder/'USAGE.AUN').read_bytes()==b''
 assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),run
 (OUT/'cases.json').write_text(json.dumps(records,indent=2)+'\n')
 report=dict(passed=True,binary_sha256=sha(OUT/'ASPINV.EXE'),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),host_compiler_sha256=sha(ROOT/'src/aspect/compiler.py'),reused_corpus_checker_sha256=sha(ROOT/'standalone/check_aspect_compiler_lexer.py'),fixture_sources=fixtures,case_count=len(cases),accepted_first_pass=sum(not r['status'] for r in records),rejected_first_pass=sum(bool(r['status']) for r in records),DOS_summary=run.strip().splitlines()[-1],ownership_summary=next(line for line in run.splitlines() if line.startswith('OWNERSHIP')),heap_observer_summary=next(line for line in run.splitlines() if line.startswith('CRT_HEAP')),isolated_CRT_probe=dict(summary=crt,binary_sha256=sha(folder/'CRTHEAP.EXE'),source_sha256=sha(ROOT/'standalone/compiler_crt_heap_probe.c')),heap_observer_sources={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'standalone/compiler_heap_snapshot.c',ROOT/'standalone/compiler_heap_snapshot.h']},units_sha256=sha(folder/'UNITS.DAT'),case_manifest_sha256=sha(OUT/'cases.json'),original_inputs=[],scope='Actual DOS8086 large-model first-pass symbols, procedure/parameter/local layout and source ranges against maintained host pass with emission disabled. Native near-heap checker and independent explicit-segment far-heap observer restore used entry identity/size after every allocation failure and200 successful disposal cycles; borrowed FILE and foreign heap block retained. Expression/body validation, dead procedure elimination, ASX output and runtime compilation remain pending.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if isinstance(v,(str,int,bool))},indent=2))
if __name__=='__main__':main()
