#!/usr/bin/env python3
"""Original-free native string component build with real near/far copy helpers."""
import hashlib,json,subprocess
from pathlib import Path
from build_aspect_operands import ASM as OPERAND_ASM,C as OPERAND_C,ENTRIES as OPERAND_ENTRIES,UNITS as OPERAND_UNITS
from build_aspect_flow import ENTRIES as FLOW_ENTRIES,UNITS as FLOW_UNITS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-strings'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
FILE_BASE=109184-0xd0d0
UNITS=[(1,'strings',0xdf04,0xe0cc,FILE_BASE),(2,'bounded',0xdd68,0xdd9c,FILE_BASE),
 (3,'length',0xde11,0xde1c,FILE_BASE),(4,'option',0xe0e4,0xe0f1,FILE_BASE),
 (5,'farcopy',0x9286,0x92a4,0x1200),(6,'getds',0x76b0,0x76b3,0x1200),
 (7,'count',0xeef0,0xeeff,55728),(8,'assign',0xef1d,0xef42,55728)]
ENTRIES=dict(read=0xdf04,read_destination=0xdf0b,read_indexed=0xdf13,read_global=0xdf71,
 next_scratch=0xdfc7,read_literal=0xdfea,flush=0xe0a4,bounded_integer=0xdd68,
 length_operand=0xde11,option_flag=0xe0e4,copy_count=0xeef0,assign=0xef1d)
TRANSFORM=bytes.fromhex('b3 35 0b c7 47 29 1d fb 1f 7f 05 59 17')
ASM=OPERAND_ASM
old='operations: dw '+','.join('op_'+n for n in FLOW_ENTRIES)+','+','.join('operand_'+n for n in OPERAND_ENTRIES)+'\n'
assert old in ASM
ASM=ASM.replace(old,old.rstrip()+','+','.join('string_'+n for n in ENTRIES)+'\n')
ASM+='\nSEGMENT _TEXT\n'
for name in ENTRIES:
 ASM+='extern aspect_string_'+name+'\nstring_'+name+':\n'
 if name in ('read_global','bounded_integer'):ASM+=' push word [bp+8]\n'
 if name in ('read_global','bounded_integer','read_indexed'):ASM+=' push word [bp+6]\n'
 ASM+=' call aspect_string_'+name+'\n ret\n'
ASM+='''
extern _model_string_builtin,_model_string_error,_string_error_stops
global aspect_string_builtin,aspect_string_error
aspect_string_builtin:
 push bp
 mov bp,sp
 push word [bp+4]
 call _model_string_builtin
 pop bx
 pop bp
 ret 2
aspect_string_error:
 push bp
 mov bp,sp
 push word [bp+4]
 call _model_string_error
 pop bx
 cmp word [_string_error_stops],0
 jne run_aborted
 pop bp
 ret 2
SEGMENT _DATA
'''
for native,cname,storage in [('aspect_string_bank_a','string_bank','times 810 db 0'),
 ('aspect_globals_table','string_globals','times 128 dd 0'),('aspect_string_pending_far','pending_far','dd 0'),
 ('aspect_string_pending_near','pending_near','dw 0'),('aspect_string_scratch','string_scratch','times 891 db 0'),
 ('aspect_string_scratch_pointer','scratch_pointer','dw 0'),('aspect_string_scratch_index','scratch_index','dw 0'),
 ('aspect_string_check_range','check_range','dw 0'),('aspect_dispatch_exit_state','exit_state','dw 0'),
 ('aspect_string_transform','transform','db '+','.join(str(b) for b in TRANSFORM))]:
 ASM+=f'global {native},_{cname}\n{native}:\n_{cname}: {storage}\n'
C=OPERAND_C.split('int main(void)')[0]
C=C.replace('ck(size==4 && count==1 && token==stream_token);','ck((size==1 || size==4) && token==stream_token);')
C+=r'''
#include <malloc.h>
#include "literal.h"
extern unsigned pending_near,scratch_index,scratch_pointer,check_range,exit_state;
extern unsigned long pending_far,string_globals[128];
extern unsigned char string_bank[810],string_scratch[891];
static unsigned char builtin_string[81];static unsigned string_errors,string_builtin_index;
unsigned string_error_stops;
unsigned model_string_builtin(unsigned index){string_builtin_index=index;return (unsigned)builtin_string;}
void model_string_error(unsigned code){++string_errors;ck(code==1);}
static void strings_setup(unsigned length){setup(length);pending_near=0;pending_far=0;scratch_index=0;check_range=1;exit_state=string_errors=string_error_stops=0;memset(string_scratch,0xa5,891);memset(string_bank,0x33,810);memset(builtin_string,0x44,81);}
int main(void){unsigned n,p,line,i,j,a,offset;unsigned char text[80],wire[82];aspect_literal_result enc;unsigned char __far *far_block;FILE *f;
 far_block=_fmalloc(243);ck(far_block!=0);if(!far_block)return 2;
 for(i=0;i<3;++i)string_globals[i]=(unsigned long)(far_block+i*81);
 for(n=1;n<=80;++n)for(p=0;p<2;++p)for(line=0;line<12;++line){
  for(i=0;i<n;++i)text[i]=(unsigned char)(33+(i*17+n)%90);
  ck(aspect_literal_encode(text,n,p,line,wire,82,&enc)==0);
  strings_setup(enc.wire_length);memcpy(data,wire,enc.wire_length);call(OP_read_literal,0,0);
  ck(result_low==(unsigned)string_scratch && !memcmp((void *)result_low,text,n) && ((unsigned char *)result_low)[n]==0);
  ck(position()==enc.wire_length && scratch_index==1);
 }
 strings_setup(0);for(i=0;i<33;++i){call(OP_next_scratch,0,0);ck(result_low==(unsigned)string_scratch+(i%11)*81 && scratch_index==(i+1)%11);}
 for(i=0;i<3;++i){for(j=0;j<81;++j)far_block[i*81+j]=(unsigned char)(j+i*31);
  strings_setup(0);call(OP_read_global,0,i);ck(!pending_near);for(j=0;j<81;++j)ck(((unsigned char *)result_low)[j]==far_block[i*81+j]);
  call(OP_read_global,1,i);ck(pending_near==result_low);memset((void *)pending_near,0x73,81);call(OP_flush,0,0);ck(!pending_near);for(j=0;j<81;++j)ck(far_block[i*81+j]==0x73);
 }
 for(i=0;i<10;++i){strings_setup(2);data[0]=100;data[1]=i;call(OP_read,0,0);ck(result_low==(unsigned)string_bank+81*i);}
 strings_setup(2);data[0]=110;data[1]=7;call(OP_read,0,0);ck(result_low==(unsigned)builtin_string && string_builtin_index==7);
 for(i=0;i<2;++i){strings_setup(3);frame=(unsigned)string_bank+400;data[0]=i?160:150;data[1]=33;data[2]=0;call(OP_read,0,0);ck(result_low==frame+(i?33:-33));}
 for(i=0;i<3;++i)for(n=0;n<5;++n){unsigned values[]={0,1,80,81,0xffff};strings_setup(3);data[0]=171;memcpy(data+1,values+n,2);check_range=i!=0;exit_state=i==2;call(OP_length_operand,0,0);ck(string_errors==((i!=0)&&(n>2)));ck(result_low==((i==2&&n>2)?0:values[n]));}
 for(i=0;i<4;++i){strings_setup(1);data[0]=i;call(OP_option_flag,0,0);ck(result_low==(i==1));}
 for(n=0;n<=80;n+=n<2?1:39){
  strings_setup(10);for(i=0;i<81;++i){string_bank[i]='D';builtin_string[i]='S';}string_bank[81]='D';
  data[0]=100;data[1]=0;data[2]=110;data[3]=0;data[4]=1;data[5]=171;data[6]=(unsigned char)n;data[7]=0;
  call(OP_assign,0,0);for(i=0;i<n;++i)ck(string_bank[i]=='S');ck(string_bank[n]==0 && string_bank[n+1]=='D');
 }
 strings_setup(5);data[0]=140;data[1]=0;data[2]=110;data[3]=0;data[4]=0;call(OP_assign,0,0);for(j=0;j<80;++j)ck(far_block[j]==0x44);ck(far_block[80]==0 && !pending_near);
 strings_setup(1);data[0]=99;call(OP_read,0,0);ck(invalids==1 && result_low==0xccdd);
 strings_setup(3);data[0]=171;data[1]=81;data[2]=0;string_error_stops=1;call(OP_length_operand,0,0);ck(aborted && string_errors==1);
 _ffree(far_block);f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_STRINGS %lu checks %u failures\n",checks,failures);fclose(f);printf("ASPECT_STRINGS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''
C=C.replace('unsigned n,p,line,i,j,a,offset;','unsigned n,p,line,i,j;')
C='\n'.join(line for line in C.splitlines() if not line.startswith(('static void put32(', 'static unsigned long result(')))+'\n'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 modules=[('strings','src/aspect/string_operands.asm','ASPECT_STRING_FLAT',[(u,n,a,b) for u,n,a,b,_ in UNITS]),('operands','src/aspect/numeric_operands.asm','ASPECT_OPERANDS_FLAT',OPERAND_UNITS),('flow','src/aspect/control_flow.asm','ASPECT_FLOW_FLAT',FLOW_UNITS)]
 sources=[]
 for name,rel,define,units in modules:
  source=ROOT/rel;sources.append(source)
  for unit,part,a,b in units:
   subprocess.run(['nasm','-f','bin','-D'+define,f'-D{define.replace("FLAT","UNIT")}={unit}',inc,str(source),'-o',str(OUT/(name+'-'+part+'.bin'))],check=True)
   assert len((OUT/(name+'-'+part+'.bin')).read_bytes())==b-a
  subprocess.run(['nasm','-f','obj',inc,str(source),'-o',str(OUT/(name+'.obj'))],check=True)
 for name,rel,defs in [('stack','src/aspect/value_stack.asm',['-DASPECT_STACK_FLAT']),('copy','reconstruction/erase/move_bytes.asm',[])]:
  source=ROOT/rel;sources.append(source)
  for fmt,flags in [('bin',defs),('obj',[] if name=='stack' else ['-DERASE_OMF'])]:subprocess.run(['nasm','-f',fmt,*flags,inc,str(source),'-o',str(OUT/(name+('.bin' if fmt=='bin' else '.obj')))],check=True)
 (OUT/'callbacks.asm').write_text(ASM)
 names=list(FLOW_ENTRIES)+list(OPERAND_ENTRIES)+list(ENTRIES)
 (OUT/'diagnostic.c').write_text('\n'.join(f'#define OP_{n} {i}' for i,n in enumerate(names))+'\n'+C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fm=STRINGS.map','-fe=STRINGS.EXE',str(OUT/'diagnostic.c'),str(ROOT/'src/aspect/literal.c'),*[str(OUT/(n+'.obj')) for n in ['strings','operands','flow','stack','copy','callbacks']]],cwd=OUT,check=True)
 sources += [ROOT/'src/aspect/literal.c',ROOT/'src/aspect/literal.h',ROOT/'standalone/build_aspect_operands.py',ROOT/'standalone/build_aspect_flow.py',ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
 report=dict(original_inputs=[],binary_sha256=sha((OUT/'STRINGS.EXE').read_bytes()),units={n:sha((OUT/('strings-'+n+'.bin')).read_bytes()) for _,n,_,_,_ in UNITS},sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},scope='Native string/numeric/frame/copy modules; source-owned CRT/builtin/error callbacks. Literal C codec supplies independent wire input. Real DOS far heap and native far copy; no full VM.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
