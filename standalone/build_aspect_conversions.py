#!/usr/bin/env python3
"""Build exact native ASPECT conversion handlers, scanner and actual CRT services."""
import hashlib,json,subprocess
from pathlib import Path
from build_aspect_string_commands import (ASM as BASE_ASM,C as BASE_C,ENTRIES as COMMAND_ENTRIES,
 COMMAND_UNITS,SERVICE_UNITS,EXPR_UNITS,LEGACY,STRING_UNITS,OPER_UNITS,FLOW_UNITS,
 FLOW_ENTRIES,OPER_ENTRIES,STRING_ENTRIES)
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-conversions'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
ENTRIES=dict(atoi=0xea4b,atol=0xea5f,scan_numeric=0xea7f,itoa=0xeaf4,ltoa=0xeb0e)
UNITS=[(1,0xea4b,0xeae1,55728),(2,0xeaf4,0xeb38,55728)]
CRT_UNITS=[(1,0x984e,0x9851,0x1200),(2,0x9b32,0x9b35,0x1200),
 (3,0x8e6c,0x8e87,0x1200),(4,0x9ae8,0x9af2,0x1200),
 (5,0xa5e8,0xa647,0x1200),(6,0xa7ce,0xa822,0x1200),(7,0x9b36,0x9b90,0x1200)]
ASM=BASE_ASM
old='operations: dw '+','.join('op_'+n for n in FLOW_ENTRIES)+','+','.join('operand_'+n for n in OPER_ENTRIES)+','+','.join('string_'+n for n in STRING_ENTRIES)+','+','.join('strcmd_'+n for n in COMMAND_ENTRIES)+'\n'
assert ASM.count(old)==1
ASM=ASM.replace(old,old.rstrip()+','+','.join('convert_'+n for n in ENTRIES)+'\n')
ASM+='\nSEGMENT _TEXT\n'
for name in ENTRIES:
 ASM+='extern aspect_convert_'+name+'\nconvert_'+name+':\n'
 if name=='scan_numeric':ASM+=' push word [bp+8]\n push word [bp+6]\n'
 ASM+=' call aspect_convert_'+name+'\n ret\n'
ASM+="""
SEGMENT _DATA
global aspect_convert_candidate_chars,aspect_convert_ctype,_convert_ctype
aspect_convert_candidate_chars: db '-.0123456789',0
aspect_convert_ctype:
_convert_ctype: times 256 db 0
"""
C=BASE_C.split('int main(void)')[0]
C='\n'.join(line for line in C.splitlines() if not line.startswith(('static void operands(', 'static unsigned compare_bytes(')))+'\n'
C+=r'''
extern unsigned char convert_ctype[256];
static unsigned scan_expected(const unsigned char *s,unsigned flag){unsigned i=0;for(;s[i];++i){
 if(s[i]>='0'&&s[i]<='9')break;
 if((s[i]=='-'||(flag&&s[i]=='.'))&&s[i+1]>='0'&&s[i+1]<='9')break;
 }return i;}
static unsigned long parse_expected(const unsigned char *s){unsigned long v=0;unsigned minus=0;
 while(*s==' '||*s=='\t')++s;if(*s=='-'||*s=='+'){minus=*s=='-';++s;}
 while(*s>='0'&&*s<='9'){v=v*10+(*s-'0');++s;}return minus?0UL-v:v;}
static void convert_setup(unsigned length){unsigned i;command_setup(length);for(i=0;i<256;++i)convert_ctype[i]=(i>='0'&&i<='9')?4:0;}
int main(void){
 static const char *cases[]={"","x","0","-0","+123","prefix=-123suffix",".25","-.25","--123","-x.42","1.234","+x-9",
 "32767","32768","-32768","-32769","65535","65536","2147483647","2147483648","-2147483648","-2147483649",
 "4294967295","4294967296","999999999999999999999999999999999999","abc- def.ghi9","abc-","abc.","  +27","\t-42","\n99"};
 unsigned i,j,k,off,flag;unsigned long value;char expected[40];unsigned char __far *far_block;FILE *f;
 for(i=0;i<sizeof(cases)/sizeof(cases[0]);++i){
  for(j=0;j<3;++j){flag=j==2?0xffff:j;convert_setup(0);strcpy((char *)builtin_string,cases[i]);
   off=scan_expected(builtin_string,flag);call(OP_scan_numeric,flag,(unsigned)builtin_string);ck(result_low==(unsigned)builtin_string+off && !aborted && !abi_bad);}
  value=parse_expected((const unsigned char *)cases[i]+scan_expected((const unsigned char *)cases[i],0));
  convert_setup(4);strcpy((char *)string_bank,cases[i]);data[0]=100;data[1]=0;data[2]=141;data[3]=0;call(OP_atoi,0,0);ck(bank_b[0]==(unsigned)value && position()==4 && !aborted);
  convert_setup(4);strcpy((char *)string_bank,cases[i]);data[0]=100;data[1]=0;data[2]=142;data[3]=0;call(OP_atol,0,0);ck(long_bank[0]==value && position()==4 && !aborted);
 }
 for(i=0;i<256;++i)for(j=0;j<2;++j){convert_setup(0);builtin_string[0]=(unsigned char)i;memcpy(builtin_string+1,"-x.9",5);off=scan_expected(builtin_string,j);call(OP_scan_numeric,j,(unsigned)builtin_string);ck(result_low==(unsigned)builtin_string+off);}
 for(i=0;i<256;++i)for(j=0;j<2;++j){
  value=j?(0xffff0000UL|((unsigned long)i*257)):(unsigned long)i*257;
  convert_setup(5);literal(0,(unsigned)value);data[3]=100;data[4]=0;call(OP_itoa,0,0);sprintf(expected,"%d",(int)value);ck(!strcmp((char *)string_bank,expected) && position()==5 && !pending_near);
  convert_setup(7);data[0]=172;memcpy(data+1,&value,4);data[5]=100;data[6]=0;call(OP_ltoa,0,0);sprintf(expected,"%ld",(long)value);ck(!strcmp((char *)string_bank,expected) && position()==7 && !pending_near);
 }
 for(k=0;k<4;++k){static const unsigned long edges[]={0UL,0x7fffffffUL,0x80000000UL,0xffffffffUL};
  value=edges[k];convert_setup(7);data[0]=172;memcpy(data+1,&value,4);data[5]=100;data[6]=0;call(OP_ltoa,0,0);sprintf(expected,"%ld",(long)value);ck(!strcmp((char *)string_bank,expected));}
 /* Native conversion writes the actual near scratch and flushes far ownership. */
 far_block=_fmalloc(81);ck(far_block!=0);if(!far_block)return 2;string_globals[0]=(unsigned long)far_block;
 convert_setup(5);_fmemset(far_block,0x5a,81);literal(0,0x8000);data[3]=140;data[4]=0;call(OP_itoa,0,0);ck(!_fstrcmp(far_block,"-32768")&&!pending_near&&far_block[7]==0x5a);
 convert_setup(7);value=0x80000000UL;data[0]=172;memcpy(data+1,&value,4);data[5]=140;data[6]=0;call(OP_ltoa,0,0);ck(!_fstrcmp(far_block,"-2147483648")&&!pending_near);
 convert_setup(4);_fmemcpy(far_block,"find -42",9);data[0]=140;data[1]=0;data[2]=142;data[3]=0;call(OP_atol,0,0);ck(long_bank[0]==0xffffffd6UL&&!pending_near);_ffree(far_block);
 f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_CONVERSIONS %lu checks %u failures\n",checks,failures);fclose(f);printf("ASPECT_CONVERSIONS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''

def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 OUT.mkdir(parents=True,exist_ok=True);inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 modules=[('conversions','src/aspect/conversions.asm','ASPECT_CONVERSIONS',UNITS),
  ('conversion-crt','src/aspect/conversion_services.asm','ASPECT_CONVERSION_SERVICES',CRT_UNITS),
  ('commands','src/aspect/string_commands.asm','ASPECT_STRING_COMMANDS',COMMAND_UNITS),
  ('services','src/aspect/string_services.asm','ASPECT_STRING_SERVICES',SERVICE_UNITS),
  ('expression','src/aspect/expression_support.asm','ASPECT_EXPR',EXPR_UNITS),
  ('strings','src/aspect/string_operands.asm','ASPECT_STRING',[(u,a,b,base) for u,_,a,b,base in STRING_UNITS]),
  ('operands','src/aspect/numeric_operands.asm','ASPECT_OPERANDS',[(u,a,b,109184-0xd0d0) for u,_,a,b in OPER_UNITS]),
  ('flow','src/aspect/control_flow.asm','ASPECT_FLOW',[(u,a,b,109184-0xd0d0) for u,_,a,b in FLOW_UNITS])]
 sources=[];objects=[];units=[]
 for name,rel,macro,parts in modules:
  source=ROOT/rel;sources.append(source);obj=OUT/(name+'.obj');subprocess.run(['nasm','-f','obj',inc,str(source),'-o',str(obj)],check=True);objects.append(str(obj))
  for unit,a,b,base in parts:
   target=OUT/f'{name}{unit}.bin';subprocess.run(['nasm','-f','bin',f'-D{macro}_FLAT',f'-D{macro}_UNIT={unit}',inc,str(source),'-o',str(target)],check=True);assert target.stat().st_size==b-a
   units.append(dict(name=target.name,start=a,end_exclusive=b,file_base=base,sha256=sha(target.read_bytes())))
 for name,rel,macro,_,a,b in LEGACY:
  source=ROOT/rel;sources.append(source)
  for fmt,flags in [('bin',[]),('obj',['-D'+macro])]:subprocess.run(['nasm','-f',fmt,*flags,inc,str(source),'-o',str(OUT/(name+'.'+fmt))],check=True)
  objects.append(str(OUT/(name+'.obj')));units.append(dict(name=name+'.bin',start=a,end_exclusive=b,file_base=0x1200,sha256=sha((OUT/(name+'.bin')).read_bytes())))
 for name,rel,defs,a,b,base in [('stack','src/aspect/value_stack.asm',['-DASPECT_STACK_FLAT'],0xd0d0,0xd195,109184-0xd0d0),('copy','reconstruction/erase/move_bytes.asm',[],0x85b4,0x85fc,0x1200)]:
  source=ROOT/rel;sources.append(source)
  for fmt,flags in [('bin',defs),('obj',[] if name=='stack' else ['-DERASE_OMF'])]:subprocess.run(['nasm','-f',fmt,*flags,inc,str(source),'-o',str(OUT/(name+'.'+fmt))],check=True)
  objects.append(str(OUT/(name+'.obj')));units.append(dict(name=name+'.bin',start=a,end_exclusive=b,file_base=base,sha256=sha((OUT/(name+'.bin')).read_bytes())))
 (OUT/'callbacks.asm').write_text(ASM)
 names=list(FLOW_ENTRIES)+list(OPER_ENTRIES)+list(STRING_ENTRIES)+list(COMMAND_ENTRIES)+list(ENTRIES)
 (OUT/'diagnostic.c').write_text('\n'.join(f'#define OP_{n} {i}' for i,n in enumerate(names))+'\n'+C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fm=CONVERT.map','-fe=CONVERT.EXE',str(OUT/'diagnostic.c'),str(ROOT/'src/aspect/literal.c'),*objects,str(OUT/'callbacks.obj')],cwd=OUT,check=True)
 sources += [ROOT/'src/aspect/literal.c',ROOT/'src/aspect/literal.h',ROOT/'standalone/build_aspect_string_commands.py',ROOT/'standalone/build_aspect_strings.py',ROOT/'standalone/build_aspect_operands.py',ROOT/'standalone/build_aspect_flow.py',ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
 report=dict(original_inputs=[],binary_sha256=sha((OUT/'CONVERT.EXE').read_bytes()),units=units,sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},scope='Four exact conversion handlers plus scanner with actual native CRT, string/numeric/lvalue/near-far copy components. File,builtin,error,unavailable-float callbacks explicit. No complete VM or arbitrary-input safety claim.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='units'},indent=2))


if __name__=='__main__':main()
