#!/usr/bin/env python3
"""Build native serial commands with actual string/format/timeout components."""
import hashlib,json,subprocess
from pathlib import Path
from build_aspect_console import (ASM as BASE_ASM,C as BASE_C,ENTRIES as CONSOLE_ENTRIES,UNITS as CONSOLE_UNITS,
 COMMAND_ENTRIES,COMMAND_UNITS,SERVICE_UNITS,EXPR_UNITS,LEGACY,STRING_UNITS,OPER_UNITS,FLOW_UNITS,
 FLOW_ENTRIES,OPER_ENTRIES,STRING_ENTRIES)
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-serial-commands'
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
ENTRIES=dict(transmit=0x5176,wait_for=0x5188,send_formatted=0x48cc,timeout_operand=0xe9f5,upper_byte=0x8252,native_clock=0x77fe,wait_status=0xda32)
UNITS=[(1,0x5176,0x517f,0x1200),(2,0x5188,0x52d0,0x1200),(3,0x48cc,0x4934,0x1200),
 (4,0xe9f5,0xea1d,55728),(5,0x8252,0x8268,0x1200),(6,0x77fe,0x780e,0x1200),(7,0xda32,0xda36,55728)]
ASM=BASE_ASM
old='operations: dw '+','.join('op_'+n for n in FLOW_ENTRIES)+','+','.join('operand_'+n for n in OPER_ENTRIES)+','+','.join('string_'+n for n in STRING_ENTRIES)+','+','.join('strcmd_'+n for n in COMMAND_ENTRIES)+','+','.join('console_'+n for n in CONSOLE_ENTRIES)+'\n'
assert ASM.count(old)==1
ASM=ASM.replace(old,old.rstrip()+','+','.join('serial_'+n for n in ENTRIES)+'\n')
ASM+='\nSEGMENT _TEXT\n'
for name in ENTRIES:
 ASM+='extern aspect_serial_'+name+'\nserial_'+name+':\n'
 if name in ('send_formatted','upper_byte'):ASM+=' push word [bp+6]\n'
 ASM+=' call aspect_serial_'+name+'\n'
 if name in ('send_formatted','upper_byte'):ASM+=' pop bx\n'
 ASM+=' ret\n'
for native,cname in [('aspect_serial_receive','serial_receive'),('aspect_serial_send_byte','serial_send'),('aspect_serial_pause_ticks','serial_pause'),('aspect_serial_character_delay','serial_delay')]:
 ASM+='extern _'+cname+'\nglobal '+native+'\n'+native+':\n push bp\n mov bp,sp\n push word [bp+4]\n call _'+cname+'\n pop bx\n pop bp\n ret 2\n'
ASM+='extern _serial_clock\nglobal aspect_serial_clock\naspect_serial_clock: jmp _serial_clock\nSEGMENT _DATA\n'
for name,cname,size in [('case_sensitive','serial_case_sensitive','dw 0'),('wait_result','serial_wait_result','dw 0'),('rx_count','serial_rx_count','dw 0'),('ctype','serial_ctype','times 256 db 0'),('pause_character','serial_pause_character','db 126'),('local_echo','serial_local_echo','dw 0'),('character_delay_value','serial_delay_value','dw 0')]:
 ASM+=f'global aspect_serial_{name},_{cname}\naspect_serial_{name}:\n_{cname}: {size}\n'
C=BASE_C.split('int main(void)')[0]
C+=r'''
extern unsigned serial_case_sensitive,serial_wait_result,serial_rx_count,serial_local_echo,serial_delay_value;
extern unsigned char serial_ctype[256],serial_pause_character;
static unsigned char rx[512],tx[512];static unsigned rx_length,rx_head,tx_count,pauses,delays,timeout_reads;
static unsigned long clocks[8];static unsigned clock_length,clock_head;static unsigned delay_last,pause_last;
unsigned serial_receive(unsigned flag){unsigned value;ck(flag==0&&rx_head<rx_length&&serial_rx_count);value=rx[rx_head++];serial_rx_count=rx_length-rx_head;return value;}
void serial_send(unsigned value){ck(value<=255&&tx_count<512);if(tx_count<512)tx[tx_count++]=(unsigned char)value;}
void serial_pause(unsigned ticks){++pauses;pause_last=ticks;}
void serial_delay(unsigned value){++delays;delay_last=value;}
unsigned long serial_clock(void){unsigned i=clock_head++;++timeout_reads;return clocks[i<clock_length?i:clock_length-1];}
static void serial_setup(unsigned length){unsigned i;console_setup(length);serial_case_sensitive=serial_wait_result=serial_rx_count=serial_local_echo=serial_delay_value=0;serial_pause_character='~';rx_length=rx_head=tx_count=pauses=delays=timeout_reads=0;clock_length=1;clock_head=0;clocks[0]=0;cancel_after=1;for(i=0;i<256;++i)serial_ctype[i]=(i>='a'&&i<='z')?2:0;}
static void queued(const unsigned char *s,unsigned n){memcpy(rx,s,n);rx_length=n;rx_head=0;serial_rx_count=n;}
static unsigned match_expected(const unsigned char *pattern,unsigned n,const unsigned char *s,unsigned length,unsigned sensitive,unsigned *consumed){unsigned p=0,i,c;
 for(i=0;i<length;++i){c=s[i];if(!sensitive&&c>='a'&&c<='z')c-=32;if(pattern[p]==c)++p;else p=pattern[0]==c?1:0;if(p==n){*consumed=i+1;return 1;}}
 *consumed=length;return n==0;}
static unsigned long signed_key(unsigned long v){return v^0x80000000UL;}
static unsigned expired(unsigned count,unsigned long start,unsigned long now){unsigned long end=start+(unsigned long)count*18UL;unsigned wrap=signed_key(end)>signed_key(0x1800b0UL);if(wrap)end-=0x1800b0UL;
 return wrap?(signed_key(now)<signed_key(start)&&signed_key(now)>=signed_key(end)):(signed_key(now)>=signed_key(end)||signed_key(now)<signed_key(start));}
int main(void){
 static const char *patterns[]={"","A","AB","AAB","ABAB","NO CARRIER","login:","^@","^M^J","^^^"};
 static const char *streams[]={"","A","aaab","ABABAB","AAAAB","xxNO CARRIERyy","Login:","abABab","xyz","^"};
 unsigned i,j,k,n,len,consumed,result,sensitive,echo,v,expected_delays;unsigned char decoded[128],expected_tx[128],expected_echo[128];unsigned expected_tx_count,expected_echo_count,expected_pauses;unsigned long start,now;FILE *f;
 for(i=0;i<sizeof(patterns)/sizeof(patterns[0]);++i)for(j=0;j<sizeof(streams)/sizeof(streams[0]);++j)for(sensitive=0;sensitive<2;++sensitive){
  serial_setup(4);serial_case_sensitive=sensitive;strcpy((char *)string_bank,patterns[i]);n=decode_expected(string_bank,decoded);if(!sensitive)for(k=0;k<n;++k)if(decoded[k]>='a'&&decoded[k]<='z')decoded[k]-=32;
  len=(unsigned)strlen(streams[j]);queued((const unsigned char *)streams[j],len);data[0]=100;data[1]=0;data[2]=1;data[3]=26;
  result=match_expected(decoded,n,rx,len,sensitive,&consumed);call(OP_wait_for,0,0);ck(serial_wait_result==result&&rx_head==consumed&&position()==4&&!aborted&&!abi_bad);ck(!timeout_reads);
 }
 for(i=0;i<256;++i){serial_setup(4);string_bank[0]=(unsigned char)(i==0?255:i);if(i=='^'){string_bank[0]='^';string_bank[1]='^';string_bank[2]='^';}queued((const unsigned char *)"",0);rx[0]=(unsigned char)(i==0?255:i);rx_length=serial_rx_count=1;data[0]=100;data[1]=0;data[2]=1;data[3]=26;call(OP_wait_for,0,0);ck(serial_wait_result==1&&rx_head==1);}
 for(i=0;i<3;++i){static const unsigned states[]={0,1,0xffff};serial_setup(0);serial_wait_result=states[i];call(OP_wait_status,0,0);ck(result_low==states[i]);}
 serial_setup(4);memset(rx,'X',83);rx_length=serial_rx_count=83;string_bank[0]='Y';data[0]=100;data[1]=0;data[2]=1;data[3]=26;call(OP_wait_for,0,0);ck(!serial_wait_result&&rx_head==82&&serial_rx_count==1&&polls==1);
 /* Native prefix-only fallback misses the overlapping AAB in AAAB. */
 serial_setup(4);memcpy(string_bank,"AAB",4);queued((const unsigned char *)"AAAB",4);data[0]=100;data[1]=0;data[2]=1;data[3]=26;call(OP_wait_for,0,0);ck(!serial_wait_result&&polls==1);
 for(i=0;i<12;++i){static const unsigned long starts[]={0,0,0,100,100,100,0x1800a6UL,0x1800a6UL,0x1800a6UL,0x18009eUL,0x18009eUL,0xfffffff0UL};static const unsigned long times[]={0,17,18,99,117,118,0x1800afUL,7,8,0x1800afUL,0,0xfffffff0UL};
  start=starts[i];now=times[i];serial_setup(6);string_bank[0]='X';data[0]=100;data[1]=0;data[2]=1;literal(3,1);clocks[0]=start;clocks[1]=now;clock_length=2;call(OP_wait_for,0,0);ck(!serial_wait_result&&timeout_reads==2&&polls==!expired(1,start,now));}
 /* Timeout token semantics: default30, explicitEND0, and bounded1..32767. */
 for(i=0;i<3;++i){serial_setup(1);data[0]=i==0?0:i==1?2:255;call(OP_timeout_operand,0,0);ck(result_low==30&&position()==1);}
 serial_setup(2);data[0]=1;data[1]=26;call(OP_timeout_operand,0,0);ck(result_low==0&&position()==2&&lookahead==0);
 for(i=0;i<3;++i){static const unsigned values[]={1,2,32767};serial_setup(4);data[0]=1;literal(1,values[i]);call(OP_timeout_operand,0,0);ck(result_low==values[i]&&position()==4&&lookahead==0);}
 for(i=0;i<2;++i){serial_setup(4);data[0]=1;literal(1,0);string_error_stops=i;call(OP_timeout_operand,0,0);ck(string_errors==1&&last_string_error==1&&aborted==i);if(!i)ck(result_low==0);}
 for(echo=0;echo<2;++echo){
  serial_setup(2);serial_local_echo=echo;serial_delay_value=7;strcpy((char *)string_bank,"AB^M^J^@C~D");n=decode_expected(string_bank,decoded);expected_tx_count=expected_echo_count=expected_pauses=expected_delays=0;
  for(i=0;i<n;++i){v=decoded[i];if(v=='~'){++expected_pauses;continue;}expected_tx[expected_tx_count++]=(unsigned char)(v==255?0:v);if(v!=255){++expected_delays;if(echo)expected_echo[expected_echo_count++]=(unsigned char)v;}}
  data[0]=100;data[1]=0;call(OP_transmit,0,0);ck(tx_count==expected_tx_count&&!memcmp(tx,expected_tx,tx_count));ck(emit_count==expected_echo_count&&!memcmp(emitted,expected_echo,emit_count));ck(pauses==expected_pauses&&pause_last==9&&delays==expected_delays&&delay_last==7&&position()==2);
 }
 serial_setup(2);serial_pause_character=255;memcpy(string_bank,"^@",3);data[0]=100;data[1]=0;call(OP_transmit,0,0);ck(pauses==1&&pause_last==9&&!tx_count&&!emit_count&&!delays);
 for(i=0;i<=80;++i){serial_setup(2);memset(string_bank,'X',i);data[0]=100;data[1]=0;call(OP_transmit,0,0);ck(tx_count==i&&delays==i&&!pauses&&!emit_count);for(j=0;j<i;++j)ck(tx[j]=='X');}
 f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_SERIAL_COMMANDS %lu checks %u failures\n",checks,failures);fclose(f);printf("ASPECT_SERIAL_COMMANDS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''

def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 OUT.mkdir(parents=True,exist_ok=True);inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 modules=[('serial-commands','src/aspect/serial_commands.asm','ASPECT_SERIAL_COMMANDS',UNITS),
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
 names=list(FLOW_ENTRIES)+list(OPER_ENTRIES)+list(STRING_ENTRIES)+list(COMMAND_ENTRIES)+list(CONSOLE_ENTRIES)+list(ENTRIES)
 (OUT/'diagnostic.c').write_text('\n'.join(f'#define OP_{n} {i}' for i,n in enumerate(names))+'\n'+C)
 subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fm=SERIAL.map','-fe=SERIAL.EXE',str(OUT/'diagnostic.c'),str(ROOT/'src/aspect/literal.c'),*objects,str(OUT/'callbacks.obj')],cwd=OUT,check=True)
 sources += [ROOT/'src/aspect/literal.c',ROOT/'src/aspect/literal.h',ROOT/'standalone/build_aspect_console.py',ROOT/'standalone/build_aspect_string_commands.py',ROOT/'standalone/build_aspect_strings.py',ROOT/'standalone/build_aspect_operands.py',ROOT/'standalone/build_aspect_flow.py',ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
 report=dict(original_inputs=[],native_serial_units=len(UNITS),native_serial_bytes=sum(b-a for _,a,b,_ in UNITS),binary_sha256=sha((OUT/'SERIAL.EXE').read_bytes()),units=units,sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sources},scope='Exact TRANSMIT/WAITFOR/formatted send/timeout operand/scalar upper/BIOS clock; actual caret/string/numeric/operand code. Device byte transmit/receive, delays, cancel and sampled clock are controlled component callbacks. No complete VM or modem/flowcontrol acceptance claim.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='units'},indent=2))


if __name__=='__main__':main()
