#!/usr/bin/env python3
"""Source-only CPU tests for CLI parsing and atomic UART-state selection."""
import argparse,hashlib,itertools,json,random,subprocess
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_ES,UC_X86_REG_EFLAGS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_INS_IN,UC_X86_INS_OUT
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
SERIAL_FIELDS=['terminal_baud_low','terminal_baud_high','terminal_parity','terminal_data_bits','terminal_stop_bits','terminal_irq_vector','terminal_port_number','uart_port_index','uart_irq_indices','uart_port_rbr','uart_port_thr','uart_port_ier','uart_port_lcr','uart_port_mcr','uart_port_lsr','uart_port_msr','uart_software_flow','uart_hardware_flow']
FIELDS=SERIAL_FIELDS+['terminal_option_mask']
RATES=[300,1200,2400,4800,9600,19200,38400,57600,115200]

def fixture():
 out=ROOT/'build/terminal-options';out.mkdir(parents=True,exist_ok=True)
 source='BITS 16\nCPU 8086\nSEGMENT _TEXT public class=CODE use16\nGROUP DGROUP _DATA STACK\n..start:\n mov ax,0x4c00\n int 0x21\nSEGMENT _DATA public class=DATA use16\n'
 for name in SERIAL_FIELDS:source+='global '+name+'\n'+name+': '+('times 16 dw 0' if name=='uart_irq_indices' else 'dw 0')+'\n'
 source+='global uart_irq_enable_masks,uart_irq_disable_masks\nuart_irq_enable_masks: times 16 dw 0x5a5a\nuart_irq_disable_masks: times 16 dw 0xa5a5\nSEGMENT STACK stack class=STACK use16\n resb 4096\n'
 (out/'host.asm').write_text(source)
 for path,obj in [(ROOT/'src/terminal/options.asm',out/'options.obj'),(out/'host.asm',out/'host.obj')]:subprocess.run(['nasm','-f','obj',str(path),'-o',str(obj)],check=True)
 subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'options.map'),'name',str(out/'OPTIONS.EXE'),'file',str(out/'options.obj')+','+str(out/'host.obj')],check=True)
 return out/'OPTIONS.EXE',out/'options.map'

class Options(DosImage):
 def __init__(self,binary,map_path):
  super().__init__(binary,map_path)
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.uc.hook_add(UC_HOOK_INSN,self.io,None,1,0,UC_X86_INS_IN)
  self.uc.hook_add(UC_HOOK_INSN,self.io,None,1,0,UC_X86_INS_OUT)
 def interrupt(self,*args):raise AssertionError('CLI parser attempted interrupt IO')
 def io(self,*args):raise AssertionError('CLI parser touched hardware')
 def parse(self,data,length=None):
  self.uc.mem_write(0x70080,bytes([len(data) if length is None else length])+data+b'\r')
  self.uc.reg_write(UC_X86_REG_AX,0x7000);self.uc.reg_write(UC_X86_REG_ES,0x6666)
  status=self.call('terminal_parse_options',limit=50000)
  assert self.uc.reg_read(UC_X86_REG_BP)==0xbabe and self.uc.reg_read(UC_X86_REG_SI)==0x1234 and self.uc.reg_read(UC_X86_REG_DI)==0x5678
  assert self.uc.reg_read(UC_X86_REG_ES)==0x6666
  return status,self.uc.reg_read(UC_X86_REG_EFLAGS)&1
 def snapshot(self):return {**{name:self.get(name) for name in FIELDS},'terminal_config_path':bytes(self.uc.mem_read(self.symbols['terminal_config_path'],64)),'terminal_dial_target':bytes(self.uc.mem_read(self.symbols['terminal_dial_target'],64))}
 def expected(self,port=1,rate=38400,parity=0,bits=8,stop=1,flow='NONE',mask=0,path=b'',dial=b''):
  base=[0x3f8,0x2f8,0x3e8,0x2e8][port-1];irq=[4,3,4,3][port-1]
  expected=dict(zip(SERIAL_FIELDS,[rate&65535,rate>>16,parity,bits,stop,irq+8,port,0,irq,base,base,base+1,base+3,base+4,base+5,base+6,int(flow=='SOFT'),int(flow=='HARD')]))
  expected.update(terminal_option_mask=mask,terminal_config_path=path+bytes(64-len(path)),terminal_dial_target=dial+bytes(64-len(dial)))
  assert self.snapshot()==expected,(self.snapshot(),expected)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--binary',type=Path);parser.add_argument('--map',type=Path);args=parser.parse_args()
 if bool(args.binary)!=bool(args.map):parser.error('--binary and --map must be specified together')
 binary,map_path=(args.binary,args.map) if args.binary else fixture()
 cases=[];count=[0]
 def check(name,test):test();cases.append({'case':name,'passed':True});print(name,'passed')
 def defaults():
  o=Options(binary,map_path)
  for data in [b'',b' ',b'\t  \t',b' '*127]:
   assert o.parse(data)==(0,0);o.expected();count[0]+=1
 check('empty-and-whitespace-tails-select-documented-defaults',defaults)
 def ports_bauds():
  o=Options(binary,map_path)
  masks={name:bytes(o.uc.mem_read(o.symbols[name],32)) for name in ['uart_irq_enable_masks','uart_irq_disable_masks']}
  for port,rate in itertools.product(range(1,5),RATES):
   assert o.parse(f'com{port} {rate}'.encode())==(0,0);o.expected(port=port,rate=rate,mask=3);count[0]+=1
   for name,data in masks.items():assert bytes(o.uc.mem_read(o.symbols[name],32))==data
 check('all-com-base-irq-and-32bit-baud-selections',ports_bauds)
 def serial_flow():
  o=Options(binary,map_path);rng=random.Random(201)
  for parity,bits,stop,flow in itertools.product('NOEMS',[7,8],[1,2],['NONE','SOFT','HARD']):
   tokens=['COM4','115200',f'{bits}{parity}{stop}',flow];rng.shuffle(tokens)
   assert o.parse(('\t'.join(tokens)).lower().encode())==(0,0)
   o.expected(4,115200,'NOEMS'.index(parity),bits,stop,flow,mask=15);count[0]+=1
  for alias,flow in [('N','NONE'),('S','SOFT'),('H','HARD')]:
   assert o.parse(alias.encode())==(0,0);o.expected(flow=flow,mask=8);count[0]+=1
 check('all-parity-data-stop-flow-combinations-case-and-order',serial_flow)
 def invalid():
  o=Options(binary,map_path)
  for index,name in enumerate(FIELDS):o.put(name,0xa500+index)
  o.uc.mem_write(o.symbols['terminal_config_path'],bytes(range(64)))
  o.uc.mem_write(o.symbols['terminal_dial_target'],bytes(range(64,128)))
  before=o.snapshot()
  for data in [b'COM0',b'COM5',b'COM11',b'14400',b'0',b'9601',b'8Z1',b'6N1',b'8N0',b'8N3',b'SOFTWARE',b'NONE HARD',b'COM2 COM3',b'9600 300',b'8N1 7E2',b'COM2 115200 8N1 JUNK',b'x'*16,b'\0',b'\r',b'\xff',b'--unknown',b'/COM2']:
   assert o.parse(data)==(2,1),(data,o.parse(data));assert o.snapshot()==before;count[0]+=1
  assert o.parse(b'',length=128)==(2,1) and o.snapshot()==before;count[0]+=1
 check('invalid-and-duplicate-tokens-never-partially-commit',invalid)
 def help_options():
  o=Options(binary,map_path)
  for data in [b'?',b'/?',b'/h',b'-H',b'--help',b'HeLp',b'COM3 115200 SOFT /?']:
   before=o.snapshot();assert o.parse(data)==(1,1) and o.snapshot()==before;count[0]+=1
 check('help-returns-cleanly-before-settings-or-hardware-effects',help_options)
 def configs():
  o=Options(binary,map_path)
  assert o.get('terminal_option_mask')==0 and o.snapshot()['terminal_config_path']==bytes(64)
  paths=[b'PCPLUS.PRM',b'C:\\PCPLUS\\SYSTEM.PRM',b'D:CONFIG.PRM',b'.\\LOCAL.PRM',b'..\\OLD\\PCPLUS.PRM',b'/LOCAL/PCPLUS.PRM',b'A'*59+b'.PRM']
  for path in paths:
   assert o.parse(b'@'+path.lower())==(0,0);o.expected(mask=16,path=path);count[0]+=1
   assert o.parse(b'COM2 @'+path.lower()+b' 19200 7E2 HARD')==(0,0)
   o.expected(2,19200,2,7,2,'HARD',mask=31,path=path);count[0]+=1
  assert o.parse(b'@'+b'A'*63+b' '*63)==(0,0);o.expected(mask=16,path=b'A'*63);count[0]+=1
  # Explicit selections must remain distinguishable even when they match defaults.
  for token,mask in [(b'COM1',1),(b'38400',2),(b'8N1',4),(b'NONE',8)]:
   assert o.parse(token)==(0,0);o.expected(mask=mask);count[0]+=1
  # A new successful parse resets staged path and explicit-selection bits.
  assert o.parse(b'COM3')==(0,0);o.expected(port=3,mask=1);count[0]+=1
  assert o.parse(b'@A.PRM')==(0,0);o.expected(mask=16,path=b'A.PRM');count[0]+=1
  assert o.parse(b'')==(0,0);o.expected();count[0]+=1
 check('explicit-PRM-paths-max63-and-selection-mask-reset',configs)
 def config_rollback():
  o=Options(binary,map_path)
  assert o.parse(b'COM4 @GOOD.PRM 115200 7O2 SOFT')==(0,0)
  before=o.snapshot()
  invalid=[b'@',b'@'+b'A'*64,b'@*.PRM',b'@FILE?.PRM',b'@"A.PRM"',b"@'A.PRM'",b'@A.PRM @B.PRM',b'@A.PRM @A.PRM',b'@C:\\BAD NAME.PRM',b'@GOOD.PRM COM2 COM3',b'COM1 9600 @GOOD.PRM JUNK',b'COM1 @BAD\0.PRM',b'@BAD\xff.PRM',b'@BAD\x7f.PRM',b'@BAD\r.PRM',b'@BAD\x1f.PRM']
  for tail in invalid:
   assert o.parse(tail)==(2,1),(tail,'unexpected result')
   assert o.snapshot()==before,tail;count[0]+=1
  for tail in [b'@NEW.PRM /?',b'COM1 @NEW.PRM HELP',b'@'+b'A'*63+b' --help']:
   assert o.parse(tail)==(1,1) and o.snapshot()==before;count[0]+=1
  # A failed stage cannot leak to a subsequent valid parse.
  assert o.parse(b'19200')==(0,0);o.expected(rate=19200,mask=2);count[0]+=1
 check('PRM-invalid-duplicate-help-and-full-state-rollback',config_rollback)
 def dial_targets():
  o=Options(binary,map_path)
  assert o.snapshot()['terminal_dial_target']==bytes(64)
  targets=[b'bbs.example:23',b'Example_BBS-2.net:2323',b'[2001:db8::1]:23',b'telnet://Bbs.Example/CaseSensitive@Path?x=AB%20cd&mode=Hi',b'0123456789',b'A'*62+b'z']
  for target in targets:
   for selector in [b'/D:',b'/d:']:
    assert o.parse(selector+target)==(0,0);o.expected(mask=32,dial=target);count[0]+=1
   assert o.parse(b'@local.prm COM2 19200 HARD /d:'+target)==(0,0)
   o.expected(port=2,rate=19200,flow='HARD',mask=59,path=b'LOCAL.PRM',dial=target);count[0]+=1
  tail=b'/D:'+b'x'*63+b' '*61
  assert len(tail)==127 and o.parse(tail)==(0,0);o.expected(mask=32,dial=b'x'*63);count[0]+=1
  assert o.parse(b'@A.PRM /D:OldCase')==(0,0);count[0]+=1
  assert o.parse(b'@B.PRM')==(0,0);o.expected(mask=16,path=b'B.PRM');count[0]+=1
  assert o.parse(b'')==(0,0);o.expected();count[0]+=1
 check('dial-target-case-prefix-punctuation-max63-and-reset',dial_targets)
 def dial_rollback():
  o=Options(binary,map_path)
  assert o.parse(b'COM4 @KEEP.PRM /d:KeepCase 115200 7O2 SOFT')==(0,0)
  before=o.snapshot()
  bad=[b'/D:',b'/D:'+b'a'*64,b'/D:host /d:other',b'/D:host /D:host',b'/D:good COM2 COM3',b'@NEW.PRM /D:Good JUNK',b'/D:bad name',b'/D:bad\tname',b'/D:bad\rname',b'/D:bad\0name',b'/D:bad\xffname',b'/D:bad\x7fname']
  for byte in b"\"'^~;,|<>+!#$(){}\\`*":bad.append(b'/D:bad'+bytes([byte])+b'Host')
  for tail in bad:
   assert o.parse(tail)==(2,1),(tail,'unexpected result')
   assert o.snapshot()==before,tail;count[0]+=1
  for tail in [b'/D:NewCase /?',b'@NEW.PRM /D:NewCase HELP',b'COM1 --help /D:NewCase']:
   assert o.parse(tail)==(1,1) and o.snapshot()==before;count[0]+=1
  assert o.parse(b'8N1')==(0,0);o.expected(mask=4);count[0]+=1
 check('dial-duplicates-unsafe-input-help-atomic-global-rollback',dial_rollback)
 out=ROOT/'build/terminal-options';out.mkdir(parents=True,exist_ok=True)
 result={'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'options_source_sha256':hashlib.sha256((ROOT/'src/terminal/options.asm').read_bytes()).hexdigest(),'passed':True,'cases':cases,'inputs':count[0],'scope':'Actual linked source-only 8086 option parser; command tails synthetic, every interrupt/port-IO forbidden, no UART installation.'}
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
