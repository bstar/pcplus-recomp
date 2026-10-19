#!/usr/bin/env python3
"""Build native ASPECT console commands and source-owned DOS callback diagnostic."""
import hashlib,json,subprocess
from pathlib import Path
from build_aspect_string_commands import (ASM as BASE_ASM,C as BASE_C,ENTRIES as COMMAND_ENTRIES,
 COMMAND_UNITS,SERVICE_UNITS,EXPR_UNITS,LEGACY,STRING_UNITS,OPER_UNITS,FLOW_UNITS,
 FLOW_ENTRIES,OPER_ENTRIES,STRING_ENTRIES)
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-console'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
ENTRIES=dict(exit=0x4eb5,message=0x5029,pause=0x507b,decode=0x4934,print_line=0x3abd,
 print=0x3adb,pause_operand=0xdd9c,native_wait_ticks=0x6b98,native_wait_second=0x6bb6)
UNITS=[(1,0x4eb5,0x4ebc,0x1200),(2,0x5029,0x5058,0x1200),
 (3,0x507b,0x50aa,0x1200),(4,0x4934,0x498b,0x1200),
 (5,0x3abd,0x3af8,0x1200),(6,0xdd9c,0xdda7,55728),(7,0x6b98,0x6bbe,0x1200)]
ASM=BASE_ASM
old='operations: dw '+','.join('op_'+n for n in FLOW_ENTRIES)+','+','.join('operand_'+n for n in OPER_ENTRIES)+','+','.join('string_'+n for n in STRING_ENTRIES)+','+','.join('strcmd_'+n for n in COMMAND_ENTRIES)+'\n'
assert ASM.count(old)==1
ASM=ASM.replace(old,old.rstrip()+','+','.join('console_'+n for n in ENTRIES)+'\n')
ASM+='\nSEGMENT _TEXT\n'
for name in ENTRIES:
 ASM+='extern aspect_console_'+name+'\nconsole_'+name+':\n'
 if name=='decode':ASM+=' push word [bp+8]\n'
 if name in ('decode','print_line','print','native_wait_ticks'):ASM+=' push word [bp+6]\n'
 ASM+=' call aspect_console_'+name+'\n'
 if name=='decode':ASM+=' add sp,4\n'
 if name in ('print_line','print'):ASM+=' pop bx\n'
 ASM+=' ret\n'
ASM+=r'''
extern _console_emit,_console_poll,_console_wait
global aspect_console_emit_byte,aspect_console_cancel_poll,aspect_console_wait_second
aspect_console_emit_byte: jmp _console_emit
aspect_console_cancel_poll: jmp _console_poll
aspect_console_wait_second: jmp _console_wait
SEGMENT _DATA
global aspect_console_message_mode,_message_mode
aspect_console_message_mode:
_message_mode: dw 1
'''
C=BASE_C.split('int main(void)')[0]
C='\n'.join(line for line in C.splitlines() if not line.startswith(('static void operands(', 'static unsigned compare_bytes(')))+'\n'
C+=r'''
#include <dos.h>
extern unsigned message_mode;
static unsigned char emitted[512];static unsigned emit_count,polls,waits,cancel_after;
void console_emit(unsigned value){ck(value<=255 && emit_count<sizeof(emitted));if(emit_count<sizeof(emitted))emitted[emit_count++]=(unsigned char)value;}
unsigned console_poll(void){++polls;return cancel_after&&polls>=cancel_after;}
void console_wait(void){++waits;}
static void console_setup(unsigned length){command_setup(length);memset(string_bank,0,810);emit_count=polls=waits=cancel_after=0;message_mode=1;memset(emitted,0xa5,sizeof(emitted));}
static unsigned decode_expected(const unsigned char *s,unsigned char *d){unsigned i=0,n=0,b;while(s[i]){b=s[i++];if(b=='^'){b=s[i++];if(b=='@')b=255;else if(b=='^'&&s[i]=='^'){++i;b='^';}else b&=31;}d[n++]=(unsigned char)b;}d[n]=0;return n;}
int main(void){
 static const char *cases[]={"","HELLO","^@","^^","^^^","^^^^","A^GB","^[31mRED^[0m","^A^B^C^D","^z^a^?","END^"};
 unsigned i,j,n,mode,k,count,stop;unsigned char expected[128],decoded[128];unsigned __far *ticks=(unsigned __far *)MK_FP(0,0x46c);unsigned before;FILE *f;
 for(i=0;i<sizeof(cases)/sizeof(cases[0]);++i)for(mode=0;mode<3;++mode){
  console_setup(2);message_mode=mode==2?0xffff:mode;strcpy((char *)string_bank,cases[i]);n=decode_expected(string_bank,expected);
  data[0]=100;data[1]=0;call(OP_message,0,0);k=(unsigned)strlen((char *)expected);ck(!memcmp(emitted,expected,k));
  ck(emit_count==k+(mode?2:0));if(mode)ck(emitted[k]==13&&emitted[k+1]==10);ck(position()==2&&!aborted&&!abi_bad&&exit_state==0);
 }
 for(i=1;i<256;++i){console_setup(2);string_bank[0]=(unsigned char)i;if(i=='^')string_bank[1]='A';data[0]=100;data[1]=0;
  n=decode_expected(string_bank,expected);call(OP_message,0,0);ck(emit_count==n+2&&!memcmp(emitted,expected,n));}
 for(n=0;n<=80;++n){console_setup(2);memset(string_bank,'X',n);data[0]=100;data[1]=0;call(OP_message,0,0);ck(emit_count==n+2);for(i=0;i<n;++i)ck(emitted[i]=='X');}
 console_setup(0);memcpy(builtin_string,"A^^^B^@C^Z",11);n=decode_expected(builtin_string,expected);memset(decoded,0xa5,sizeof(decoded));call(OP_decode,(unsigned)builtin_string,(unsigned)decoded);ck(!memcmp(decoded,expected,n+1)&&decoded[n+1]==0xa5);
 for(i=0;i<4;++i){static const unsigned values[]={0,1,999,0xffff};console_setup(0);exit_state=values[i];call(OP_exit,0,0);ck(exit_state==1&&!emit_count&&!polls&&!waits);}
 for(i=0;i<6;++i)for(j=0;j<5;++j){static const unsigned counts[]={0,1,2,17,255,32767};static const unsigned stops[]={0,1,2,17,32767};
  count=counts[i];stop=stops[j];console_setup(3);literal(0,count);cancel_after=stop;call(OP_pause,0,0);
  ck(comparison_result==(stop&&stop<=count));ck(polls==(stop&&stop<=count?stop:count));ck(waits==(stop&&stop<=count?stop-1:count));ck(position()==3&&!aborted&&!abi_bad);
 }
 for(i=0;i<2;++i){console_setup(3);literal(0,0xffff);string_error_stops=i;cancel_after=1;call(OP_pause,0,0);ck(last_string_error==1&&string_errors==1&&aborted==i);if(i)ck(!polls&&!waits);else ck(polls==1&&waits==0&&comparison_result==0);}
 /* Disabled range checking retains signed16-bit result after unsigned countdown. */
 console_setup(3);check_range=0;literal(0,0x8001);cancel_after=1;call(OP_pause,0,0);ck(polls==1&&!waits&&comparison_result==0);
 /* Actual BIOS clock test; PAUSE cases above count modeled wait callbacks. */
 console_setup(0);before=*ticks;call(OP_native_wait_second,0,0);ck((unsigned)(*ticks-before)>=19&&!abi_bad);before=*ticks;call(OP_native_wait_ticks,0,0);ck((unsigned)(*ticks-before)>=1&&!abi_bad);
 f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_CONSOLE %lu checks %u failures\n",checks,failures);fclose(f);printf("ASPECT_CONSOLE %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''
# Pause bounds returning-error models accept only native code1, as inherited.
def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 OUT.mkdir(parents=True,exist_ok=True);inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 modules=[('console','src/aspect/console_commands.asm','ASPECT_CONSOLE',UNITS),
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
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fm=CONSOLE.map','-fe=CONSOLE.EXE',str(OUT/'diagnostic.c'),str(ROOT/'src/aspect/literal.c'),*objects,str(OUT/'callbacks.obj')],cwd=OUT,check=True)
 sources += [ROOT/'src/aspect/literal.c',ROOT/'src/aspect/literal.h',ROOT/'standalone/build_aspect_string_commands.py',ROOT/'standalone/build_aspect_strings.py',ROOT/'standalone/build_aspect_operands.py',ROOT/'standalone/build_aspect_flow.py',ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
 report=dict(original_inputs=[],binary_sha256=sha((OUT/'CONSOLE.EXE').read_bytes()),units=units,sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},scope='Exact EXIT/MESSAGE/PAUSE, caret decoder, print loops, bounded pause operand and BIOS delay. Actual operand/string/frame/copy code. Byte renderer/cancellation/wait policies controlled; native BIOS delay calls run in DOS. No complete VM or arbitrary-input safety claim.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='units'},indent=2))


if __name__=='__main__':main()
