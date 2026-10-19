#!/usr/bin/env python3
"""Build native numeric operands with real flow/stack and modeled service fixture."""
import hashlib
import json
from pathlib import Path
import subprocess
from build_aspect_flow import ASM as FLOW_ASM,C as FLOW_C,ENTRIES as FLOW_ENTRIES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-operands'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[(1,'addresses',0xd19e,0xd1b0),(2,'predicates',0xdb10,0xdb65),
       (3,'numeric',0xdc48,0xdd26),(4,'token',0xe0f1,0xe129)]
ENTRIES={'is_integer':0xdb10,'is_long':0xdb2b,'is_float':0xdb48,
         'frame_plus':0xd19e,'frame_minus':0xd1a6,'next_token':0xe0f1,
         'read_integer':0xdc48,'read_long':0xdcc1}
FILE_BASE=109184-0xd0d0
LOOKAHEAD=0xe38c
BANK_A,BANK_B,LONG_BANK,SYSTEM=0xd126,0xd482,0xd582,0xe3c4
BACKENDS={'byte':0x4cb4,'builtin_integer':0xd988,'builtin_long':0xda39,'invalid':0x4f90}

# Reuse the maintained source-owned file/flow callback fixture; do not read its
# generated build outputs. Numeric operations append to its near dispatch table.
ASM=FLOW_ASM
old='operations: dw '+','.join('op_'+name for name in FLOW_ENTRIES)+'\n'
assert ASM.count(old)==1
ASM=ASM.replace(old,old.rstrip()+','+','.join('operand_'+name for name in ENTRIES)+'\n')
ASM+='\nSEGMENT _TEXT\n'
ASM+='\n'.join('extern aspect_operand_'+name for name in ENTRIES)+'\n'
for name in ENTRIES:
    ASM+='operand_'+name+':\n'
    if name.startswith('is_'):ASM+=' push word [bp+6]\n'
    ASM+=' call aspect_operand_'+name+'\n ret\n'
ASM+=r'''
extern _model_byte,_model_builtin_integer,_model_builtin_long,_model_invalid
extern _invalid_returns
global aspect_dispatch_read,aspect_operand_builtin_integer,aspect_operand_builtin_long,aspect_operand_invalid
aspect_dispatch_read: jmp _model_byte
aspect_operand_builtin_integer:
 push bp
 mov bp,sp
 push word [bp+4]
 call _model_builtin_integer
 pop bx
 pop bp
 ret 2
aspect_operand_builtin_long:
 push bp
 mov bp,sp
 push word [bp+4]
 call _model_builtin_long
 pop bx
 pop bp
 ret 2
aspect_operand_invalid:
 call _model_invalid
 cmp word [_invalid_returns],0
 je run_aborted
 ret
SEGMENT _DATA
global aspect_operand_lookahead,aspect_operand_integer_bank_a,aspect_operand_integer_bank_b
 global aspect_operand_long_bank,aspect_operand_system_values
 global _lookahead,_bank_a,_bank_b,_long_bank,_system_values
aspect_operand_lookahead:
_lookahead: dw 0
aspect_operand_integer_bank_a:
_bank_a: times 256 dw 0
aspect_operand_integer_bank_b:
_bank_b: times 256 dw 0
aspect_operand_long_bank:
_long_bank: times 256 dd 0
aspect_operand_system_values:
_system_values: times 256 dq 0
'''
C=FLOW_C.split('int main(void)')[0]+r'''
extern unsigned lookahead,bank_a[256],bank_b[256];
extern unsigned long long_bank[256];
extern unsigned char system_values[256][8];
static unsigned char local_values[128];
unsigned invalid_returns;
static unsigned invalids,builtin_index,builtin_integers,builtin_longs;
unsigned model_byte(void){
 --file_record.remaining;
 if(file_record.remaining>=0)return *((unsigned char *)file_record.pointer++);
 return model_refill(stream_token);
}
unsigned model_builtin_integer(unsigned index){++builtin_integers;builtin_index=index;return index^0x7654;}
unsigned long model_builtin_long(unsigned index){++builtin_longs;builtin_index=index;return 0x89abcdefUL^index;}
unsigned long model_invalid(void){++invalids;return 0xaabbccddUL;}
static void setup(unsigned length){unsigned i;unsigned long value;
 reset(length);lookahead=0;invalids=builtin_integers=builtin_longs=0;invalid_returns=1;
 for(i=0;i<256;++i){bank_a[i]=i*257^0x1234;bank_b[i]=i*73^0x9876;long_bank[i]=0x87654321UL^((unsigned long)i*0x01010101UL);
  value=0xfedcba98UL^((unsigned long)i*0x01010101UL);memcpy(system_values[i],&value,4);memset(system_values[i]+4,0x77,4);}
 for(i=0;i<128;++i)local_values[i]=(unsigned char)(i*37+11);
}
static unsigned long result(void){return ((unsigned long)result_high<<16)|result_low;}
int main(void){unsigned i,j,token,n,word,accepted;unsigned long value;FILE *f;
 for(i=0;i<512;++i){setup(0);call(OP_is_integer,i,0);ck(result_low==(i%10==1));call(OP_is_long,i,0);ck(result_low==(i%10==2));call(OP_is_float,i,0);ck(result_low==(i%10==3));}
 for(j=0;j<3;++j){i=j==0?0x7fff:j==1?0x8000:0xffff;setup(0);call(OP_is_integer,i,0);ck(result_low==(i%10==1));call(OP_is_long,i,0);ck(result_low==(i%10==2));call(OP_is_float,i,0);ck(result_low==(i%10==3));}
 for(i=1;i<256;++i){setup(1);lookahead=i;call(OP_next_token,0,0);ck(result_low==i && lookahead==0 && position()==0 && refills==0);}
 for(n=0;n<2;++n){setup(1);data[0]=0x98;file_record.remaining=n;head=n;call(OP_next_token,0,0);ck(result_low==0x98 && position()==1 && refills==!n);}
 setup(0);call(OP_next_token,0,0);ck(result_low==0xffff);
 for(i=0;i<256;++i){
  setup(2);data[0]=101;data[1]=i;call(OP_read_integer,0,0);ck(result_low==bank_a[i] && !invalids);
  setup(2);data[0]=141;data[1]=i;call(OP_read_integer,0,0);ck(result_low==bank_b[i]);
  setup(2);data[0]=121;data[1]=i;call(OP_read_integer,0,0);memcpy(&word,system_values[i],2);ck(result_low==word);
  setup(2);data[0]=111;data[1]=i;call(OP_read_integer,0,0);ck(result_low==(i^0x7654) && builtin_index==i && builtin_integers==1);
  setup(2);data[0]=142;data[1]=i;call(OP_read_long,0,0);ck(result()==long_bank[i]);
  setup(2);data[0]=122;data[1]=i;call(OP_read_long,0,0);memcpy(&value,system_values[i],4);ck(result()==value);
  setup(2);data[0]=112;data[1]=i;call(OP_read_long,0,0);ck(result()==(0x89abcdefUL^i) && builtin_index==i && builtin_longs==1);
 }
 for(i=0;i<32;++i){
  setup(3);frame=(unsigned)local_values+64;data[0]=151;data[1]=i;data[2]=0;call(OP_read_integer,0,0);memcpy(&word,local_values+64-i,2);ck(result_low==word);
  setup(3);frame=(unsigned)local_values+32;data[0]=161;data[1]=i;data[2]=0;call(OP_read_integer,0,0);memcpy(&word,local_values+32+i,2);ck(result_low==word);
  setup(3);frame=(unsigned)local_values+64;data[0]=152;data[1]=i;data[2]=0;call(OP_read_long,0,0);memcpy(&value,local_values+64-i,4);ck(result()==value);
  setup(3);frame=(unsigned)local_values+32;data[0]=162;data[1]=i;data[2]=0;call(OP_read_long,0,0);memcpy(&value,local_values+32+i,4);ck(result()==value);
 }
 for(i=0;i<256;++i){
  setup(3);data[0]=171;data[1]=i;data[2]=i^0xff;call(OP_read_integer,0,0);ck(result_low==(i|((i^0xff)<<8)));
  setup(2);data[0]=181;data[1]=i;call(OP_read_integer,0,0);ck(result_low==i);
  setup(5);data[0]=172;value=0x89abcdefUL^((unsigned long)i*0x01010101UL);put32(1,value);call(OP_read_long,0,0);ck(result()==value);
 }
 for(token=0;token<256;++token){
  accepted=token==101||token==111||token==121||token==141||token==151||token==161||token==171||token==181;
  if(!accepted){setup(1);data[0]=token;call(OP_read_integer,0,0);ck(invalids==1 && result_low==0xccdd);}
  accepted=token==112||token==122||token==142||token==152||token==162||token==172;
  if(!accepted){setup(1);data[0]=token;call(OP_read_long,0,0);ck(invalids==1 && result()==0xaabbccddUL);}
 }
 setup(0);lookahead=171;call(OP_read_integer,0,0);ck(result_low==0xffff && lookahead==0);
 setup(1);data[0]=131;invalid_returns=0;call(OP_read_integer,0,0);ck(invalids==1 && aborted);
 setup(1);data[0]=131;invalid_returns=0;call(OP_read_long,0,0);ck(invalids==1 && aborted);
 f=fopen("DONE.TXT","w");if(!f)return 2;
 fprintf(f,"ASPECT_OPERANDS %lu checks %u failures\n",checks,failures);fclose(f);
 printf("ASPECT_OPERANDS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'src/aspect/numeric_operands.asm';flow=ROOT/'src/aspect/control_flow.asm'
    stack=ROOT/'src/aspect/value_stack.asm';move=ROOT/'reconstruction/erase/move_bytes.asm'
    inc='-I'+str(ROOT/'reconstruction/uart')+'/'
    for unit,name,start,end in UNITS:
        subprocess.run(['nasm','-f','bin','-DASPECT_OPERANDS_FLAT',f'-DASPECT_OPERANDS_UNIT={unit}',inc,str(source),'-o',str(OUT/(name+'.bin'))],check=True)
        assert len((OUT/(name+'.bin')).read_bytes())==end-start
    subprocess.run(['nasm','-f','obj',inc,str(source),'-o',str(OUT/'operands.obj')],check=True)
    from build_aspect_flow import UNITS as FLOW_UNITS
    for unit,name,start,end in FLOW_UNITS:
        subprocess.run(['nasm','-f','bin','-DASPECT_FLOW_FLAT',f'-DASPECT_FLOW_UNIT={unit}',inc,str(flow),'-o',str(OUT/('flow-'+name+'.bin'))],check=True)
    subprocess.run(['nasm','-f','obj',inc,str(flow),'-o',str(OUT/'flow.obj')],check=True)
    for fmt,defs,target in [('bin',['-DASPECT_STACK_FLAT'],'stack.bin'),('obj',[],'stack.obj')]:
        subprocess.run(['nasm','-f',fmt,*defs,inc,str(stack),'-o',str(OUT/target)],check=True)
    for fmt,defs,target in [('bin',[],'copy.bin'),('obj',['-DERASE_OMF'],'copy.obj')]:
        subprocess.run(['nasm','-f',fmt,*defs,inc,str(move),'-o',str(OUT/target)],check=True)
    (OUT/'callbacks.asm').write_text(ASM)
    operations=list(FLOW_ENTRIES)+list(ENTRIES)
    definitions='\n'.join(f'#define OP_{name} {i}' for i,name in enumerate(operations))+'\n'
    (OUT/'diagnostic.c').write_text(definitions+C)
    subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=OPERANDS.map','-fe=OPERANDS.EXE',
                    str(OUT/'diagnostic.c'),str(OUT/'operands.obj'),str(OUT/'flow.obj'),str(OUT/'stack.obj'),str(OUT/'copy.obj'),str(OUT/'callbacks.obj')],cwd=OUT,check=True)
    inputs=[source,flow,stack,move,ROOT/'reconstruction/uart/encodings.inc',ROOT/'standalone/build_aspect_flow.py',Path(__file__).resolve()]
    report=dict(binary_sha256=sha((OUT/'OPERANDS.EXE').read_bytes()),original_inputs=[],
                units=[dict(name=name,start=start,end_exclusive=end,source_file_start=FILE_BASE+start,
                            bytes=end-start,sha256=sha((OUT/(name+'.bin')).read_bytes())) for _,name,start,end in UNITS],
                sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in inputs},
                scope='Native numeric selection/token/address predicates with real flow/stack/copy. Modeled byte/CRT/builtin/invalid callbacks and source-owned banks; no original services, floating arithmetic, or full VM claim.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
