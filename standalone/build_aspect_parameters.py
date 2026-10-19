#!/usr/bin/env python3
"""Build exact typed parameter handlers with real operand/stack/copy code."""
import hashlib
import json
from pathlib import Path
import subprocess
from build_aspect_operands import ASM as OPER_ASM,C as OPER_C,ENTRIES as OPER_ENTRIES,UNITS as OPER_UNITS
from build_aspect_flow import ENTRIES as FLOW_ENTRIES,UNITS as FLOW_UNITS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-parameters'
START,END,FILE_START=0xd1b0,0xd1f2,109408
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
ENTRIES=dict(stack_address=0xd1b0,push_numeric=0xd1b8,push_string=0xd1ea)

ASM=OPER_ASM
old='operations: dw '+','.join('op_'+name for name in FLOW_ENTRIES)+','+','.join('operand_'+name for name in OPER_ENTRIES)+'\n'
assert ASM.count(old)==1
ASM=ASM.replace(old,old.rstrip()+','+','.join('parameter_'+name for name in ENTRIES)+'\n')
ASM+='\nSEGMENT _TEXT\n'+'\n'.join('extern aspect_parameter_'+name for name in ENTRIES)+'\n'
for name in ENTRIES:ASM+='parameter_'+name+':\n call aspect_parameter_'+name+'\n ret\n'
ASM+=r'''
extern _parameter_float,_parameter_string,_parameter_available
global aspect_expr_read_float,aspect_string_read
aspect_expr_read_float:
 cmp word [_parameter_available],0
 je run_aborted
 jmp _parameter_float
aspect_string_read:
 cmp word [_parameter_available],0
 je run_aborted
 jmp _parameter_string
'''
C=OPER_C.split('int main(void)')[0]+r'''
static unsigned char float_bytes[8],string_bytes[81];
unsigned parameter_available;static unsigned float_reads,string_reads,forwarded_token;
unsigned parameter_float(void){++float_reads;forwarded_token=lookahead;lookahead=0;return (unsigned)float_bytes;}
unsigned parameter_string(void){++string_reads;return (unsigned)string_bytes;}
static void parameter_setup(unsigned length){unsigned i;setup(length);parameter_available=1;float_reads=string_reads=forwarded_token=0;
 for(i=0;i<8;++i)float_bytes[i]=(unsigned char)(i*73);for(i=0;i<81;++i)string_bytes[i]=(unsigned char)(i*29);}
static void pushed(unsigned length,const void *expected){
 ck(!aborted && pointer==(unsigned)arena+length && !memcmp(arena,expected,length));ck(arena[length]==0xa5);ck(!abi_bad && !errors);}
int main(void){unsigned i,j,k,policy,start,length,value;unsigned long wide;FILE *f;
 for(i=0;i<256;++i){
  parameter_setup(2);data[0]=101;data[1]=i;call(OP_push_numeric,0,0);pushed(2,&bank_a[i]);ck(lookahead==0);
  parameter_setup(2);data[0]=142;data[1]=i;call(OP_push_numeric,0,0);pushed(4,&long_bank[i]);ck(lookahead==0);
  parameter_setup(3);data[0]=171;data[1]=i;data[2]=i^255;value=i|((i^255)<<8);call(OP_push_numeric,0,0);pushed(2,&value);
  parameter_setup(5);data[0]=172;wide=0x89abcdefUL^((unsigned long)i*0x01010101UL);put32(1,wide);call(OP_push_numeric,0,0);pushed(4,&wide);
 }
 for(i=0;i<256;++i){
  parameter_setup(1);data[0]=i;
  if(i%10==1){
   /* Invalid selectors are allowed to return by this diagnostic service. */
   if(i!=101&&i!=111&&i!=121&&i!=141&&i!=151&&i!=161&&i!=171&&i!=181){call(OP_push_numeric,0,0);value=0xccdd;pushed(2,&value);ck(invalids==1);}
  }else if(i%10==2){
   if(i!=112&&i!=122&&i!=142&&i!=152&&i!=162&&i!=172){call(OP_push_numeric,0,0);wide=0xaabbccddUL;pushed(4,&wide);ck(invalids==1);}
  }else{call(OP_push_numeric,0,0);pushed(8,float_bytes);ck(float_reads==1 && forwarded_token==i && lookahead==0);}
 }
 parameter_setup(0);call(OP_push_numeric,0,0);pushed(8,float_bytes);ck(forwarded_token==0xffff);
 for(i=0;i<16;++i){parameter_setup(0);pointer=(unsigned)arena+i;call(OP_push_string,0,0);ck(pointer==(unsigned)arena+i+81 && !memcmp(arena+i,string_bytes,81));ck(string_reads==1 && arena[i+81]==0xa5);}
 for(i=0;i<32;++i){parameter_setup(3);frame=(unsigned)local_values+64;data[0]=151;data[1]=i;data[2]=0;call(OP_push_numeric,0,0);pushed(2,local_values+64-i);}
 for(i=0;i<16;++i)for(j=0;j<16;++j){parameter_setup(2);pointer=(unsigned)arena+i;data[0]=j;data[1]=0;call(OP_stack_address,0,0);ck(result_low==(unsigned)arena+i+j && pointer==(unsigned)arena+i);}
 /* Operand processing precedes reserve failure; native error return continues. */
 for(k=0;k<4;++k)for(policy=0;policy<2;++policy){
  parameter_setup(5);length=k==0?2:k==1?4:k==2?8:81;start=(unsigned)arena+0x3aca-length+1;pointer=start;error_returns=policy;
  data[0]=k==0?181:k==1?172:123;data[1]=0x34;data[2]=0x12;data[3]=0x78;data[4]=0x56;
  call(k==3?OP_push_string:OP_push_numeric,0,0);ck(errors==1 && aborted==!policy);ck(pointer==start+(policy?length:0));
  ck(position()==(k==0?2:k==1?5:k==2?1:0));if(!policy)ck(arena[0x3aca-length+1]==0xa5);
 }
 for(i=0;i<2;++i){parameter_setup(1);data[0]=i?2:1;invalid_returns=0;call(OP_push_numeric,0,0);ck(aborted && pointer==(unsigned)arena && !errors);}
 parameter_setup(1);data[0]=123;parameter_available=0;call(OP_push_numeric,0,0);ck(aborted && pointer==(unsigned)arena && !errors);
 parameter_setup(0);parameter_available=0;call(OP_push_string,0,0);ck(aborted && pointer==(unsigned)arena && !errors);
 f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_PARAMETERS %lu checks %u failures\n",checks,failures);fclose(f);
 printf("ASPECT_PARAMETERS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''
C=C.replace('static unsigned long result(void){return ((unsigned long)result_high<<16)|result_low;}','')


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=ROOT/'src/aspect/parameters.asm';oper=ROOT/'src/aspect/numeric_operands.asm';flow=ROOT/'src/aspect/control_flow.asm';stack=ROOT/'src/aspect/value_stack.asm';copy=ROOT/'reconstruction/erase/move_bytes.asm';inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 for fmt,defs,name in [('bin',['-DASPECT_PARAMETERS_FLAT'],'parameters.bin'),('obj',[],'parameters.obj')]:subprocess.run(['nasm','-f',fmt,*defs,inc,str(source),'-o',str(OUT/name)],check=True)
 assert len((OUT/'parameters.bin').read_bytes())==END-START
 for prefix,units,macro,path in [('operand-',OPER_UNITS,'ASPECT_OPERANDS',oper),('flow-',FLOW_UNITS,'ASPECT_FLOW',flow)]:
  for unit,name,_,_ in units:subprocess.run(['nasm','-f','bin',f'-D{macro}_FLAT',f'-D{macro}_UNIT={unit}',inc,str(path),'-o',str(OUT/(prefix+name+'.bin'))],check=True)
  subprocess.run(['nasm','-f','obj',inc,str(path),'-o',str(OUT/(prefix.rstrip('-')+'.obj'))],check=True)
 for fmt,defs,name in [('bin',['-DASPECT_STACK_FLAT'],'stack.bin'),('obj',[],'stack.obj')]:subprocess.run(['nasm','-f',fmt,*defs,inc,str(stack),'-o',str(OUT/name)],check=True)
 for fmt,defs,name in [('bin',[],'copy.bin'),('obj',['-DERASE_OMF'],'copy.obj')]:subprocess.run(['nasm','-f',fmt,*defs,inc,str(copy),'-o',str(OUT/name)],check=True)
 (OUT/'callbacks.asm').write_text(ASM)
 definitions='\n'.join(f'#define OP_{name} {i}' for i,name in enumerate(list(FLOW_ENTRIES)+list(OPER_ENTRIES)+list(ENTRIES)))+'\n'
 (OUT/'diagnostic.c').write_text(definitions+C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=PARAM.map','-fe=PARAM.EXE',str(OUT/'diagnostic.c'),*[str(OUT/(n+'.obj')) for n in ['parameters','operand','flow','stack','copy','callbacks']]],cwd=OUT,check=True)
 inputs=[source,oper,flow,stack,copy,ROOT/'reconstruction/uart/encodings.inc',ROOT/'standalone/build_aspect_flow.py',ROOT/'standalone/build_aspect_operands.py',Path(__file__).resolve()]
 report=dict(binary_sha256=sha((OUT/'PARAM.EXE').read_bytes()),flat_sha256=sha((OUT/'parameters.bin').read_bytes()),original_inputs=[],sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in inputs},scope='Three native parameter primitives plus actual numeric/flow/typed stack/copy. Float/string readers return opaque fixture buffers; no float/string parser acceptance, real builtin services, or complete VM claim.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
