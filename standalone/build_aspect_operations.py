#!/usr/bin/env python3
"""Build recovered ASPECT comparison/assignment routines without original inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-operations'
START,END=0xd4a5,0xd943
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
FILE_BASE=0xd9b0
ENTRIES=dict(metadata=0xd4a5,store_result=0xd4b9,store_boolean=0xd4f7,
 load_first=0xd50f,word_result=0xd536,dword_result=0xd550,eight_result=0xd573,
 logical_and=0xd5a2,logical_not=0xd5c7,logical_or=0xd5d9,equal=0xd5fe,
 less_equal=0xd63b,less=0xd67a,greater_equal=0xd6b9,greater=0xd6f8,
 not_equal=0xd737,decrement=0xd774,increment=0xd7aa,assign=0xd7e0,
 assign_chained=0xd7e7,assignment=0xd7ef)
DATA=dict(source_type=0xe3c0,target_type=0xe3c2,lookahead=0xe38c,
 word_value=0xd474,dword_value=0xd476,float_value=0xe150)
BACKENDS={0x4cb4:'read',0xdb7d:'boolean',0xdbc6:'signed',0xdbdd:'stage',
 0xdc48:'integer',0xdcc1:'long',0xdd26:'float_read',0xde4d:'integer_address',
 0xde92:'long_address',0xdecb:'float_address',0xd408:'float_transform',
 0xd446:'float_operand',0xd458:'float_destination',0xd48c:'float_compare'}

ASM = r"""
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern erase_move_bytes
global _run_ops
_run_ops:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov [_saved_sp],sp
 mov word [_aborted],0
 mov si,0x1357
 mov di,0x2468
 mov bx,[bp+4]
 shl bx,1
 call word [cs:operations+bx]
 mov [_result_low],ax
 mov [_result_high],dx
 cmp sp,[_saved_sp]
 jne ops_bad
 cmp si,0x1357
 jne ops_bad
 cmp di,0x2468
 je ops_done
ops_bad:
 inc word [_abi_bad]
 jmp short ops_done
ops_unavailable:
 mov word [_aborted],1
 mov sp,[_saved_sp]
ops_done:
 pop es
 pop di
 pop si
 pop bp
 ret
"""
ASM += '\n'.join('extern aspect_ops_'+n for n in ENTRIES)+'\n'
ASM += 'operations: dw '+','.join('op_'+n for n in ENTRIES)+'\n'
for name in ENTRIES:
 ASM += 'op_'+name+':\n'
 if name in ('store_boolean','assignment'):ASM += ' push word [bp+6]\n'
 ASM += ' call aspect_ops_'+name+'\n ret\n'
for symbol,callback in {
 'aspect_dispatch_read':'read_code','aspect_expr_boolean':'read_boolean',
 'aspect_expr_signed':'read_long','aspect_expr_stage':'stage_float',
 'aspect_operand_read_integer':'read_integer','aspect_operand_read_long':'read_long',
 'aspect_expr_read_float':'read_float','aspect_expr_integer_address':'next_address',
 'aspect_expr_long_address':'next_address','aspect_expr_float_address':'next_address'}.items():
 ASM += f'extern _{callback}\nglobal {symbol}\n{symbol}: jmp _{callback}\n'
for symbol,flag in [('aspect_operand_is_integer','classifier_integer'),('aspect_operand_is_long','classifier_long')]:
 ASM += f'extern _{flag}\nglobal {symbol}\n{symbol}:\n mov ax,[_{flag}]\n ret 2\n'
for symbol in ['aspect_ops_float_transform','aspect_ops_float_operand','aspect_ops_float_destination','aspect_ops_float_compare']:
 ASM += f'global {symbol}\n{symbol}: jmp ops_unavailable\n'
ASM += 'SEGMENT _DATA public class=DATA use16\nGROUP DGROUP _DATA\n'
for symbol,cname,storage in [('aspect_ops_source_type','source_type','dw 0'),
 ('aspect_ops_target_type','target_type','dw 0'),('aspect_operand_lookahead','lookahead','dw 0'),
 ('aspect_ops_word_value','word_value','dw 0'),('aspect_ops_dword_value','dword_value','dd 0'),
 ('aspect_ops_float_value','float_value','times 8 db 0')]:
 ASM += f'global {symbol},_{cname}\n{symbol}:\n_{cname}: {storage}\n'
for n in ['saved_sp','aborted','abi_bad','result_low','result_high']:
 ASM += f'global _{n}\n_{n}: dw 0\n'

C = r"""
#include <stdio.h>
#include <string.h>
extern unsigned source_type,target_type,lookahead,word_value,aborted,abi_bad,result_low,result_high;
extern unsigned long dword_value;extern unsigned char float_value[8];
extern void run_ops(unsigned op,unsigned argument);
unsigned classifier_integer,classifier_long;
static unsigned raw[4],ints[4],truth[4],raw_i,int_i,long_i,truth_i,address_i;
static unsigned long longs[4];
static unsigned char first[16],second[16],float_source[8];
static unsigned long checks;static unsigned failures;
static void ck(unsigned c){++checks;if(!c){++failures;printf("FAIL %lu\n",checks);}}
unsigned read_code(void){ck(raw_i<4);return raw[raw_i++];}
unsigned read_integer(void){ck(int_i<4);return ints[int_i++];}
unsigned long read_long(void){ck(long_i<4);return longs[long_i++];}
unsigned read_boolean(void){ck(truth_i<4);return truth[truth_i++];}
void stage_float(void){memcpy(float_value,float_source,8);}
unsigned read_float(void){return (unsigned)float_source;}
unsigned next_address(void){return (unsigned)(address_i++?second:first);}
static void reset(void){
 memset(raw,0,sizeof(raw));memset(ints,0,sizeof(ints));memset(longs,0,sizeof(longs));memset(truth,0,sizeof(truth));
 memset(first,0,sizeof(first));memset(second,0,sizeof(second));memcpy(float_source,"abcdefgh",8);memcpy(float_value,"ABCDEFGH",8);
 source_type=target_type=lookahead=word_value=0;dword_value=0;
 raw_i=int_i=long_i=truth_i=address_i=classifier_integer=classifier_long=aborted=abi_bad=0;
}
static void call(unsigned op,unsigned arg){run_ops(op,arg);ck(!abi_bad);}
static unsigned predicate(unsigned p,long a,long b){
 switch(p){case 0:return a==b;case 1:return a<=b;case 2:return a<b;case 3:return a>=b;case 4:return a>b;default:return a!=b;}
}
static const unsigned compare_ops[]={OP_equal,OP_less_equal,OP_less,OP_greater_equal,OP_greater,OP_not_equal};
static const unsigned words[]={0,1,0x7fff,0x8000,0xffff};
static const unsigned long dwords[]={0UL,1UL,32767UL,32768UL,65535UL,65536UL,0x7fffffffUL,0x80000000UL,0xffffffffUL};
int main(void){unsigned a,b,p,s,t,ch,v;unsigned long wide;FILE *f;
 ck(sizeof(unsigned)==2 && sizeof(long)==4);
 for(v=0;v<256;++v){reset();raw[0]=v;call(OP_metadata,0);ck(source_type==(v&3) && target_type==(v>>2));}
 reset();raw[0]=0xffff;call(OP_metadata,0);ck(source_type==3 && target_type==0x3fff);
 for(s=0;s<4;++s){reset();source_type=s;word_value=0x8001;dword_value=0x12345678UL;
  call(OP_word_result,0);ck(result_low==(s==0?0x8001:s==1?0x5678:0x4241));
  call(OP_dword_result,0);wide=(unsigned long)result_high*65536UL+result_low;
  ck(wide==(s==0?0xffff8001UL:s==1?0x12345678UL:0x44434241UL));
 }
 for(p=0;p<6;++p){
  for(a=0;a<5;++a)for(b=0;b<5;++b){reset();raw[0]=0;ints[0]=words[b];ints[1]=words[a];call(compare_ops[p],0);
   ck(!aborted && *(unsigned *)first==predicate(p,(int)words[a],(int)words[b]));}
  for(a=0;a<9;++a)for(b=0;b<9;++b){reset();raw[0]=1;longs[0]=dwords[b];longs[1]=dwords[a];call(compare_ops[p],0);
   ck(!aborted && *(unsigned *)first==predicate(p,(long)dwords[a],(long)dwords[b]));}
  reset();raw[0]=2;call(compare_ops[p],0);ck(aborted);
 }
 for(a=0;a<5;++a)for(b=0;b<5;++b){
  reset();truth[0]=words[a];truth[1]=words[b];call(OP_logical_and,0);ck(*(unsigned *)first==(words[a]!=0 && words[b]!=0));
  reset();truth[0]=words[a];truth[1]=words[b];call(OP_logical_or,0);ck(*(unsigned *)first==(words[a]!=0 || words[b]!=0));
  reset();truth[0]=words[a];call(OP_logical_not,0);ck(*(unsigned *)first==(words[a]==0));
 }
 for(s=0;s<2;++s)for(t=0;t<2;++t)for(ch=0;ch<3;++ch){reset();raw[0]=(t<<2)|s;ints[0]=0x8001;longs[0]=0x12345678UL;
  call(OP_assignment,ch);ck(!aborted);wide=t?*(unsigned long *)first:*(unsigned *)first;
  ck(wide==(t?(s?0x12345678UL:0xffff8001UL):(s?0x5678UL:0x8001UL)));
  if(ch)ck(!memcmp(first,second,t?4:2));
 }
 for(ch=0;ch<3;++ch){reset();raw[0]=10;call(OP_assignment,ch);ck(!aborted && !memcmp(first,"abcdefgh",8));if(ch)ck(!memcmp(first,second,8));}
 for(s=0;s<3;++s)for(p=0;p<2;++p){reset();raw[0]=101+s;classifier_integer=s==0;classifier_long=s==1;*(unsigned long *)first=0xffffffffUL;
  call(p?OP_increment:OP_decrement,0);
  if(s==0)ck(!aborted && *(unsigned *)first==(p?0:0xfffe));
  else if(s==1)ck(!aborted && *(unsigned long *)first==(p?0UL:0xfffffffeUL));else ck(aborted);
 }
 reset();source_type=0;call(OP_eight_result,0);ck(aborted);
 reset();source_type=2;call(OP_eight_result,0);ck(!aborted && result_low==(unsigned)float_value);
 reset();target_type=2;call(OP_store_boolean,1);ck(aborted);
 f=fopen("DONE.TXT","w");if(!f)return 2;
 fprintf(f,"ASPECT_OPERATIONS %lu checks %u failures\n",checks,failures);fclose(f);
 printf("ASPECT_OPERATIONS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
"""

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=ROOT/'src/aspect/numeric_operations.asm'
 operands=ROOT/'src/aspect/numeric_operands.asm'
 copy=ROOT/'reconstruction/erase/move_bytes.asm'
 inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 for fmt,defs,name in [('bin',['-DASPECT_OPERATIONS_FLAT'],'operations.bin'),('obj',[],'operations.obj')]:
  subprocess.run(['nasm','-f',fmt,*defs,inc,str(source),'-o',str(OUT/name)],check=True)
 assert len((OUT/'operations.bin').read_bytes())==END-START
 subprocess.run(['nasm','-f','bin','-DASPECT_OPERANDS_FLAT','-DASPECT_OPERANDS_UNIT=2',inc,str(operands),'-o',str(OUT/'predicates.bin')],check=True)
 for fmt,defs,name in [('bin',[],'copy.bin'),('obj',['-DERASE_OMF'],'copy.obj')]:
  subprocess.run(['nasm','-f',fmt,*defs,inc,str(copy),'-o',str(OUT/name)],check=True)
 (OUT/'callbacks.asm').write_text(ASM)
 definitions='\n'.join(f'#define OP_{name} {i}' for i,name in enumerate(ENTRIES))+'\n'
 (OUT/'diagnostic.c').write_text(definitions+C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=OPERATE.map','-fe=OPERATE.EXE',
  str(OUT/'diagnostic.c'),str(OUT/'operations.obj'),str(OUT/'copy.obj'),str(OUT/'callbacks.obj')],cwd=OUT,check=True)
 report=dict(binary_sha256=sha((OUT/'OPERATE.EXE').read_bytes()),original_inputs=[],start=START,end_exclusive=END,bytes=END-START,
  flat_sha256=sha((OUT/'operations.bin').read_bytes()),
  sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [source,operands,copy,ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]},
  scope='Source-only native numeric metadata/comparison/assignment plus native classification predicates and overlap-safe copy. Float and expression/system services remain external dependencies; no complete VM claim.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
