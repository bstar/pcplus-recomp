#!/usr/bin/env python3
"""Source-only native WHEN CPU/8086 DOS checks, optional private byte comparison."""
import argparse,json,os,re,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from build_aspect_when import ROOT,OUT,SOURCE,UNITS,ENTRIES,HELPERS,COMPOSITION,sha
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
DATA=0x40000
class Machine:
 def __init__(self):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  for n,a,b,_ in UNITS:self.u.mem_write(0x10000+a,(OUT/f'unit{n}.bin').read_bytes())
  for name,_,_,a,b in HELPERS:self.u.mem_write(0x10000+a,(OUT/(name+'.bin')).read_bytes())
  for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_SS,0x4000),(UC_X86_REG_ES,0x4000)]:self.u.reg_write(r,v)
  self.slot=0;self.strings=[];self.tokens=[];self.target=0;self.actions=[];self.carrier=1;self.ready=0;self.key=0;self.confirm=0;self.instructions=set();self.polls=0;self.dispatched=[];self.aborts=0
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_INTR,lambda *a:(_ for _ in ()).throw(AssertionError('Unexpected interrupt')))
 def put(self,a,v):self.u.mem_write(DATA+a,struct.pack('<H',v))
 def get(self,a):return struct.unpack('<H',self.u.mem_read(DATA+a,2))[0]
 def string(self,a):return bytes(self.u.mem_read(DATA+a,81)).split(b'\0')[0]
 def hook(self,u,at,size,_):
  if at==0x1f000:u.emu_stop();return
  self.instructions.add(at)
  callbacks={0xe0e4,0xdd68,0xdf04,0x4cb4,0xe176,0x8252,0x48cc,0xcd8f,0xcd9b,0xdde,0xaa5c,0x651a,0x64fe,0x4e6b,0x4ebc,0x1604}
  ip=at-0x10000
  if ip not in callbacks:
   assert any(a<=ip<b for _,a,b,_ in UNITS) or any(a<=ip<b for _,_,_,a,b in HELPERS),hex(ip)
   return
  sp=u.reg_read(UC_X86_REG_SP);ret=self.get(sp);arg=lambda n:self.get(sp+2+2*n);v=0;clean=0
  if ip==0xe0e4:v=int(self.slot!=3)
  elif ip==0xdd68:assert arg(0)==2 and arg(1)==0 and self.slot in range(3);v=self.slot;clean=4
  elif ip==0xdf04:
   assert arg(0)==40;v=0x5000+(2-len(self.strings))*128;s=self.strings.pop(0);assert len(s)<=80;u.mem_write(DATA+v,s+b'\0'*(81-len(s)))
  elif ip==0x4cb4:v=self.tokens.pop(0)
  elif ip==0xe176:v=self.target&65535;u.reg_write(UC_X86_REG_DX,self.target>>16)
  elif ip==0x8252:v=arg(0);v=v-32 if 97<=v<=122 else v
  elif ip==0x48cc:self.actions.append(dict(kind='transmit-request',string_hex=self.string(arg(0)).hex()))
  elif ip==0xcd8f:self.actions.append(dict(kind='call-request',target=arg(0)|(arg(1)<<16)));clean=4
  elif ip==0xcd9b:self.actions.append(dict(kind='frame-request'))
  elif ip==0xdde:self.polls+=1
  elif ip==0xaa5c:v=self.carrier
  elif ip==0x651a:v=self.ready
  elif ip==0x64fe:v=self.key
  elif ip==0x4e6b:v=self.confirm
  elif ip==0x4ebc:self.aborts+=1
  elif ip==0x1604:self.dispatched.append(self.get(0xcffa))
  u.reg_write(UC_X86_REG_AX,v);u.reg_write(UC_X86_REG_SP,sp+2+clean);u.reg_write(UC_X86_REG_IP,ret)
 def call(self,name,args=()):
  u=self.u;sp=0xd000;u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_BP,0xc000);u.reg_write(UC_X86_REG_SI,0x1234);u.reg_write(UC_X86_REG_DI,0x5678);u.mem_write(DATA+sp,struct.pack('<'+'H'*(1+len(args)),0xf000,*args));u.emu_start(0x10000+ENTRIES[name],0x20000,count=30000)
  assert u.reg_read(UC_X86_REG_IP)==0xf000 and u.reg_read(UC_X86_REG_SP)==sp+2+2*len(args)
  if name not in ('slot','service'):assert u.reg_read(UC_X86_REG_BP)==0xc000 and u.reg_read(UC_X86_REG_SI)==0x1234 and u.reg_read(UC_X86_REG_DI)==0x5678
  return u.reg_read(UC_X86_REG_AX)
 def arm(self,slot,pattern=b'A',action=b'X',case=False,frame=False):
  self.slot=slot;self.put(0xe398,int(case));self.strings=([pattern] if slot<3 else [])+([action] if isinstance(action,bytes) else []);self.tokens=[50] if isinstance(action,bytes) else [7,200 if frame else 199];self.target=action if isinstance(action,int) else 0;self.call('register');assert not self.strings and not self.tokens
 def feed(self,b):
  for v in b:self.call('monitor',[v])
 def cancel(self,s):self.slot=s;self.call('cancel')
 def cursor(self,s):return self.get(0xe1f4+86*s)
 def pattern(self,s):return self.string(0xe1a1+86*s)
def cpu():
 cases=[];addresses=set()
 def check(name,fn):
  m=Machine();details=fn(m);addresses.update(m.instructions);cases.append(dict(name=name,passed=True,details=details,actions=m.actions))
 def register(m):
  m.arm(0,b'aBc',b'xYz');assert m.pattern(0)==b'ABC' and m.get(0xe2f8)==1;m.feed(b'abcABC');assert m.actions==[dict(kind='transmit-request',string_hex='78597a')]*2
  return {'rearmed_cursor':m.cursor(0)}
 check('casefold-register-repeated-transmit',register)
 def priority(m):
  for i in range(3):m.arm(i,b'OK',bytes([65+i]))
  m.feed(b'OKOK');assert [a['string_hex'] for a in m.actions]==['41','42','43']*2 and m.get(0xe2f8)==3
 check('three-slots-priority-repeat',priority)
 tests=[('fallback',b'AB',b'AAB',1),('no-KMP',b'ABAAB',b'ABABAAB',0),('nonoverlap',b'AAA',b'AAAAA',1),('sensitive-hit',b'AbC',b'AbC',1),('sensitive-miss',b'AbC',b'abc',0),('high-hit',b'\xff',b'\xff',1),('high-miss',b'\x80',b'\xa0',0),('caret',b'^M^@^^',b'\r\xff\x1e',1),('empty',b'',b'A\0',1),('length40',b'A'*40,b'A'*40,1)]
 for name,p,b,count in tests:
  def run(m,p=p,b=b,count=count,name=name):m.arm(0,p,case=name.startswith('sensitive'));m.feed(b);assert len(m.actions)==count;return dict(expected_events=count)
  check(name,run)
 def trunc(m):
  m.arm(0,b'A'*80,b'R'*80);assert m.pattern(0)==b'A'*40;m.feed(b'A'*40);assert m.actions==[dict(kind='transmit-request',string_hex=(b'R'*40).hex())]
 check('eighty-copy-truncated40',trunc)
 def cancel(m):
  m.arm(0,b'AB');m.feed(b'A');m.cancel(0);m.cancel(0);assert m.get(0xe2f8)==0 and m.cursor(0)==0;m.feed(b'B');assert not m.actions;m.arm(0,b'AB');m.feed(b'A');m.arm(0,b'AB');assert m.get(0xe2f8)==1;m.feed(b'B');assert not m.actions;m.feed(b'AB');assert len(m.actions)==1
 check('cancel-rearm',cancel)
 def toggle(m):
  m.arm(0,b'abc',case=True);m.put(0xe398,0);m.feed(b'abc');assert not m.actions;m.arm(0,b'abc');assert m.string(0x5000)==b'ABC';m.put(0xe398,1);m.feed(b'abcABC');assert len(m.actions)==1
 check('mode-toggle-buffer-alias',toggle)
 for framed in [False,True]:
  def call(m,framed=framed):
   m.arm(1,b'GO',0x12345678,frame=framed);m.feed(b'GO');assert m.actions==[dict(kind='call-request',target=0x12345678)]+([dict(kind='frame-request')] if framed else []);assert m.get(0xe382)==1
  check('framed-call-request' if framed else 'plain-call-request',call)
 def disconnect(m):
  m.arm(3,action=b'BYE');assert m.get(0xe2fa)==1 and m.get(0xe2f8)==0;m.carrier=1;assert m.call('service')==0 and not m.actions;m.carrier=0;assert m.call('service')==0;m.call('service');assert len(m.actions)==1 and m.get(0xe2fa)==0;m.arm(3);m.cancel(3);assert m.get(0xe2fa)==0
 check('disconnect-native-service-one-shot-cancel',disconnect)
 for name,ready,key,confirm,disabled,expected in [('no-key',0,65,0,0,0),('disabled',1,65,0,1,0),('ordinary',1,65,0,0,0),('escape-denied',1,27,0,0,0),('escape-confirmed',1,27,1,0,1)]:
  def keycase(m,ready=ready,key=key,confirm=confirm,disabled=disabled,expected=expected):
   m.ready=ready;m.key=key;m.confirm=confirm;m.put(0xe380,disabled);assert m.call('service')==expected and m.polls==1;assert m.aborts==expected
   assert m.dispatched==([65] if ready and not disabled and key!=27 else []);assert m.get(0x397a)==65535
  check('service-'+name,keycase)
 return cases,sorted(addresses)

class Composed(Machine):
 def __init__(self,wire,rx):
  super().__init__();self.wire=wire;self.rx=list(rx);self.released=False;self.tx=[];self.display=[];self.trace=[];self.ins=set();self.steps=0;self.stop=0x1f000
  for name,relative,macro,n,a,b in COMPOSITION:self.u.mem_write(0x10000+a,(OUT/(name+'.bin')).read_bytes())
  self.uc=self.u;self.u.mem_write(DATA+0x3000,wire);self.u.mem_write(DATA+0xd00a,bytes(range(256)))
  self.u.mem_write(DATA+0x7748,bytes.fromhex('b3350bc747291dfb1f7f055917'))
  self.u.mem_write(DATA+0x7caf,bytes(2 if 97<=i<=122 else 0 for i in range(256)))
  for opcode,handler in {0xcf:0xd27d,0xc9:0x5431,0x94:0xd317,0x95:0xd339,0xd2:0xd1f2,0xd6:0xe8fc,0xd4:0x5188,0xbf:0x5176}.items():self.put(0x4b08+opcode*2,handler)
  self.put(0xe37e,1);self.put(0xe13c,0x7000);self.put(0xe13a,0x6800);self.put(0x4b02,0x2000);self.seek(1)
 def seek(self,pos):
  assert 0<=pos<=len(self.wire),pos
  self.put(0x2000,0x3000+pos);self.put(0x2002,len(self.wire)-pos)
 def event(self,kind,**kw):self.trace.append(dict(kind=kind,pos=self.get(0x2000)-0x3000,gate=self.get(0xe382),depth=self.get(0xe37a),frame=self.get(0xe13a),stack=self.get(0xe13c),remaining=len(self.rx),**kw))
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  self.ins.add(at);self.steps+=1
  if self.steps>250000:raise AssertionError('Replay step bound')
  ip=at-0x10000
  if ip in (0x5188,0x5431) and not self.released:self.released=True;self.put(0x8e20,len(self.rx));self.event('release-rx')
  if ip in (0xd27d,0xd2d6,0xd2f9,0xd317,0xd339,0x53c2,0x5188,0x5431):self.event('native-entry',ip=hex(ip))
  sp=u.reg_read(UC_X86_REG_SP);ret=self.get(sp);args=lambda n:self.get(sp+2+2*n)
  result=0;cleanup=0
  if ip==0xc1d7:self.event('startup-model')
  elif ip==0x9048:result=0
  elif ip==0xc21f:self.seek(1);self.put(0xe382,1);result=1;cleanup=4;self.event('open-model')
  elif ip in (0xc2eb,0x8318,0xc273):self.event('cleanup-model',ip=hex(ip))
  elif ip==0x4cb4:
   pos=self.get(0x2000)-0x3000;assert pos<len(self.wire);result=self.wire[pos];self.seek(pos+1)
  elif ip==0x8ed8:result=self.get(0x2000)-0x3000;u.reg_write(UC_X86_REG_DX,0)
  elif ip==0x853a:
   offset=args(1)|(args(2)<<16);offset=offset if offset<0x80000000 else offset-0x100000000
   pos=offset+(self.get(0x2000)-0x3000 if args(3)==1 else 0);self.seek(pos);self.event('fseek-model',target=pos)
  elif ip==0x845a:
   dest,size,count,file=args(0),args(1),args(2),args(3);assert file==0x2000
   pos=self.get(file)-0x3000;n=min(size*count,len(self.wire)-pos);u.mem_write(DATA+dest,self.wire[pos:pos+n]);self.seek(pos+n);result=n//size
  elif ip in (0xaa65,0x5ca0):
   result=self.rx.pop(0) if self.rx else 65535;self.put(0x8e20,len(self.rx));self.event('raw-read',value=result)
  elif ip==0x0610:self.display.append(args(0));self.event('display-boundary',value=args(0))
  elif ip==0xab0b:self.tx.append(args(0)&255);cleanup=2;self.event('tx-boundary',value=args(0))
  elif ip==0x6b72:assert args(0)==0;cleanup=2
  elif ip in (0x0dde,0x651a):result=0
  elif ip==0xaa5c:result=1
  elif ip==0x77fe:result=0;u.reg_write(UC_X86_REG_DX,0)
  else:
   targets={0xc357:0xd1f2,0xc543:0xe8fc,0xc84f:0xd317,0xc8a3:0xd339,0xcab3:0xd27d,0xcd83:0xe9f5,0xcd8f:0xd2d6,0xcd9b:0xd2f9,0xce13:0xde4d,0xce1f:0xdf04}
   if ip in targets:u.reg_write(UC_X86_REG_IP,targets[ip]);return
   assert any(a<=ip<b for _,a,b,_ in UNITS) or any(a<=ip<b for _,_,_,a,b in HELPERS) or any(a<=ip<b for _,_,_,_,a,b in COMPOSITION),('Unexpected execution',hex(ip))
   return
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)
 def run(self):
  self.u.reg_write(UC_X86_REG_SP,0xd000);self.u.reg_write(UC_X86_REG_BP,0xc000);self.u.mem_write(DATA+0xd000,struct.pack('<3H',0xf000,1,0x5000));self.u.emu_start(0x14b1f,0x20000,count=300000);assert self.u.reg_read(UC_X86_REG_IP)==0xf000

def composed():
 fixture=ROOT/'standalone/fixtures/aspect_when_vectors.json';corpus=json.loads(fixture.read_text());results=[]
 for name,expected in corpus['flow_cases'].items():
  vector=next(v for v in corpus['vectors'] if v['name']==name);wire=bytes.fromhex(vector['asx_hex']);assert sha(wire)==vector['asx_sha256'];assert sha(vector['source'].encode(vector['source_encoding']))==vector['source_sha256']
  m=Composed(wire,bytes.fromhex(expected['rx_hex']));m.run();assert bytes(m.tx).hex()==expected['tx_hex'] and bytes(m.display).hex()==expected['display_hex']
  assert m.get(0xe37a)==0 and m.get(0xe13c)==0x7000 and m.get(0xe13a)==0x6800 and m.get(0xe382)==0
  assert all(t['remaining']==0 for t in m.trace if t['kind']=='tx-boundary')
  if name=='FLOWGC':assert m.get(0xd482)==65
  results.append(dict(name=name,passed=True,trace=m.trace,instruction_addresses=[hex(a) for a in sorted(m.ins)]))
 return results

DOS_ASM=r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _run_when
extern _abi_bad,_saved_sp
_run_when:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov [_saved_sp],sp
 mov si,0x1234
 mov di,0x5678
 mov bx,[bp+4]
 shl bx,1
 call word [cs:operations+bx]
 cmp sp,[_saved_sp]
 jne bad
 cmp si,0x1234
 jne bad
 cmp di,0x5678
 je done
bad: inc word [_abi_bad]
 mov sp,[_saved_sp]
done:
 pop es
 pop di
 pop si
 pop bp
 ret
operations: dw reg,cancel,monitor,trigger,service,slot
extern aspect_when_register,aspect_when_cancel,aspect_when_monitor,aspect_when_trigger,aspect_when_service,aspect_when_slot
reg: call aspect_when_register
 ret
cancel: call aspect_when_cancel
 ret
monitor: push word [bp+6]
 call aspect_when_monitor
 ret
trigger: push word [bp+6]
 call aspect_when_trigger
 ret
service: call aspect_when_service
 ret
slot: call aspect_when_slot
 ret
extern _model_string,_model_option,_model_bounded,_model_token,_model_target,_model_upper,_model_send,_model_call,_model_frame
extern _model_poll,_model_carrier,_model_ready,_model_read_key,_model_confirm,_model_abort,_model_dispatch_key
global aspect_string_read,aspect_string_option_flag,aspect_string_bounded_integer,aspect_dispatch_read,aspect_flow_read_dword
aspect_string_read: jmp _model_string
aspect_string_option_flag: jmp _model_option
aspect_string_bounded_integer:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call _model_bounded
 add sp,4
 pop bp
 ret 4
aspect_dispatch_read: jmp _model_token
aspect_flow_read_dword: jmp _model_target
global aspect_serial_upper_byte,aspect_serial_send_formatted,aspect_flow_call,aspect_flow_push_frame
aspect_serial_upper_byte: jmp _model_upper
aspect_serial_send_formatted: jmp _model_send
aspect_flow_call:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call _model_call
 add sp,4
 pop bp
 ret 4
aspect_flow_push_frame: jmp _model_frame
global aspect_when_host_poll,aspect_when_carrier,aspect_when_key_ready,aspect_when_read_key,aspect_when_confirm_abort,aspect_when_abort,aspect_when_dispatch_key
aspect_when_host_poll: jmp _model_poll
aspect_when_carrier: jmp _model_carrier
aspect_when_key_ready: jmp _model_ready
aspect_when_read_key: jmp _model_read_key
aspect_when_confirm_abort: jmp _model_confirm
aspect_when_abort: jmp _model_abort
aspect_when_dispatch_key: jmp _model_dispatch_key
global aspect_string_upper,aspect_console_decode
extern directory_dial_upper_original
aspect_string_upper: jmp directory_dial_upper_original
aspect_console_decode:
incbin "decode.bin"
SEGMENT _DATA public class=DATA use16
'''
DOS_C=r'''
#include <stdio.h>
#include <string.h>
unsigned abi_bad,saved_sp,checks,failed;
extern unsigned active_count,disconnect_armed,case_sensitive,wait_gate,pending_key,keyboard_disabled,last_key;
extern unsigned char records[344];
static unsigned selected,head,token_head,framed,is_call,send_count,frame_count,call_count,polls,carrier=1,ready,key,confirm,aborts,dispatches;
static unsigned long target=0x12345678UL,called;
static char strings[2][81],sent[16][81];
unsigned run_when(unsigned,unsigned);
#define CK(x) do {++checks;if(!(x)){++failed;printf("FAIL line%u\n",__LINE__);}} while(0)
char *model_string(void){CK(head<2);return strings[head++];}
unsigned model_option(void){return selected!=3;}
unsigned model_bounded(unsigned hi,unsigned lo){CK(hi==2&&lo==0&&selected<3);return selected;}
unsigned model_token(void){if(!is_call)return 50;return token_head++?framed?200:199:7;}
unsigned long model_target(void){return target;}
unsigned model_upper(unsigned v){return v>=97&&v<=122?v-32:v;}
void model_send(char *s){CK(send_count<16);strcpy(sent[send_count++],s);}
void model_call(unsigned long address){++call_count;called=address;}
void model_frame(void){++frame_count;}
void model_poll(void){++polls;}
unsigned model_carrier(void){return carrier;}
unsigned model_ready(void){return ready;}
unsigned model_read_key(void){return key;}
unsigned model_confirm(void){return confirm;}
void model_abort(void){++aborts;}
void model_dispatch_key(void){++dispatches;}
static unsigned cursor(unsigned s){return *(unsigned *)(records+s*86+84);}
static void reset(void){memset(records,0,sizeof(records));active_count=disconnect_armed=case_sensitive=wait_gate=send_count=call_count=frame_count=abi_bad=polls=ready=keyboard_disabled=aborts=dispatches=0;carrier=1;}
static void arm(unsigned s,const char *p,const char *a,unsigned call,unsigned frame){selected=s;head=token_head=0;is_call=call;framed=frame;memset(strings,0,sizeof(strings));strcpy(strings[0],s==3&&!call?a:p);strcpy(strings[1],a);run_when(0,0);CK(!abi_bad);}
static void feed(const unsigned char *s,unsigned n){while(n--)run_when(2,*s++);CK(!abi_bad);}
int main(void){
 unsigned i,j,n,s;
 reset();arm(0,"aBc","xYz",0,0);CK(!strcmp((char *)records+1,"ABC")&&active_count==1);feed((unsigned char *)"abcABC",6);CK(send_count==2&&!strcmp(sent[0],"xYz")&&cursor(0)==(unsigned)(records+1));
 reset();for(i=0;i<3;++i){char a[2];a[0]='A'+i;a[1]=0;arm(i,"OK",a,0,0);}feed((unsigned char *)"OKOK",4);CK(send_count==6&&active_count==3);for(i=0;i<6;++i)CK(sent[i][0]=='A'+i%3);
 reset();arm(0,"AB","X",0,0);feed((unsigned char *)"AAB",3);CK(send_count==1);
 reset();arm(0,"ABAAB","X",0,0);feed((unsigned char *)"ABABAAB",7);CK(!send_count);
 reset();arm(0,"AAA","X",0,0);feed((unsigned char *)"AAAAA",5);CK(send_count==1);
 reset();case_sensitive=1;arm(0,"AbC","X",0,0);feed((unsigned char *)"abcAbC",6);CK(send_count==1);
 reset();arm(0,"^M^@^^","X",0,0);{unsigned char b[3]={13,255,30};feed(b,3);}CK(send_count==1);
 reset();arm(0,"","X",0,0);{unsigned char b[2]={'A',0};feed(b,2);}CK(send_count==1);
 for(s=0;s<3;++s)for(n=1;n<=80;++n){char p[81],a[81];reset();memset(p,'a',n);p[n]=0;memset(a,'R',n);a[n]=0;arm(s,p,a,0,0);j=n>40?40:n;CK(strlen((char *)records+s*86+1)==j);for(i=0;i<j;++i)CK(records[s*86+1+i]=='A');for(i=0;i<j;++i)run_when(2,'a');CK(send_count==1&&strlen(sent[0])==j&&cursor(s)==(unsigned)(records+s*86+1));}
 for(i=1;i<256;++i){unsigned char p[4];reset();p[0]=i;p[1]=0;if(i==94){p[0]=p[1]=p[2]=94;p[3]=0;}arm(0,(char *)p,"X",0,0);run_when(2,i);CK(send_count==1);}
 reset();arm(0,"AB","X",0,0);run_when(2,'A');selected=0;run_when(1,0);run_when(1,0);CK(!active_count&&!cursor(0));run_when(2,'B');CK(!send_count);arm(0,"AB","X",0,0);run_when(2,'A');arm(0,"AB","Y",0,0);CK(active_count==1);run_when(2,'B');CK(!send_count);feed((unsigned char *)"AB",2);CK(send_count==1&&!strcmp(sent[0],"Y"));
 reset();case_sensitive=1;arm(0,"abc","X",0,0);case_sensitive=0;feed((unsigned char *)"abc",3);CK(!send_count);arm(0,"abc","X",0,0);CK(!strcmp(strings[0],"ABC"));case_sensitive=1;feed((unsigned char *)"abcABC",6);CK(send_count==1);
 for(i=0;i<2;++i){reset();arm(1,"GO","",1,i);feed((unsigned char *)"GO",2);CK(call_count==1&&called==target&&frame_count==i&&wait_gate==1);}
 reset();arm(3,"","BYE",0,0);CK(disconnect_armed&&!active_count);CK(run_when(4,0)==0&&!send_count);carrier=0;CK(run_when(4,0)==0&&send_count==1&&!disconnect_armed);run_when(4,0);CK(send_count==1);arm(3,"","X",0,0);selected=3;run_when(1,0);CK(!disconnect_armed);
 reset();ready=1;key=65;run_when(4,0);CK(dispatches==1&&last_key==65&&pending_key==65535);keyboard_disabled=1;run_when(4,0);CK(dispatches==1);keyboard_disabled=0;key=27;confirm=0;CK(!run_when(4,0)&&!aborts);confirm=1;CK(run_when(4,0)==1&&aborts==1);
 CK(!abi_bad);printf("WHEN %u checks %u failed\n",checks,failed);return failed?1:0;
}
'''

def dos():
 aliases=[('aspect_when_records','records'),('aspect_when_active_count','active_count'),('aspect_when_disconnect_armed','disconnect_armed'),('aspect_when_case_sensitive','case_sensitive'),('aspect_flow_wait_gate','wait_gate'),('aspect_when_pending_key','pending_key'),('aspect_when_keyboard_disabled','keyboard_disabled'),('aspect_when_last_key','last_key')]
 asm=DOS_ASM
 # C owns storage; native module imports aliases bound to the same addresses.
 for native,c in aliases:asm+=f'global _{c},{native}\n{native}:\n_{c}: '+('times 344 db 0' if c=='records' else 'dw 0')+'\n'
 (OUT/'callbacks.asm').write_text(asm);(OUT/'diagnostic.c').write_text(DOS_C)
 inc='-I'+str(ROOT/'reconstruction/uart')+'/'
 objects=[OUT/'when.obj']
 for name,rel,defs in [('copy','reconstruction/erase/move_bytes.asm',['-DERASE_OMF']),('upper','reconstruction/directory_dial/uppercase.asm',['-DDIRECTORY_DIAL_OMF'])]:
  target=OUT/(name+'.obj');subprocess.run(['nasm','-f','obj',inc,*defs,str(ROOT/rel),'-o',str(target)],check=True);objects.append(target)
 subprocess.run(['nasm','-f','obj','callbacks.asm','-o','callbacks.obj'],cwd=OUT,check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-fm=WHEN.map','-fe=WHEN.EXE','diagnostic.c',*[str(o) for o in objects],'callbacks.obj'],cwd=OUT,check=True)
 conf=OUT/'dosbox.conf';conf.write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nWHEN >RESULT.TXT\nexit\n')
 (OUT/'RESULT.TXT').unlink(missing_ok=True)
 with (OUT/'dosbox.log').open('w') as f:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(conf)],stdout=f,stderr=f,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=30,check=True)
 result=(OUT/'RESULT.TXT').read_text();assert result.startswith('WHEN ') and result.endswith(' checks 0 failed\n'),result
 return int(result.split()[1])
def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();native=[]
 if a.original:
  image=a.original.read_bytes();assert sha(image)==ORIGINAL
  for n,start,end,base in UNITS:
   assert image[base+start:base+end]==(OUT/f'unit{n}.bin').read_bytes();native.append(dict(unit=n,bytes=end-start,file_offset=base+start))
  for name,rel,defs,start,end in HELPERS:
   assert image[0x1200+start:0x1200+end]==(OUT/(name+'.bin')).read_bytes();native.append(dict(helper=name,bytes=end-start,file_offset=0x1200+start))
  for name,rel,macro,n,start,end in COMPOSITION:
   base=55728 if start>=0xd0d0 else 0x1200
   assert image[base+start:base+end]==(OUT/(name+'.bin')).read_bytes();native.append(dict(composition=name,bytes=end-start,file_offset=base+start))
 fixture=ROOT/'standalone/fixtures/aspect_when_vectors.json';corpus=json.loads(fixture.read_text())
 for vector in corpus['vectors']+corpus['compiler_rejected']:
  assert sha(vector['source'].encode(vector['source_encoding']))==vector['source_sha256']
  if 'asx_hex' in vector:assert sha(bytes.fromhex(vector['asx_hex']))==vector['asx_sha256']
 cases,addresses=cpu();flows=composed();count=dos()
 instruction_set={int(a,16)+0x10000 for a in re.findall(r'^when_loc_([0-9a-f]+):',SOURCE.read_text(),re.M)}
 assert instruction_set<=set(addresses)
 manifest=json.loads((OUT/'manifest.json').read_text());assert manifest['source_sha256']==sha(SOURCE.read_bytes())
 for unit in manifest['units']:assert sha((OUT/f"unit{unit['unit']}.bin").read_bytes())==unit['sha256']
 for part in manifest['helpers']+manifest['composition']:assert sha((OUT/(part['name']+'.bin')).read_bytes())==part['sha256'] and sha((ROOT/part['source']).read_bytes())==part['source_sha256']
 for path,digest in manifest['source_dependencies'].items():assert sha((ROOT/path).read_bytes())==digest
 report=dict(passed=True,original_inputs=[str(a.original)] if a.original else [],original_comparison=native,source_sha256=sha(SOURCE.read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),builder_sha256=sha((ROOT/'standalone/build_aspect_when.py').read_bytes()),manifest_sha256=sha((OUT/'manifest.json').read_bytes()),binary_sha256=sha((OUT/'WHEN.EXE').read_bytes()),native_instruction_coverage=dict(covered=len(instruction_set&set(addresses)),total=len(instruction_set)),compiler_corpus=dict(accepted=len(corpus['vectors']),rejected=len(corpus['compiler_rejected'])),composed_cases=flows,fixture_sha256=sha((ROOT/'standalone/fixtures/aspect_when_vectors.json').read_bytes()),cpu_cases=cases,instruction_addresses=[hex(a) for a in addresses],dos_assertions=count,generated_sources={p.name:sha(p.read_bytes()) for p in [OUT/'callbacks.asm',OUT/'diagnostic.c']},scope='Exact602 native WHEN/CWHEN/monitor/trigger/service bytes; source-built native copy/uppercase/caret. Slot numeric parser/string/token/DWORD input, uppercase-byte, TX/call requests and host/carrier/keyboard services are explicit callback models. Four source-only CPU compositions additionally execute native dispatcher/flow/frame/stack/operands/literals/WAITFOR/read selectors with modeled FILE/byte/platform IO, reproducing independently predicted original compiler sources. ActualDOS diagnostic captures call requests; actual procedure bodies are proven in CPU composition, not DOS VM. Renderer/UART hardware and full application remain outside scope.')
 (OUT/('checks-native.json' if a.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print('WHEN:',len(cases),'CPU cases /',len(addresses),'instruction addresses;',count,'actual8086 DOS assertions PASS')
if __name__=='__main__':main()
