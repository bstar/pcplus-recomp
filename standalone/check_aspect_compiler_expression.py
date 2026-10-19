#!/usr/bin/env python3
"""Compare real8086 DOS expression fragments with the maintained host compiler."""
import decimal,hashlib,json,math,os,random,shutil,struct,subprocess,sys
from pathlib import Path
from build_aspect_compiler_expression import ROOT,OUT,sha,main as build
from check_aspect_compiler_unit import Inventory
from check_aspect_compiler_lexer import source_corpus
sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler

SCOPE=('integer i,j,k\nlong l,m\nfloat f,g\nstring s,t\nproc main\n'
       'intparm p\nlongparm q\nfloatparm r\nstrparm z\n'
       'integer x,y\nlong u\nfloat v\nstring a,b\n')
MODES={'EXPR':0,'ATOM':1,'WORD':2,'ASSIGN':3,'CHAIN':4}

def reference(case):
 c=Inventory();c.compile(case['raw'].decode('cp437'));c.proc=c.procedures[case['proc']]
 c.line=case['line'];c.output=bytearray(case['prefix'])
 tokens=compiler.tokenize(case['raw'].decode('cp437').splitlines()[c.line-1],c.line)[case['first']:case['last']]
 try:
  if case['mode'] in ('ASSIGN','CHAIN'):
   c.assign(tokens,chained=case['mode']=='CHAIN');kind=c.lvalue(('symbol',tokens[0]))[0]
  else:
   node=c.tree(tokens);kind=c.kind(node)
   if case['mode']=='EXPR':value=c.expression(node,case['slot'])
   elif case['mode']=='ATOM':value=c.atomic(node)
   else:value=c.word_argument(node);kind=0
   c.operand(value,compact=case['compact'])
  return dict(accepted=True,kind=kind,data=bytes(c.output[case['prefix']:]))
 except (compiler.CompileError,TypeError,OverflowError) as error:
  return dict(accepted=False,error_type=type(error).__name__,error=str(error))

def cases():
 result=[]
 def add(text,mode='EXPR',prefix=0,slot=0,compact=False,label=None):
  raw=(SCOPE+text+'\nendproc\n').encode('cp437')
  if len(text.encode('cp437'))>253:return
  result.append(dict(raw=raw,line=len(SCOPE.splitlines())+1,proc='main',first=0,last=None,
                     mode=mode,prefix=prefix,slot=slot,compact=compact,label=label or text))
 atoms=['0','1','255','256','32767','32768','65535','65536','2147483647','4294967295',
        '4294967296','18446744073709551616','0xffffffff','0x100000000','1L','0x8000L',
        '-32768','-32768L','-32769','-0','-0.0','0.0','1.5','1e309','1e-324',
        '2.2250738585072014e-308','4.9406564584124654e-324',
        'i','l','f','s','x','u','v','a','p','q','r','z','s0','s9','unknown',
        *compiler.TYPED_BUILTINS,'""','"Hello^MWorld"','"'+bytes([219]).decode('cp437')*80+'"','"'+'x'*81+'"','"a\0b"']
 for text in atoms:
  for mode in ('EXPR','ATOM','WORD'):add(text,mode,compact=mode!='EXPR')
 for left in ('i','l','f','s','x','p','q','r','z'):
  for right in ('j','m','g','t','y','1','32768','1.5','"x"'):
   for op in compiler.OPS:add(left+op+right)
 for text in ('i+j*k','(i+j)*k','i-j-k','i/(j/k)','-(-1)','-(i+j)',
              '++i','--x','++q','--r','++s','++1','++(i+j)','++success',
              'i=j=k=1','i=l=f','s=t="x"','i=1+(j=2)','1=2',
              'i||j&&k','(i||j)&&(k||x)','i&&(j||(k&&x))',
              '1||0','0&&1','4294967296L||i','0.0||i','-0.0&&i','s||i',
              '','(','i+','i j','i++','+1','i+=1',')','(i','i)'):
  add(text)
 for dest in ('i','l','f','s','x','u','v','a','p','q','r','z','s0','s9','success','$null','unknown','1'):
  for op in ('=','+=','-=','*=','/=','%='):
   for rhs in ('j+1','1.5','"abc"'):
    for mode in ('ASSIGN','CHAIN'):add(dest+op+rhs,mode)
 for prefix in (1,2,65535,65536,70000):
  for text in ('"Ansi ▓▒░"','i||(j&&x)','i&&(j||k)','(i||j)&&(k||x)'):
   add(text,prefix=prefix)
 for slot in (254,255,256):
  for text in ('i','i+j','(i+j)*(k+x)','i||(j&&x)'):add(text,slot=slot)
 for text in ('('*120+'i'+')'*120,'- '*120+'1','+'.join(['i']*127),
              '||'.join(['i']*84),'i='*125+'1'):
  add(text)
 rng=random.Random(438)
 def expression(depth):
  if not depth:return rng.choice(('i','j','l','f','0','1','32768','1.5'))
  return '('+expression(depth-1)+rng.choice(tuple(compiler.PRIORITY))+expression(depth-1)+')'
 for _ in range(200):add(expression(rng.randrange(1,5)),label='seeded mixed expression')
 # Decimal conversion must match Python's IEEE754 rounding, including long
 # mantissas, subnormals and overflow, with the emulated FPU disabled.
 add('100591108740498876e-335',label='pinned CRT subnormal rounding regression')
 for _ in range(1000):
  digits=rng.randrange(1,220)
  mantissa=''.join(str(rng.randrange(10)) for _ in range(digits))
  add(mantissa+'e'+str(rng.randrange(-325-digits,310-digits)),label='decimal rounding')
 # Exact halfway values on both even/odd mantissas and immediate decimal
 # neighbors. Underflow halfways needing more than253 bytes are out of grammar.
 with decimal.localcontext() as context:
  context.prec=1200
  for binary in (-500,-100,-10,0,10,53,100,500,1023):
   for offset in (0,1,2,3):
    value=math.ldexp(1.0,binary)
    for _ in range(offset):value=math.nextafter(value,math.inf)
    middle=(decimal.Decimal(value)+decimal.Decimal(math.nextafter(value,math.inf)))/2
    for adjustment in (-1,0,1):
     add(str(middle+decimal.Decimal(adjustment).scaleb(middle.adjusted()-230)),label='IEEE nearest even decimal boundary')
 for text in ('0.0e999999999999999999999999','1e999999999999999999999999',
              '1e-999999999999999999999999','000000.00000001',
              '1.7976931348623157e308','1.7976931348623158e308',
              '1.7976931348623159e308','2.4703282292062327e-324','2.4703282292062328e-324',
              '2.2250738585072011e-308','2.2250738585072012e-308','-32768.0'):
  add(text,'WORD' if text=='-32768.0' else 'EXPR',label='decimal boundary')
 corpus,fixtures=source_corpus()
 seen=set()
 for source in corpus:
  raw=source['raw']
  try:c=Inventory();c.compile(raw.decode('cp437'))
  except compiler.CompileError:continue
  proc=None
  for number,line in enumerate(raw.decode('cp437').splitlines(),1):
   t=compiler.tokenize(line,number)
   if not t:continue
   if t[0]=='proc':proc=t[1]
   elif t[0]=='endproc':proc=None
   elif proc and len(t)>2 and t[1] in ('=','+=','-=','*=','/=','%='):
    key=(tuple(t),number%12,tuple((k,s.kind,s.space,s.index) for k,s in c.procedures[proc].symbols.items()),tuple((k,s.kind,s.index) for k,s in c.globals.items()))
    if key in seen:continue
    seen.add(key)
    result.append(dict(raw=raw,line=number,proc=proc,first=0,last=None,mode='ASSIGN',prefix=0,slot=0,compact=False,label=source['references']))
 return result,fixtures

HARNESS=r'''
#include <stdio.h>
#include <string.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <malloc.h>
#include "compiler_expression_dump.h"
#include "compiler_output.h"
#include "compiler_heap_snapshot.h"
static unsigned checks,failures;
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL API check%u\n",checks);}}
static void output_api(void){
 FILE *f;aspect_compiler_output writer;unsigned long i;unsigned char bytes[8];
 ck(aspect_compiler_output_init(&writer,0)==ASPECT_OUTPUT_STATE);
 f=fopen("OUTPUT.DAT","w+b");ck(f!=0);if(!f)return;
 ck(aspect_compiler_output_init(&writer,f)==0);
 for(i=0;i<70000UL;++i)aspect_compiler_emit_byte(&writer,0xa5);
 aspect_compiler_emit_dword(&writer,0);aspect_compiler_emit_word(&writer,0x1234);
 ck(writer.position==70006UL);aspect_compiler_patch_dword(&writer,70000UL,0x12345678UL);
 ck(!writer.status && writer.position==70006UL && ftell(f)==70006L);
 aspect_compiler_emit_byte(&writer,0x99);ck(aspect_compiler_output_flush(&writer)==0);
 ck(fseek(f,70000L,SEEK_SET)==0 && fread(bytes,1,7,f)==7);
 ck(!memcmp(bytes,"\x78\x56\x34\x12\x34\x12\x99",7));
 ck(fseek(f,0L,SEEK_END)==0);aspect_compiler_output_init(&writer,f);
 aspect_compiler_patch_dword(&writer,writer.position-3,1);ck(writer.status==ASPECT_OUTPUT_RANGE);
 aspect_compiler_emit_byte(&writer,0);ck(writer.position==70007UL && ftell(f)==70007L);
 aspect_compiler_output_init(&writer,f);aspect_compiler_patch_dword(&writer,0,0x80000000UL);ck(writer.status==ASPECT_OUTPUT_RANGE);
 aspect_compiler_output_init(&writer,f);writer.position=ASPECT_OUTPUT_MAX;
 aspect_compiler_emit_byte(&writer,0);ck(writer.status==ASPECT_OUTPUT_RANGE && ftell(f)==70007L);
 ck(fclose(f)==0);f=fopen("OUTPUT.DAT","rb");ck(f!=0);if(!f)return;
 aspect_compiler_output_init(&writer,f);aspect_compiler_emit_byte(&writer,0);aspect_compiler_output_flush(&writer);
 ck(writer.status==ASPECT_OUTPUT_IO);ck(fclose(f)==0);
 f=fopen("SHORT.DAT","w+b");ck(f!=0);if(!f)return;
 aspect_compiler_output_init(&writer,f);aspect_compiler_patch_dword(&writer,0,0);ck(writer.status==ASPECT_OUTPUT_RANGE && ftell(f)==0);
 ck(fclose(f)==0);
}
static void cli(const char *path,const char *line,const char *mode,const char *name,unsigned expected){
 int fd,save,result;fflush(stdout);
 fd=open(name,O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);ck(fd>=0);if(fd<0)return;
 save=dup(1);ck(save>=0);if(save<0){close(fd);return;}ck(dup2(fd,1)==0);close(fd);
 result=spawnl(P_WAIT,"ASPEXP.EXE","ASPEXP",path,line,mode,(char *)0);
 fflush(stdout);ck(dup2(save,1)==0);close(save);ck(result==expected);
}
static void ownership(void){
 struct _heapinfo before[128],after[128];FILE *input,*output;unsigned char *foreign;
 unsigned count=0,n=0,i,j;input=fopen("CLI.ASP","rb");output=tmpfile();ck(input!=0 && output!=0);
 if(!input||!output){if(input)fclose(input);if(output)fclose(output);return;}
 ck(aspect_compiler_expression_dump(input,output,14UL,0,65535U,0,0UL,0,0)==0);
 foreign=malloc(37);ck(foreign!=0);if(!foreign){fclose(input);fclose(output);return;}memset(foreign,0x5a,37);
 ck(compiler_far_heap_snapshot(before,128,&count)==0);
 for(i=0;i<100;++i){
  rewind(input);rewind(output);
  ck(aspect_compiler_expression_dump(input,output,14UL,0,65535U,i%2?2:0,0UL,0,0)==(i%2?1:0));
  ck(ftell(input)>=0 && !ferror(input));ck(ftell(output)>=0 && !ferror(output));
  n=0;ck(compiler_far_heap_snapshot(after,128,&n)==0);ck(n==count);
  for(j=0;j<n && j<count;++j)ck(before[j]._pentry==after[j]._pentry && before[j]._size==after[j]._size);
  ck(foreign[0]==0x5a && foreign[36]==0x5a);
 }
 free(foreign);ck(fclose(input)==0);ck(fclose(output)==0);
}
int main(void){
 FILE *list,*out,*input;char path[13];unsigned mode,slot,compact,first,last,expected,failed=0,count=0;
 unsigned long line,prefix;int status;
 list=fopen("CASES.LST","rt");out=fopen("EXPRS.DAT","wb");if(!list||!out)return 99;
 while(fscanf(list,"%12s %lu %u %u %u %lu %u %u %u",path,&line,&first,&last,&mode,&prefix,&slot,&compact,&expected)==9){
  input=fopen(path,"rb");if(!input)return 98;
  status=aspect_compiler_expression_dump(input,out,line,first,last,mode,prefix,slot,compact);
  if(status!=expected){++failed;printf("FAIL %u %s status%d expected%u\n",count,path,status,expected);}
  if(fclose(input))return 97;++count;
 }
 if(fclose(list)||fclose(out))return 96;
 output_api();ownership();
 cli("CLI.ASP","14","EXPR","CLI.DAT",0);
 cli("CLI.ASP","14","WORD","CLIWORD.DAT",1);
 cli("CLI.ASP","-1","EXPR","NEGATIVE.DAT",64);
 cli("CLI.ASP","4294967296","EXPR","OVERFLOW.DAT",64);
 cli("ABSENT.ASP","1","EXPR","MISSING.DAT",1);
 cli("CLI.ASP","14","INVALID","USAGE.DAT",64);
 printf("API %u checks %u failures\n",checks,failures);
 printf("EXPRESSION %u cases %u failures\n",count,failed);return failed||failures?1:0;
}
'''

def main():
 build();entries,fixtures=cases();answers=[reference(c) for c in entries]
 folder=OUT/'tests';folder.mkdir(exist_ok=True);shutil.copyfile(OUT/'ASPEXP.EXE',folder/'ASPEXP.EXE')
 (folder/'CLI.ASP').write_bytes((SCOPE+'i+1\nendproc\n').encode('cp437'))
 listing=[]
 for index,(case,answer) in enumerate(zip(entries,answers)):
  name=f'E{index:05}.ASP';(folder/name).write_bytes(case['raw'])
  listing.append(f"{name} {case['line']} {case['first']} {65535 if case['last'] is None else case['last']} {MODES[case['mode']]} {case['prefix']} {case['slot']} {int(case['compact'])} {int(not answer['accepted'])}\n")
 (folder/'CASES.LST').write_text(''.join(listing));(folder/'harness.c').write_text(HARNESS)
 sources=['compiler_lexer.c','compiler_unit.c','compiler_decimal.c','compiler_expr.c','compiler_output.c','compiler_emit.c','compiler_expression_dump.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-fpc','-ecc','-s','-w4','-we','-k32768','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm=EXPRTEST.map','-fe=EXPRTEST.EXE',str(folder/'harness.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*[str(ROOT/'src/aspect'/p) for p in sources]],cwd=folder,check=True)
 for name in ('PASS.TXT','FAIL.TXT','RUN.TXT','EXPRS.DAT'):(folder/name).unlink(missing_ok=True)
 config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{folder}"\nc:\nEXPRTEST >RUN.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=240)
 data=(folder/'EXPRS.DAT').read_bytes();position=0;records=[];mismatches=[]
 for index,(case,answer) in enumerate(zip(entries,answers)):
  magic,status,io,cursor,nodes,kind,size=struct.unpack_from('<4sBBHHHI',data,position);position+=16
  fragment=data[position:position+size];position+=size
  assert magic==b'AEX1' and len(fragment)==size
  accepted=not(status or io)
  if accepted!=answer['accepted'] or (accepted and (fragment!=answer['data'] or kind!=answer['kind'])):
   mismatches.append(dict(index=index,label=case['label'],mode=case['mode'],prefix=case['prefix'],slot=case['slot'],source=case['raw'].decode('cp437'),actual=dict(status=status,io=io,kind=kind,data=fragment.hex()),expected={k:v.hex() if isinstance(v,bytes) else v for k,v in answer.items()}))
  records.append(dict(source_sha256=hashlib.sha256(case['raw']).hexdigest(),line=case['line'],mode=case['mode'],prefix=case['prefix'],slot=case['slot'],accepted=accepted,fragment_sha256=hashlib.sha256(fragment).hexdigest()))
 assert position==len(data)
 (OUT/'mismatches.json').write_text(json.dumps(mismatches,indent=2)+'\n')
 run=(folder/'RUN.TXT').read_text();print(run)
 assert not mismatches,(len(mismatches),mismatches[:3])
 cli_case=dict(raw=(SCOPE+'i+1\nendproc\n').encode('cp437'),line=14,proc='main',first=0,last=None,mode='EXPR',prefix=0,slot=0,compact=False)
 cli_bytes=(folder/'CLI.DAT').read_bytes();assert cli_bytes[:4]==b'AEX1' and cli_bytes[4:6]==b'\0\0' and cli_bytes[16:]==reference(cli_case)['data']
 assert (folder/'CLIWORD.DAT').read_bytes()[4]!=0
 assert all((folder/name).read_bytes()==b'' for name in ('NEGATIVE.DAT','OVERFLOW.DAT','MISSING.DAT','USAGE.DAT'))
 assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
 (OUT/'cases.json').write_text(json.dumps(records,indent=2)+'\n')
 report=dict(passed=True,case_count=len(entries),accepted=sum(a['accepted'] for a in answers),rejected=sum(not a['accepted'] for a in answers),binary_sha256=sha(OUT/'ASPEXP.EXE'),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),host_compiler_sha256=sha(ROOT/'src/aspect/compiler.py'),fixture_sources=fixtures,fragments_sha256=sha(folder/'EXPRS.DAT'),case_manifest_sha256=sha(OUT/'cases.json'),DOS_summary=run.strip(),host_exception_edges=[dict(index=i,error=a['error']) for i,a in enumerate(answers) if a.get('error_type') in ('TypeError','OverflowError')],original_inputs=[],scope='Actual8086 DOS software-float expression/operand and assignment fragment equality. Statement grammar, complete ASX emission and runtime compiler integration remain unfinished.')
 report.update(API_summary=next(line for line in run.splitlines() if line.startswith('API ')),ownership_cycles=100,CLI_children=6,
  reused_sources={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'standalone/check_aspect_compiler_unit.py',ROOT/'standalone/check_aspect_compiler_lexer.py',ROOT/'standalone/compiler_heap_snapshot.c',ROOT/'standalone/compiler_heap_snapshot.h']})
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if isinstance(v,(str,int,bool))},indent=2))
if __name__=='__main__':main()
