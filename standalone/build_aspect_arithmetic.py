#!/usr/bin/env python3
"""Build exact overlay17 arithmetic with explicit controlled long/float fixture."""
import hashlib
import json
from pathlib import Path
import subprocess
from build_aspect_operations import ASM as OPS_ASM,C as OPS_C,ENTRIES as OPS_ENTRIES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-arithmetic'
START,END=0xebb1,0xee4a
FILE_BASE=55728
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
ENTRIES=dict(add=0xebb1,bit_and=0xebe2,bit_not=0xec04,divide=0xec2a,modulo=0xec32,
 multiply=0xec3a,negate=0xec70,bit_or=0xeca1,shift_left=0xecc3,shift_right=0xece7,
 subtract=0xed0b,bit_xor=0xed3d,division=0xed5f,zero_divisor=0xee3c)
LONG_BACKENDS={0x9b90:'multiply',0x9bb0:'shift_left',0x9bcc:'shift_right',0x9af2:'divide',0x9b12:'modulo'}

ASM=OPS_ASM
old='operations: dw '+','.join('op_'+name for name in OPS_ENTRIES)+'\n'
assert ASM.count(old)==1
ASM=ASM.replace(old,old.rstrip()+','+','.join('arith_'+name for name in ENTRIES)+'\n')
ASM=ASM.replace('_float_value: times 8 db 0','_float_value: times 16 db 0')
assert '_float_value: times 16 db 0' in ASM
ASM+='\nSEGMENT _TEXT\n'+'\n'.join('extern aspect_arith_'+name for name in ENTRIES)+'\n'
for name in ENTRIES:
 ASM+='arith_'+name+':\n'
 if name=='division':ASM+=' push word [bp+6]\n'
 ASM+=' call aspect_arith_'+name+'\n ret\n'
for name in LONG_BACKENDS.values():
 count=2 if name.startswith('shift_') else 3
 ASM+=f'extern _model_long_{name}\nglobal aspect_long_{name}\naspect_long_{name}:\n push bp\n mov bp,sp\n'
 for offset in reversed(range(4,4+count*2,2)):ASM+=f' push word [bp+{offset}]\n'
 ASM+=f' call _model_long_{name}\n add sp,byte {count*2}\n pop bp\n ret {count*2}\n'
for symbol in ('aspect_ops_float_transform','aspect_ops_float_operand'):
 old=symbol+': jmp ops_unavailable\n'
 assert ASM.count(old)==1
 ASM=ASM.replace(old,symbol+':\n push bp\n mov bp,sp\n mov ax,[bp+4]\n mov [_float_service],ax\n pop bp\n jmp ops_unavailable\n')
ASM+=r'''
extern _record_arithmetic_error,_error_returns,_model_compare
 global aspect_arith_error,aspect_expr_compare
aspect_arith_error:
 push bp
 mov bp,sp
 push word [bp+4]
 call _record_arithmetic_error
 pop bx
 cmp word [_error_returns],0
 je ops_unavailable
 pop bp
 ret 2
aspect_expr_compare: jmp _model_compare
SEGMENT _DATA
global aspect_expr_stage_types,aspect_expr_float_zero,_stage_types,_float_service
aspect_expr_stage_types:
_stage_types: times 2 db 0
aspect_expr_float_zero: times 8 db 0
_float_service: dw 0
'''
C='unsigned stage_calls;\n'+OPS_C.split('static unsigned predicate(')[0]
C=C.replace('float_value[8]','float_value[16]').replace('void stage_float(void){memcpy(float_value,float_source,8);}',
 'void stage_float(void){memcpy(float_value+(stage_calls++?8:0),float_source,8);}')
assert 'stage_calls++' in C
C+=r'''
extern unsigned char stage_types[2];extern unsigned float_service;
unsigned error_returns;static unsigned error_calls,last_error,long_calls;
void record_arithmetic_error(unsigned code){++error_calls;last_error=code;ck(code==2);}
unsigned model_compare(unsigned left,unsigned right,unsigned length){int r=memcmp((void *)left,(void *)right,length);return r<0?0xffff:r>0?1:0;}
static unsigned long join(unsigned low,unsigned high){return ((unsigned long)high<<16)|low;}
void model_long_multiply(unsigned long *dest,unsigned low,unsigned high){++long_calls;*dest*=join(low,high);}
void model_long_shift_left(unsigned long *dest,unsigned count){++long_calls;count&=255;while(count--)*dest<<=1;}
void model_long_shift_right(unsigned long *dest,unsigned count){++long_calls;count&=255;while(count--)*dest=(*dest>>1)|(*dest&0x80000000UL);}
void model_long_divide(unsigned long *dest,unsigned low,unsigned high){++long_calls;*dest=(long)*dest/(long)join(low,high);}
void model_long_modulo(unsigned long *dest,unsigned low,unsigned high){++long_calls;*dest=(long)*dest%(long)join(low,high);}
static void setup(unsigned source,unsigned target){reset();raw[0]=(target<<2)|source;
 stage_calls=stage_types[0]=stage_types[1]=float_service=error_calls=last_error=long_calls=0;error_returns=1;}
static unsigned shift_word(unsigned value,unsigned count,unsigned right){count&=255;while(count--){if(right)value=(value>>1)|(value&0x8000);else value<<=1;}return value;}
static unsigned expected_word(unsigned op,unsigned a,unsigned b){
 switch(op){case OP_add:return a+b;case OP_subtract:return a-b;case OP_multiply:return a*b;
 case OP_bit_and:return a&b;case OP_bit_or:return a|b;case OP_bit_xor:return a^b;
 case OP_negate:return -a;case OP_bit_not:return ~a;case OP_shift_left:return shift_word(a,b,0);
 case OP_shift_right:return shift_word(a,b,1);case OP_divide:return (int)a/(int)b;default:return (int)a%(int)b;}}
static unsigned long expected_long(unsigned op,unsigned long a,unsigned long b){
 unsigned count;switch(op){case OP_add:return a+b;case OP_subtract:return a-b;case OP_multiply:return a*b;
 case OP_bit_and:return a&b;case OP_bit_or:return a|b;case OP_bit_xor:return a^b;case OP_negate:return -a;case OP_bit_not:return ~a;
 case OP_shift_left:count=(unsigned)b&255;while(count--)a<<=1;return a;
 case OP_shift_right:count=(unsigned)b&255;while(count--)a=(a>>1)|(a&0x80000000UL);return a;
 case OP_divide:return (long)a/(long)b;default:return (long)a%(long)b;}}
static const unsigned operations[]={OP_add,OP_subtract,OP_multiply,OP_bit_and,OP_bit_or,OP_bit_xor,OP_negate,OP_bit_not,OP_shift_left,OP_shift_right,OP_divide,OP_modulo};
static const unsigned words[]={0,1,2,0x7fff,0x8000,0xffff};
static const unsigned long wides[]={0UL,1UL,2UL,65535UL,65536UL,0x7fffffffUL,0x80000000UL,0xffffffffUL};
int main(void){unsigned p,a,b,t,op,w,count;unsigned long v;FILE *f;
 for(p=0;p<12;++p){op=operations[p];
  for(a=0;a<6;++a)for(b=0;b<6;++b)for(t=0;t<2;++t){
   if((op==OP_divide||op==OP_modulo)&&(!words[b]||(words[a]==0x8000&&words[b]==0xffff)))continue;
   setup(0,t);ints[0]=words[a];ints[1]=words[b];call(op,0);w=expected_word(op,words[a],words[b]);
   ck(!aborted && !error_calls);if(t)ck(*(unsigned long *)first==(unsigned long)(long)(int)w);else ck(*(unsigned *)first==w);
  }
  for(a=0;a<8;++a)for(b=0;b<8;++b)for(t=0;t<2;++t){
   if((op==OP_divide||op==OP_modulo)&&(!wides[b]||(wides[a]==0x80000000UL&&wides[b]==0xffffffffUL)))continue;
   setup(1,t);longs[0]=wides[a];longs[1]=wides[b];call(op,0);v=expected_long(op,wides[a],wides[b]);
   ck(!aborted && !error_calls);if(t)ck(*(unsigned long *)first==v);else ck(*(unsigned *)first==(unsigned)v);
  }
 }
 /* Real8086 word shifts include full low8-bit counts, including32/255. */
 for(a=0;a<6;++a)for(count=0;count<256;++count){
  setup(0,0);ints[0]=words[a];ints[1]=count;call(OP_shift_left,0);ck(*(unsigned *)first==shift_word(words[a],count,0));
  setup(0,0);ints[0]=words[a];ints[1]=count;call(OP_shift_right,0);ck(*(unsigned *)first==shift_word(words[a],count,1));
 }
 for(p=0;p<2;++p)for(t=0;t<2;++t){
  setup(t,t);ints[0]=13;longs[0]=13;call(p?OP_modulo:OP_divide,0);ck(error_calls==1 && last_error==2 && truth_i==1 && !aborted && !memcmp(first,"\0\0\0\0",4));
  setup(t,t);error_returns=0;ints[0]=13;longs[0]=13;call(p?OP_modulo:OP_divide,0);ck(error_calls==1 && aborted && truth_i==0);
 }
 for(p=0;p<4;++p){op=p==0?OP_add:p==1?OP_subtract:p==2?OP_multiply:OP_negate;setup(2,2);call(op,0);ck(aborted && float_service==(p==0?0:p==1?0xb5:p==2?0x7d:0x7e));}
 for(p=0;p<2;++p){setup(2,2);call(p?OP_modulo:OP_divide,0);ck(aborted && float_service==(p?0x7b:0x26));
  setup(2,2);memset(float_source,0,8);call(p?OP_modulo:OP_divide,0);ck(!aborted && error_calls==1 && truth_i==1);
 }
 f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_ARITHMETIC %lu checks %u failures\n",checks,failures);fclose(f);
 printf("ASPECT_ARITHMETIC %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=ROOT/'src/aspect/arithmetic.asm';ops=ROOT/'src/aspect/numeric_operations.asm';copy=ROOT/'reconstruction/erase/move_bytes.asm';inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 for fmt,defs,name in [('bin',['-DASPECT_ARITHMETIC_FLAT'],'arithmetic.bin'),('obj',[],'arithmetic.obj')]:subprocess.run(['nasm','-f',fmt,*defs,inc,str(source),'-o',str(OUT/name)],check=True)
 assert len((OUT/'arithmetic.bin').read_bytes())==END-START
 for fmt,defs,name in [('bin',['-DASPECT_OPERATIONS_FLAT'],'operations.bin'),('obj',[],'operations.obj')]:subprocess.run(['nasm','-f',fmt,*defs,inc,str(ops),'-o',str(OUT/name)],check=True)
 for fmt,defs,name in [('bin',[],'copy.bin'),('obj',['-DERASE_OMF'],'copy.obj')]:subprocess.run(['nasm','-f',fmt,*defs,inc,str(copy),'-o',str(OUT/name)],check=True)
 predicates=ROOT/'src/aspect/numeric_operands.asm'
 subprocess.run(['nasm','-f','bin','-DASPECT_OPERANDS_FLAT','-DASPECT_OPERANDS_UNIT=2',inc,str(predicates),'-o',str(OUT/'predicates.bin')],check=True)
 (OUT/'callbacks.asm').write_text(ASM)
 definitions='\n'.join(f'#define OP_{name} {i}' for i,name in enumerate(list(OPS_ENTRIES)+list(ENTRIES)))+'\n'
 (OUT/'diagnostic.c').write_text(definitions+C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=ARITH.map','-fe=ARITH.EXE',str(OUT/'diagnostic.c'),str(OUT/'arithmetic.obj'),str(OUT/'operations.obj'),str(OUT/'copy.obj'),str(OUT/'callbacks.obj')],cwd=OUT,check=True)
 inputs=[source,ops,copy,predicates,ROOT/'reconstruction/uart/encodings.inc',ROOT/'standalone/build_aspect_operations.py',Path(__file__).resolve()]
 report=dict(binary_sha256=sha((OUT/'ARITH.EXE').read_bytes()),flat_sha256=sha((OUT/'arithmetic.bin').read_bytes()),original_inputs=[],
  sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in inputs},scope='Exact overlay17 handlers with actual numeric operations/copy; long arithmetic, operands, errors and float availability are explicit controlled callbacks, not native helper or full VM claims.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
