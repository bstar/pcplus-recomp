#!/usr/bin/env python3
"""Build native string commands and real string/CRT/operand/copy components."""
import hashlib,json,subprocess
from pathlib import Path
from build_aspect_strings import ASM as STRING_ASM,C as STRING_C,ENTRIES as STRING_ENTRIES,UNITS as STRING_UNITS
from build_aspect_operands import ENTRIES as OPER_ENTRIES,UNITS as OPER_UNITS
from build_aspect_flow import ENTRIES as FLOW_ENTRIES,UNITS as FLOW_UNITS

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-string-commands'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
ENTRIES=dict(compare_bytes=0xeeff,concat=0xef42,compare=0xef9c,length=0xefca,lower=0xefd7,
 get_char=0xefe3,set_char=0xeff8,fill=0xf00d,subcopy=0xf02f,upper=0xf07f,substr=0xf08b)
COMMAND_UNITS=[(1,0xeeff,0xef1d,55728),(2,0xef42,0xf0b5,55728)]
SERVICE_UNITS=[(1,0x9476,0x94a1,0x1200),(2,0x9be8,0x9c06,0x1200),(3,0x9736,0x9763,0x1200),
 (4,0xdde3,0xddee,55728),(5,0xde1c,0xde27,55728),(6,0xde3a,0xde4d,55728),(7,0xda0c,0xda10,55728),(8,0xda28,0xda32,55728)]
# Operand wrappers use the independently verified overlay16 coordinate base.
SERVICE_UNITS=[(u,a,b,(109184-0xd0d0) if u>=4 else base) for u,a,b,base in SERVICE_UNITS]
EXPR_UNITS=[(1,0xd2a0,0xd2d6,109184-0xd0d0),(2,0xd3f2,0xd408,109184-0xd0d0),
 (3,0xdb7d,0xdc48,109184-0xd0d0),(4,0xde4d,0xdf04,109184-0xd0d0),(5,0x9ac0,0x9ae7,0x1200)]
LEGACY=[('strlen','reconstruction/program_exec/strlen.asm','PROGRAM_EXEC_OMF','program_strlen',0x8d18,0x8d33),
 ('strncmp','reconstruction/program_exec/strncmp.asm','PROGRAM_EXEC_OMF','program_strncmp',0x9c06,0x9c40),
 ('concat','reconstruction/directory_dial/append.asm','DIRECTORY_DIAL_OMF','directory_dial_append_original',0x9852,0x9887),
 ('upper','reconstruction/directory_dial/uppercase.asm','DIRECTORY_DIAL_OMF','directory_dial_upper_original',0x9128,0x9146)]
ASM=STRING_ASM
old='operations: dw '+','.join('op_'+n for n in FLOW_ENTRIES)+','+','.join('operand_'+n for n in OPER_ENTRIES)+','+','.join('string_'+n for n in STRING_ENTRIES)+'\n'
assert ASM.count(old)==1
ASM=ASM.replace(old,old.rstrip()+','+','.join('strcmd_'+n for n in ENTRIES)+'\n')
ASM+='\nSEGMENT _TEXT\n'
for name in ENTRIES:ASM+='extern aspect_strcmd_'+name+'\nstrcmd_'+name+':\n call aspect_strcmd_'+name+'\n ret\n'
for name,_,_,native,_,_ in LEGACY:ASM+=f'extern {native}\nglobal aspect_string_{name}\naspect_string_{name}: jmp {native}\n'
ASM+='global aspect_expr_read_float\naspect_expr_read_float: jmp run_aborted\nSEGMENT _DATA\n'
for native,cname,size in [('aspect_string_compare_result','comparison_result','dw 0'),('aspect_expr_float_bank','float_bank','times 1024 db 0'),
 ('aspect_expr_stage_index','stage_index','dw 0'),('aspect_expr_stage_types','stage_types','times 10 db 0'),
 ('aspect_ops_float_value','float_values','times 80 db 0'),('aspect_expr_float_zero','float_zero','times 8 db 0')]:
 ASM+=f'global {native},_{cname}\n{native}:\n_{cname}: {size}\n'
C='unsigned last_string_error;\n'+STRING_C.split('int main(void)')[0]
C=C.replace('ck(code==1);','last_string_error=code;ck(code==1 || code==3);')
C+=r'''
extern unsigned comparison_result,stage_index;extern unsigned char stage_types[10],float_values[80];
static void command_setup(unsigned length){strings_setup(length);last_string_error=comparison_result=stage_index=0;memset(stage_types,0,10);memset(float_values,0,80);memset(string_bank,0xa5,810);memset(builtin_string,0,81);}
static void word_at(unsigned offset,unsigned value){memcpy(data+offset,&value,2);}
static void literal(unsigned offset,unsigned value){data[offset]=171;word_at(offset+1,value);}
static void operands(unsigned option,unsigned count){data[0]=100;data[1]=0;data[2]=100;data[3]=1;data[4]=option;literal(5,count);}
static unsigned compare_bytes(const unsigned char *a,const unsigned char *b,unsigned n){int v=memcmp(a,b,n);return v<0?0xffff:v>0?1:0;}
int main(void){unsigned i,j,n,index,stop;unsigned char before[162],expected[162];unsigned char __far *far_block;FILE *f;
 far_block=_fmalloc(81);ck(far_block!=0);if(!far_block)return 2;string_globals[0]=(unsigned long)far_block;
 for(n=0;n<=80;++n){
  command_setup(8);operands(1,n);memset(string_bank,'A',162);string_bank[80]=string_bank[161]=0;if(n)string_bank[81+n-1]='B';
  call(OP_compare_bytes,0,0);ck(comparison_result==compare_bytes(string_bank,string_bank+81,n));
  head=0;file_record.pointer=(unsigned)data;file_record.remaining=0;file_record.flags=0;call(OP_compare,0,0);ck(comparison_result==compare_bytes(string_bank,string_bank+81,n));
 }
 for(i=0;i<256;++i)for(j=0;j<3;++j){
  command_setup(5);operands(0,0);string_bank[0]=(unsigned char)i;string_bank[1]=0;string_bank[81]=(unsigned char)(j==0?i:j==1?i^128:0);string_bank[82]=0;
  call(OP_compare,0,0);ck(comparison_result==(i==string_bank[81]?0:i<string_bank[81]?0xffff:1));
 }
 for(i=0;i<=80;i+=i<2?1:13)for(n=0;n<=80;n+=n<2?1:13)for(stop=0;stop<2;++stop){
  command_setup(8);data[0]=100;data[1]=0;data[2]=110;data[3]=0;data[4]=1;literal(5,n);memset(string_bank,'D',i);string_bank[i]=0;memset(builtin_string,'S',80);builtin_string[80]=0;
  memcpy(before,string_bank,81);string_error_stops=stop;call(OP_concat,0,0);
  if(i+n>80){ck(string_errors==1 && last_string_error==3);if(stop){ck(aborted && !memcmp(string_bank,before,81));continue;}}
  else ck(!string_errors && !aborted);
  index=n>80-i?80-i:n;for(j=0;j<i;++j)ck(string_bank[j]=='D');for(j=0;j<index;++j)ck(string_bank[i+j]=='S');ck(string_bank[i+index]==0);
 }
 command_setup(5);data[0]=100;data[1]=0;data[2]=110;data[3]=0;data[4]=0;memcpy(string_bank,"ABC",4);memcpy(builtin_string,"def",4);call(OP_concat,0,0);ck(!strcmp((char *)string_bank,"ABCdef"));
 for(n=0;n<=80;++n){command_setup(4);data[0]=100;data[1]=0;data[2]=141;data[3]=0;memset(string_bank,'L',n);string_bank[n]=0;call(OP_length,0,0);ck(bank_b[0]==n);}
 for(i=1;i<256;++i){
  command_setup(2);data[0]=100;data[1]=0;string_bank[0]=(unsigned char)i;string_bank[1]=0;call(OP_lower,0,0);ck(string_bank[0]==(i>='A'&&i<='Z'?i+32:i));
  command_setup(2);data[0]=100;data[1]=0;string_bank[0]=(unsigned char)i;string_bank[1]=0;call(OP_upper,0,0);ck(string_bank[0]==(i>='a'&&i<='z'?i-32:i));
 }
 for(index=0;index<80;++index){
  command_setup(7);data[0]=100;data[1]=0;literal(2,index);data[5]=141;data[6]=0;call(OP_get_char,0,0);ck(bank_b[0]==0xa5);
  command_setup(8);data[0]=100;data[1]=0;literal(2,index);literal(5,255-index);call(OP_set_char,0,0);ck(string_bank[index]==255-index && string_bank[80]==0xa5);
 }
 for(n=0;n<=80;++n){command_setup(9);data[0]=100;data[1]=0;literal(2,0xfe);data[5]=1;literal(6,n);call(OP_fill,0,0);for(i=0;i<n;++i)ck(string_bank[i]==0xfe);ck(string_bank[80]==0 && string_bank[81]==0xa5);if(n<80)ck(string_bank[n]==0xa5);}
 for(index=0;index<80;index+=7)for(n=0;n<=80;n+=11)for(stop=0;stop<2;++stop){
  command_setup(10);data[0]=100;data[1]=0;data[2]=100;data[3]=1;literal(4,index);literal(7,n);memset(string_bank+81,'S',81);memcpy(before,string_bank,162);string_error_stops=stop;
  call(OP_subcopy,0,0);if(index+n>80 && stop){ck(aborted && last_string_error==3 && !memcmp(before,string_bank,162));continue;}
  j=n>80-index?80-index:n;memcpy(expected,before,162);memset(expected+index,'S',j);expected[80]=0;ck(!memcmp(string_bank,expected,162));ck(string_errors==(index+n>80));
  command_setup(10);data[0]=100;data[1]=0;data[2]=100;data[3]=1;literal(4,index);literal(7,n);for(i=0;i<162;++i)string_bank[81+i]=(unsigned char)(i*37+1);memcpy(before,string_bank,81);
  call(OP_substr,0,0);memcpy(expected,before,81);for(i=0;i<n;++i)expected[i]=(unsigned char)((index+i)*37+1);expected[n]=0;ck(!memcmp(string_bank,expected,81) && !string_errors);
 }
 /* Real far destination round trip through scratch plus native flush. */
 command_setup(2);data[0]=140;data[1]=0;_fmemcpy(far_block,"aBc\0",4);call(OP_upper,0,0);ck(far_block[0]=='A'&&far_block[1]=='B'&&far_block[2]=='C'&&!pending_near);
 _ffree(far_block);f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_STRING_COMMANDS %lu checks %u failures\n",checks,failures);fclose(f);printf("ASPECT_STRING_COMMANDS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''
# The inherited C helper is unused here; the compiler enforces warning-free C.
C='\n'.join(line for line in C.splitlines() if not line.startswith(('static void put32(', 'static unsigned long result(')))+'\n'


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 OUT.mkdir(parents=True,exist_ok=True);inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 modules=[('commands','src/aspect/string_commands.asm','ASPECT_STRING_COMMANDS',COMMAND_UNITS),
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
 names=list(FLOW_ENTRIES)+list(OPER_ENTRIES)+list(STRING_ENTRIES)+list(ENTRIES)
 (OUT/'diagnostic.c').write_text('\n'.join(f'#define OP_{n} {i}' for i,n in enumerate(names))+'\n'+C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fm=STRCMD.map','-fe=STRCMD.EXE',str(OUT/'diagnostic.c'),str(ROOT/'src/aspect/literal.c'),*objects,str(OUT/'callbacks.obj')],cwd=OUT,check=True)
 sources += [ROOT/'src/aspect/literal.c',ROOT/'src/aspect/literal.h',ROOT/'standalone/build_aspect_strings.py',ROOT/'standalone/build_aspect_operands.py',ROOT/'standalone/build_aspect_flow.py',ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
 report=dict(original_inputs=[],binary_sha256=sha((OUT/'STRCMD.EXE').read_bytes()),units=units,sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},scope='11native string commands with actual string/numeric/frame/stack/near-far copy, text CRT helpers and byte/index/store wrappers. File,builtin,error and unavailable-float callbacks remain explicit. No full VM or arbitrary-input safety claim.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='units'},indent=2))


if __name__=='__main__':main()
