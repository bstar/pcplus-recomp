#!/usr/bin/env python3
"""Exact native printer/logger CPU tests; --original is explicit optional replay."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/printer'
PROOF=json.loads((ROOT/'reconstruction/printer/provenance.json').read_text())
COUNTERS=['open','putc','flush','close','status','capture_error','capture_close']
FIELDS=['printer_enabled','printer_stream','terminal_cr_adds_lf','terminal_sink_398a_enabled','terminal_sink_398c_disabled','terminal_sink_handle','fixture_open_result','fixture_putc_result','fixture_capture_putc_result','fixture_flush_result','fixture_close_result','fixture_last_handle','fixture_wire_count','fixture_trace_count']+['fixture_'+n+'_calls' for n in COUNTERS]
class Original:
 def __init__(self):
  b=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(b).hexdigest()==PROOF['source_sha256']
  self.uc=Uc(UC_ARCH_X86,UC_MODE_16);self.uc.mem_map(0,0x100000);self.uc.mem_write(0x10000,b[0x1200:0xe2d0]);self.base=0x10000;self.ds=0x4000;self.data_base=0x40000
  self.symbols={name:self.data_base+int(at,16) for at,name in PROOF['state'].items()}
  self.symbols.update({name:self.base+int(at,16) for at,name in PROOF['boundaries'].items()})
  for at,name in PROOF['state'].items():self.symbols[name]=self.data_base+int(at,16)
  state={0x1d24:'terminal_cr_adds_lf',0x398a:'terminal_sink_398a_enabled',0x398c:'terminal_sink_398c_disabled',0xd114:'terminal_sink_handle',0x418a:'terminal_sink_error_state'}
  self.symbols.update({name:self.data_base+at for at,name in state.items()})
  self.symbols['terminal_log_character']=0x109b6
  for i,name in enumerate(n for n in FIELDS if n not in self.symbols):self.symbols[name]=self.data_base+0x5000+i*2
  self.symbols['fixture_last_filename']=self.data_base+0x5100;self.symbols['fixture_last_mode']=self.data_base+0x5102;self.symbols['fixture_wire']=self.data_base+0x5200;self.symbols['fixture_trace']=self.data_base+0x5400
  self.symbols['fixture_guard_before']=self.data_base+0x51fe;self.symbols['fixture_guard_after']=self.data_base+0x5300
  self.put('fixture_guard_before',0x5aa5);self.put('fixture_guard_after',0xa55a)
  self.uc.mem_write(self.symbols['printer_device'],b'PRN\0');self.uc.mem_write(self.symbols['printer_binary_mode'],b'wb\0');self.uc.hook_add(UC_HOOK_CODE,self.boundary)
 def get(self,name):return int.from_bytes(self.uc.mem_read(self.symbols[name],2),'little')
 def put(self,name,value):self.uc.mem_write(self.symbols[name],struct.pack('<H',value))
 def boundary(self,u,address,size,_):
  counters={0x8436:'putc',0x8c54:'flush',0x841a:'open',0x8318:'close',0x2fb8:'status',0x427f:'capture_error',0xbb23:'capture_close'}
  if address-0x10000 not in counters:return
  kind=counters[address-0x10000];trace=self.get('fixture_trace_count');self.uc.mem_write(self.symbols['fixture_trace']+trace,{'open':b'O','close':b'C','putc':b'P','flush':b'F','status':b'S','capture_error':b'E','capture_close':b'L'}[kind]);self.put('fixture_trace_count',trace+1);counter='fixture_'+kind+'_calls';self.put(counter,self.get(counter)+1)
  sp=u.reg_read(UC_X86_REG_SP);words=struct.unpack('<3H',u.mem_read(self.data_base+sp,6));result=None
  if kind=='open':self.put('fixture_last_filename',words[1]);self.put('fixture_last_mode',words[2]);result=self.get('fixture_open_result')
  elif kind in ('putc','flush','close'):
   self.put('fixture_last_handle',words[2] if kind=='putc' else words[1]);result=self.get('fixture_capture_putc_result') if kind=='putc' and words[2]==self.get('terminal_sink_handle') else self.get('fixture_'+kind+'_result')
   if kind=='putc' and result!=0xffff:
    count=self.get('fixture_wire_count');assert count<256;u.mem_write(self.symbols['fixture_wire']+count,bytes([words[1]&255]));self.put('fixture_wire_count',count+1)
  elif kind=='capture_close':self.put('terminal_sink_398a_enabled',0)
  if result is not None:u.reg_write(UC_X86_REG_AX,result)
  u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,words[0])

def call(m,name,args=()):
 u=m.uc;returned=[]
 def stop(u,at,size,_):
  if at==0x1f000:returned.append(True);u.emu_stop()
 hook=u.hook_add(UC_HOOK_CODE,stop);m.returned=False
 for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_ES,0x1234),(UC_X86_REG_SP,0xe000),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468),(UC_X86_REG_AX,0x7777),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
 u.mem_write(m.data_base+0xe000,struct.pack('<'+'H'*(len(args)+1),0xf000,*args));u.emu_start(m.symbols[name],0x20000,count=100000);u.hook_del(hook)
 assert returned or m.returned
 assert u.reg_read(UC_X86_REG_SP)==0xe002
 for r,v in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]:assert u.reg_read(r)==v,(name,r)
 assert m.get('fixture_guard_before')==0x5aa5 and m.get('fixture_guard_after')==0xa55a
 return u.reg_read(UC_X86_REG_AX)
def cstring(m,field):
 offset=m.get(field)
 if not offset:return ''
 value=bytearray()
 while len(value)<32:
  b=bytes(m.uc.mem_read(m.data_base+offset+len(value),1))
  if b==b'\0':return value.decode('ascii')
  value.extend(b)
 raise AssertionError('Unterminated fixture string')
def run(original=False):
 cases=[]
 for kind in ['byte','logger']:
  for value in [0,10,13,26,65,127,128,255,0x01ff,0x017f,0x010d]:
   for newline in [0,1]:cases.append(dict(kind=kind,value=value,newline=newline))
 for putc,flush in [(0xffff,0),(0,0xffff),(0xffff,0xffff),(0xffff,0x1234)]:cases.append(dict(kind='byte',value=65,putc=putc,flush=flush))
 for enabled,result in [(0,0x1111),(0,0),(1,0),(2,0xffff)]:cases.append(dict(kind='toggle',enabled=enabled,result=result))
 for paused in [0,1]:cases.append(dict(kind='logger',value=65,capture=1,paused=paused))
 cases += [dict(kind='logger',value=65,capture=1,putc=0xffff),dict(kind='logger',value=65,capture=1,capture_putc=0xffff),dict(kind='logger',value=13,capture=1,newline=1,capture_putc=0xffff),dict(kind='logger',value=65,capture=1,flush=0xffff)]
 for enabled in [0,1]:
  for capture in [0,1]:
   for paused in [0,1]:cases.append(dict(kind='logger',value=65,enabled=enabled,capture=capture,paused=paused))
 output=[]
 for case in cases:
  m=Original() if original else DosImage(OUT/'PRINTER.EXE',OUT/'printer.map')
  for name,n in [('printer_enabled',case.get('enabled',1)),('printer_stream',0x1111),('terminal_cr_adds_lf',case.get('newline',0)),('terminal_sink_398a_enabled',case.get('capture',0)),('terminal_sink_398c_disabled',case.get('paused',0)),('terminal_sink_handle',0x2222),('fixture_open_result',case.get('result',0x1111)),('fixture_putc_result',case.get('putc',0)),('fixture_capture_putc_result',case.get('capture_putc',0)),('fixture_flush_result',case.get('flush',0)),('fixture_close_result',case.get('result',0))]:m.put(name,n)
  entry={'byte':'printer_byte_original','logger':'terminal_log_character','toggle':'printer_toggle_original'}[case['kind']]
  ax=call(m,entry,() if case['kind']=='toggle' else (case['value'],));trace=bytes(m.uc.mem_read(m.symbols['fixture_trace'],m.get('fixture_trace_count'))).decode('ascii');state={name:m.get(name) for name in FIELDS};wire=bytes(m.uc.mem_read(m.symbols['fixture_wire'],m.get('fixture_wire_count')))
  if case['kind']=='toggle':
   if not case.get('enabled',0):assert state['printer_enabled']==1 and state['printer_stream']==case['result'] and state['fixture_open_calls']==1 and cstring(m,'fixture_last_filename')=='PRN' and cstring(m,'fixture_last_mode')=='wb'
   else:assert not state['printer_enabled'] and state['fixture_close_calls']==1 and state['printer_stream']==0x1111
   assert state['fixture_status_calls']==1
   assert trace==('OS' if not case.get('enabled',0) else 'CS')
  else:
   expected=[]
   if case['kind']=='byte' or case['value'] not in (127,255):expected=[case['value']&255]+([10] if case['value']==13 and case.get('newline') and case['kind']=='logger' else [])
   if case['kind']=='logger' and not case.get('enabled',1):expected=[]
   printer_calls=len(expected);accepted=list(expected) if case.get('putc',0)!=0xffff else [];capture_calls=0
   if case.get('capture') and not case.get('paused'):
    capture_calls=1 if case['value']!=13 or case.get('newline') else 0
    if capture_calls and case.get('capture_putc',0)!=0xffff:accepted += [10 if case['value']==13 else case['value']&255]
   assert state['fixture_flush_calls']==printer_calls
   assert state['fixture_putc_calls']==printer_calls+capture_calls
   expected_trace='PF'*printer_calls+'P'*capture_calls
   if capture_calls and case.get('capture_putc')==0xffff and case['value']!=13:expected_trace+='ELS'
   assert trace==expected_trace,(trace,expected_trace)
   assert wire==bytes(accepted)
   if case.get('capture') and case.get('capture_putc')==0xffff:assert state['fixture_capture_close_calls']==(case['value']!=13)
   if case.get('capture') and not case.get('capture_putc'):assert state['terminal_sink_398a_enabled']==1
  output.append(dict(case=case,result=ax,state=state,wire=wire.hex(),trace=trace))
 return output

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');a=p.parse_args();rows=run();compared=0
 if a.original:assert rows==run(True);compared=len(rows)
 m=DosImage(OUT/'PRINTER.EXE',OUT/'printer.map');assert m.call('_printer_dos_test')==0
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'PRINTER.EXE').read_bytes()).hexdigest(),'native_printer_bytes':79,'borrowed_logger_bytes':132,'case_count':len(rows),'original_comparisons':compared,'cases':rows,'scope':'Exact native printer/logger instructions with declared memoryCRT open/putc/flush/close/status fixtures. Table-driven bytes,newlines,FF/DEL,direct-vslogger,capturepause/errors,null-open,closefailure,stack/register/canary ABI. No realPRN, private input or original application execution.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(rows),'printer cases;',compared,'original comparisons')
if __name__=='__main__':
 try:main()
 except Exception as error:
  OUT.mkdir(parents=True,exist_ok=True);(OUT/'checks.json').write_text(json.dumps({'passed':False,'error':str(error)})+'\n');raise
