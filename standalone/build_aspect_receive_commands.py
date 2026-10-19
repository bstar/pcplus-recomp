#!/usr/bin/env python3
"""Build native ASPECT receive commands and explicit device-boundary diagnostic."""
import hashlib,json,re,subprocess
from pathlib import Path
from build_aspect_serial_commands import (ASM as BASE_ASM,C as BASE_C,ENTRIES as SERIAL_ENTRIES,UNITS as SERIAL_UNITS,
 CONSOLE_ENTRIES,CONSOLE_UNITS,COMMAND_ENTRIES,COMMAND_UNITS,SERVICE_UNITS,EXPR_UNITS,LEGACY,
 STRING_UNITS,OPER_UNITS,FLOW_UNITS,FLOW_ENTRIES,OPER_ENTRIES,STRING_ENTRIES)
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-receive-commands'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
ENTRIES=dict(comgetc=0x5431,comgetcd=0x5438,read_integer=0x5440,rget=0x50c7,wait_quiet=0x52d0,
 read_control=0x4c4f,native_seconds=0x3323,native_time=0x778c,native_delayed_read=0x5ca0,available_status=0xda08,forever=0xda10)
UNITS=[(1,0x5431,0x5458,0x1200),(2,0x50c7,0x5157,0x1200),(3,0x52d0,0x5345,0x1200),
 (4,0x4c4f,0x4c74,0x1200),(5,0x3323,0x332e,0x1200),(6,0x778c,0x77ad,0x1200),
 (7,0x5ca0,0x5cce,0x1200),(8,0xda08,0xda0c,55728),(9,0xda10,0xda14,55728)]
ASM=BASE_ASM
old='operations: dw '+','.join('op_'+n for n in FLOW_ENTRIES)+','+','.join('operand_'+n for n in OPER_ENTRIES)+','+','.join('string_'+n for n in STRING_ENTRIES)+','+','.join('strcmd_'+n for n in COMMAND_ENTRIES)+','+','.join('console_'+n for n in CONSOLE_ENTRIES)+','+','.join('serial_'+n for n in SERIAL_ENTRIES)+'\n'
assert ASM.count(old)==1
ASM=ASM.replace(old,old.rstrip()+','+','.join('receive_'+n for n in ENTRIES)+'\n')
ASM+='\nSEGMENT _TEXT\n'
for name in ENTRIES:
 ASM+='extern aspect_receive_'+name+'\nreceive_'+name+':\n'
 if name in ('read_integer','read_control','native_time'):ASM+=' push word [bp+6]\n'
 ASM+=' call aspect_receive_'+name+'\n ret\n'
# The selected integer-builtin dispatcher remains a fixture boundary, while
# COMDATA/FOREVER execute their actual recovered native bodies.
old='aspect_operand_builtin_integer:\n push bp'
assert ASM.count(old)==1
ASM=ASM.replace(old,r'''aspect_operand_builtin_integer:
 mov bx,sp
 cmp word [bx+2],20
 jne .forever
 call aspect_receive_available_status
 ret 2
.forever:
 cmp word [bx+2],22
 jne .other
 call aspect_receive_forever
 ret 2
.other:
 push bp''')
ASM+=r'''
extern _receive_character,_receive_raw,_receive_seconds
global aspect_receive_character,aspect_receive_raw_read,aspect_receive_seconds
aspect_receive_character:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call _receive_character
 add sp,4
 pop bp
 ret 4
aspect_receive_raw_read: jmp _receive_raw
aspect_receive_seconds: jmp _receive_seconds
SEGMENT _DATA
global aspect_receive_display,_receive_display,aspect_receive_suppress_echo,_receive_suppress_echo
aspect_receive_display:
_receive_display: dw 0
aspect_receive_suppress_echo:
_receive_suppress_echo: dw 0
global aspect_receive_clock_sample,_receive_clock_sample
aspect_receive_clock_sample:
_receive_clock_sample: times 4 dw 0
'''
C=BASE_C.split('int main(void)')[0]
# Omit unused test oracles inherited with the shared callback fixture.
for helper in ('decode_expected','match_expected','signed_key','expired'):
 match=re.search(r'static unsigned(?: long)? '+helper+r'\(',C)
 assert match,helper
 opening=C.index('{',match.start());depth=1;closing=opening+1
 while depth:
  depth+=(C[closing]=='{')-(C[closing]=='}');closing+=1
 C=C[:match.start()]+C[closing:]
C='void receive_wait(void);\n'+C.replace('void console_wait(void){++waits;}','void console_wait(void){++waits;receive_wait();}')
C+=r'''
extern unsigned receive_display,receive_suppress_echo,receive_clock_sample[4];
static unsigned device_echo,device_delay,device_calls,raw_calls,seconds_calls,seconds_tail;
static unsigned seconds_values[32],seconds_length,seconds_head,arrival_count,arrival_index,arrival_lengths[32];
static unsigned char arrival_bytes[32][4];
unsigned receive_raw(void){++raw_calls;if(rx_head>=rx_length)return 0xffff;serial_rx_count=rx_length-rx_head-1;return rx[rx_head++];}
unsigned receive_character(unsigned echo,unsigned delayed){device_echo=echo;device_delay=delayed;++device_calls;return receive_raw();}
unsigned receive_seconds(void){unsigned i=seconds_head++;++seconds_calls;if(seconds_length)return seconds_values[i<seconds_length?i:seconds_length-1];if(serial_rx_count)return 0;return (seconds_tail++/2)%60;}
void receive_wait(void){if(arrival_index<arrival_count){queued(arrival_bytes[arrival_index],arrival_lengths[arrival_index]);++arrival_index;}}
static void receive_setup(unsigned length){serial_setup(length);receive_display=receive_suppress_echo=0;device_echo=device_delay=device_calls=raw_calls=seconds_calls=seconds_tail=seconds_length=seconds_head=arrival_count=arrival_index=0;cancel_after=0;memset(receive_clock_sample,0,8);}
static void rget_wire(unsigned max,unsigned timeout){data[0]=100;data[1]=0;data[2]=1;literal(3,max);data[6]=1;literal(7,timeout);}
static void quiet_wire(unsigned quiet,unsigned timeout){data[0]=1;literal(1,quiet);data[4]=1;if(timeout)literal(5,timeout);else data[5]=26;}
int main(void){
 unsigned i,j,k,value,mode,n,len,limit,timeout,expected;unsigned time_values[5];unsigned char __far *far_block;FILE *f;
 for(mode=0;mode<2;++mode)for(i=0;i<2;++i)for(j=0;j<2;++j)for(k=0;k<4;++k){
  static const unsigned values[]={0,13,255,0xffff};value=values[k];receive_setup(2);data[0]=141;data[1]=0;receive_display=i;receive_suppress_echo=j;if(value!=0xffff){rx[0]=(unsigned char)value;rx_length=serial_rx_count=1;}
  call(mode?OP_comgetcd:OP_comgetc,0,0);ck(bank_b[0]==value&&device_calls==1&&device_echo==(i&&!j)&&device_delay==mode&&position()==2&&!aborted&&!abi_bad);
 }
 for(i=0;i<256;++i){receive_setup(2);data[0]=141;data[1]=i;rx[0]=(unsigned char)(255-i);rx_length=serial_rx_count=1;call(OP_comgetc,0,0);ck(bank_b[i]==255-i);}
 for(limit=1;limit<=80;++limit)for(mode=0;mode<3;++mode){
  receive_setup(10);rget_wire(limit,30);len=limit+(mode==0?1:0);memset(rx,'A',len);if(mode==1)rx[limit/2]=13;if(mode==2)rx[0]=13;rx_length=serial_rx_count=len;
  memset(string_bank,0x5a,82);call(OP_rget,0,0);n=mode==0?limit:mode==1?limit/2:0;ck(comparison_result==0&&rx_head==n+(mode?1:0));for(i=0;i<n;++i)ck(string_bank[i]=='A');ck(string_bank[n]==0&&string_bank[n+1]==0x5a&&position()==10&&!pending_near);
 }
 /* zero requested length still accepts A before CR: retained native quirk. */
 receive_setup(10);rget_wire(0,30);queued((const unsigned char *)"A\r",2);call(OP_rget,0,0);ck(string_bank[0]=='A'&&string_bank[1]==0&&rx_head==2&&!comparison_result);
 receive_setup(10);rget_wire(80,0);queued((const unsigned char *)"A",1);call(OP_rget,0,0);ck(comparison_result==1&&!rx_head&&!polls&&string_bank[0]==0);
 receive_setup(10);rget_wire(80,1);seconds_values[0]=59;seconds_values[1]=0;seconds_values[2]=0;seconds_length=3;call(OP_rget,0,0);ck(comparison_result==1&&seconds_calls==3&&polls==1);
 receive_setup(10);rget_wire(80,2);seconds_values[0]=0;seconds_values[1]=10;seconds_values[2]=10;seconds_values[3]=20;seconds_values[4]=20;seconds_length=5;call(OP_rget,0,0);ck(comparison_result==1&&seconds_calls==5&&polls==2);
 receive_setup(10);rget_wire(80,30);cancel_after=1;queued((const unsigned char *)"A",1);call(OP_rget,0,0);ck(!comparison_result&&!rx_head&&string_bank[0]==0);
 receive_setup(3);data[0]=100;data[1]=0;data[2]=0;queued((const unsigned char *)"OK\r",3);call(OP_rget,0,0);ck(!strcmp((char *)string_bank,"OK")&&!comparison_result&&position()==3);
 /* FOREVER integer builtin22 is native1, not a timeout normalization. */
 receive_setup(9);rget_wire(80,1);data[7]=111;data[8]=22;seconds_values[0]=0;seconds_values[1]=1;seconds_values[2]=1;seconds_length=3;call(OP_rget,0,0);ck(comparison_result==1&&seconds_calls==3&&position()==9);
 for(i=0;i<5;++i)for(j=0;j<5;++j){static const unsigned qu[]={0,1,2,15,31};static const unsigned overall[]={0,1,2,30,31};n=qu[i];timeout=overall[j];receive_setup(timeout?8:6);quiet_wire(n,timeout);call(OP_wait_quiet,0,0);expected=n==0?0:timeout&&timeout<n?1:0;ck(comparison_result==expected&&waits==(n==0?0:timeout&&timeout<n?timeout:n)&&!rx_head);}
 receive_setup(1);data[0]=0;call(OP_wait_quiet,0,0);ck(!comparison_result&&waits==15&&position()==1);
 receive_setup(8);quiet_wire(2,8);arrival_count=2;arrival_lengths[0]=1;arrival_lengths[1]=2;arrival_bytes[0][0]='A';arrival_bytes[1][0]='B';arrival_bytes[1][1]='C';call(OP_wait_quiet,0,0);ck(!comparison_result&&waits==4&&rx_head==2&&arrival_index==2);
 receive_setup(8);quiet_wire(2,8);cancel_after=1;call(OP_wait_quiet,0,0);ck(comparison_result==1&&!waits&&!rx_head);
 far_block=_fmalloc(81);ck(far_block!=0);if(!far_block)return 2;string_globals[0]=(unsigned long)far_block;receive_setup(10);rget_wire(80,30);data[0]=140;_fmemset(far_block,0x5a,81);queued((const unsigned char *)"FAR\r",4);call(OP_rget,0,0);ck(!_fstrcmp(far_block,"FAR")&&!pending_near&&far_block[4]==0x5a);_ffree(far_block);
 for(i=0;i<4;++i){static const unsigned states[]={0,1,4096,0xffff};receive_setup(0);serial_rx_count=states[i];call(OP_available_status,0,0);ck(result_low==states[i]);call(OP_forever,0,0);ck(result_low==1);}
 receive_setup(0);rx[0]='Q';rx_length=serial_rx_count=1;call(OP_native_delayed_read,0,0);ck(result_low=='Q'&&raw_calls==1&&!serial_rx_count);
 receive_setup(0);call(OP_native_delayed_read,0,0);ck(result_low==0xffff&&!raw_calls);
 memset(time_values,0xa5,sizeof(time_values));receive_setup(0);call(OP_native_time,(unsigned)time_values,0);ck(time_values[0]<100&&time_values[1]<24&&time_values[2]<60&&time_values[3]<60&&time_values[4]==0xa5a5);value=time_values[3];call(OP_native_seconds,0,0);ck(result_low<60&&((result_low+60-value)%60)<=1);
 f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_RECEIVE_COMMANDS %lu checks %u failures\n",checks,failures);fclose(f);printf("ASPECT_RECEIVE_COMMANDS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''

def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 OUT.mkdir(parents=True,exist_ok=True);inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 modules=[('receive-commands','src/aspect/receive_commands.asm','ASPECT_RECEIVE_COMMANDS',UNITS),
  ('serial-commands','src/aspect/serial_commands.asm','ASPECT_SERIAL_COMMANDS',SERIAL_UNITS),
  ('console','src/aspect/console_commands.asm','ASPECT_CONSOLE',CONSOLE_UNITS),
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
 names=list(FLOW_ENTRIES)+list(OPER_ENTRIES)+list(STRING_ENTRIES)+list(COMMAND_ENTRIES)+list(CONSOLE_ENTRIES)+list(SERIAL_ENTRIES)+list(ENTRIES)
 (OUT/'diagnostic.c').write_text('\n'.join(f'#define OP_{n} {i}' for i,n in enumerate(names) if n not in list(ENTRIES) or i>=len(names)-len(ENTRIES))+'\n'+C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fm=RECEIVE.map','-fe=RECEIVE.EXE',str(OUT/'diagnostic.c'),str(ROOT/'src/aspect/literal.c'),*objects,str(OUT/'callbacks.obj')],cwd=OUT,check=True)
 sources += [ROOT/'src/aspect/literal.c',ROOT/'src/aspect/literal.h',ROOT/'standalone/build_aspect_serial_commands.py',ROOT/'standalone/build_aspect_console.py',ROOT/'standalone/build_aspect_string_commands.py',ROOT/'standalone/build_aspect_strings.py',ROOT/'standalone/build_aspect_operands.py',ROOT/'standalone/build_aspect_flow.py',ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
 report=dict(original_inputs=[],native_receive_units=len(UNITS),native_receive_bytes=sum(b-a for _,a,b,_ in UNITS),binary_sha256=sha((OUT/'RECEIVE.EXE').read_bytes()),units=units,sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},scope='Exact COMGETC/COMGETCD/RGET/WAITQUIET/read selector/native delayed read/DOS time and COMDATA20/FOREVER22. Actual operand/string/frame/copy/selected builtin bodies. Device4C74,rawread,seconds,wait,cancel callbacks controlled except direct native time/delay tests. No complete application or liveUART acceptance claim.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='units'},indent=2))


if __name__=='__main__':main()
