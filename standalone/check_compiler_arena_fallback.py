#!/usr/bin/env python3
"""DOS inventory fallback under independently limited allocations and logical faults."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUTS=['src/aspect/compiler_unit.c','src/aspect/compiler_unit.h','src/aspect/compiler_lexer.c','src/aspect/compiler_lexer.h',
 'src/aspect/compiler_unit_dump.c','src/aspect/compiler_unit_dump.h','standalone/compiler_heap_snapshot.c','standalone/compiler_heap_snapshot.h']
FALLBACK='''  while(!block && capacity>rounded){
   capacity/=2U;if(capacity<rounded)capacity=rounded;
   block=malloc(offsetof(struct aspect_compiler_allocation,payload)+capacity);
  }
'''
DRIVER=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "compiler_unit.h"
#include "compiler_unit_dump.h"
#include "compiler_heap_snapshot.h"
static unsigned limit,attempts,denied,live,checks,failures;
static void *pointers[256];
static struct _heapinfo before[128],after[128];
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL check%u\n",checks);}}
void *__watcall arena_malloc(size_t bytes)
{
 void *p;unsigned i;++attempts;
 if(limit&&bytes>limit){++denied;return 0;}
 p=malloc(bytes);if(!p)return 0;
 for(i=0;i<256;++i)if(!pointers[i]){pointers[i]=p;++live;return p;}
 free(p);++failures;return 0;
}
void __watcall arena_free(void *p)
{
 unsigned i;
 for(i=0;i<256;++i)if(pointers[i]==p){pointers[i]=0;--live;free(p);return;}
 ++failures;
}
static void owned(unsigned count)
{
 unsigned n=0,i;ck(!compiler_far_heap_snapshot(after,128,&n));ck(n==count);
 for(i=0;i<n&&i<count;++i)ck(after[i]._pentry==before[i]._pentry&&after[i]._size==before[i]._size);
}
static int same(const char *left,const char *right)
{
 FILE *a=fopen(left,"rb"),*b=fopen(right,"rb");int x,y,ok=1;
 if(!a||!b)return 0;
 do{x=fgetc(a);y=fgetc(b);if(x!=y){ok=0;break;}}while(x!=EOF);
 fclose(a);fclose(b);return ok;
}
int main(int argc,char **argv)
{
 FILE *in,*out;aspect_compiler_unit unit;unsigned count=0,old=argc>1&&argv[1][0]=='O';
 unsigned long logical,i;unsigned char *foreign;unsigned cycle,status;
 setvbuf(stdout,0,_IONBF,0);
 in=fopen("OWNER.ASP","rb");if(!in)return 98;
 out=fopen("NORMAL.BIN","wb");if(!out)return 97;
 limit=0;ck(!aspect_compiler_unit_dump(in,out));ck(!fclose(out));ck(!live);
 rewind(in);aspect_compiler_unit_init(&unit);ck(!aspect_compiler_unit_load(&unit,in));logical=unit.allocation_calls;
 aspect_compiler_unit_dispose(&unit);ck(logical>10&&!live);
 /* Warm the comparison fixture's extra stdio slots before measuring unit
  * ownership. Watcom retains its stream-table expansion after fclose. */
 ck(same("NORMAL.BIN","NORMAL.BIN"));
 foreign=malloc(37);if(!foreign)return 96;memset(foreign,0x5a,37);
 ck(!compiler_far_heap_snapshot(before,128,&count));
 limit=256;attempts=denied=0;
 rewind(in);aspect_compiler_unit_init(&unit);status=aspect_compiler_unit_load(&unit,in);
 if(old){ck(status==ASPECT_COMPILE_HEAP);ck(denied==1);}
 else{ck(!status);ck(unit.allocation_calls==logical);ck(denied>0&&attempts>denied);}
 aspect_compiler_unit_dispose(&unit);ck(!live);owned(count);
 if(!old){
  rewind(in);out=fopen("LIMIT.BIN","wb");ck(out!=0);
  ck(!aspect_compiler_unit_dump(in,out));ck(!fclose(out));ck(same("NORMAL.BIN","LIMIT.BIN"));ck(!live);
  /* A failed logical allocation must not become a physical fallback retry. */
  for(i=0;i<logical;++i){
   rewind(in);aspect_compiler_unit_init(&unit);unit.fail_after=i;
   ck(aspect_compiler_unit_load(&unit,in)==ASPECT_COMPILE_HEAP);
   ck(unit.allocation_calls==i+1&&!unit.allocations&&!unit.live_allocations);
   aspect_compiler_unit_dispose(&unit);ck(!live);owned(count);
  }
  for(cycle=0;cycle<100;++cycle){
   rewind(in);aspect_compiler_unit_init(&unit);ck(!aspect_compiler_unit_load(&unit,in));
   ck(unit.allocation_calls==logical);aspect_compiler_unit_dispose(&unit);ck(!live);
  }
  owned(count);
 }
 /* Neither a preferred arena nor the actual object fits. No leak or unbounded
  * retry is permitted; the caller's stream/foreign allocation remain live. */
 limit=1;attempts=denied=0;rewind(in);aspect_compiler_unit_init(&unit);
 ck(aspect_compiler_unit_load(&unit,in)==ASPECT_COMPILE_HEAP);
 ck((old?attempts==1U:attempts>=2U&&attempts<=10U)&&denied==attempts&&unit.allocation_calls==1&&!live);
 aspect_compiler_unit_dispose(&unit);owned(count);
 for(cycle=0;cycle<37;++cycle)ck(foreign[cycle]==0x5a);
 free(foreign);ck(!fclose(in));
 printf("ARENA_%s logical%lu checks%u failures%u\n",old?"CONTROL":"FALLBACK",logical,checks,failures);
 return failures?1:0;
}
'''
SOURCE='''integer shared
long amount
string name
proc worker
intparm value
integer a=1,b=2
message name
endproc
proc main
integer local=3
message "test"
call worker with local
endproc
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 source=ROOT/'src/aspect/compiler_unit.c';text=source.read_text();assert text.count(FALLBACK)==1
 control=out/'unit-control.c';control.write_text(text.replace(FALLBACK,''))
 driver=out/'driver.c';driver.write_text(DRIVER);(out/'OWNER.ASP').write_text(SOURCE)
 for name,path in [('FALLBACK',source),('CONTROL',control)]:
  obj=out/(name+'.o')
  subprocess.run(['wcc','-q','-bt=dos','-0','-ml','-ecc','-w4','-we','-dmalloc=arena_malloc','-dfree=arena_free',
   '-i='+str(ROOT/'src/aspect'),'-fo='+str(obj),str(path)],check=True)
  subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),
   '-fe='+name+'.EXE',str(driver),str(obj),str(ROOT/'src/aspect/compiler_lexer.c'),str(ROOT/'src/aspect/compiler_unit_dump.c'),
   str(ROOT/'standalone/compiler_heap_snapshot.c')],cwd=out,check=True)
 cfg='''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "'''+str(out)+'''"
c:
CONTROL OLD > CONTROL.TXT
if errorlevel 1 goto failed
FALLBACK > FALLBACK.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (out/'dosbox.conf').write_text(cfg)
 with(out/'dosbox.log').open('w')as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 summaries={name:(out/(name+'.TXT')).read_text().strip()for name in ['CONTROL','FALLBACK']}
 assert(out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists(),summaries
 assert all('failures0'in value for value in summaries.values()),summaries
 assert(out/'NORMAL.BIN').read_bytes()==(out/'LIMIT.BIN').read_bytes()
 paths=[ROOT/name for name in INPUTS]+[Path(__file__)]
 result=dict(passed=True,summaries=summaries,sources={str(p.relative_to(ROOT)):sha(p)for p in paths},
  artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()},original_inputs=[],scope=__doc__+
  ' Allocator wrappers constrain requested block sizes while returning real CRT allocations. The control removes only the fallback. Exact inventories, all logical fault positions, bounded all-attempt failure,100 cycles and real far-heap/foreign ownership verified.')
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summaries))
if __name__=='__main__':main()
