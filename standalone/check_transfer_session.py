#!/usr/bin/env python3
"""Native session fragments and genuine nonlocal cancellation with explicit IO fixture."""
import argparse,hashlib,json,struct
from pathlib import Path
from dos_image import DosImage
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_BP,UC_X86_REG_DI,UC_X86_REG_SI
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/transfer-session/SESSION.EXE'
class Session(DosImage):
 def __init__(self):super().__init__(BINARY,BINARY.parent/'transfer_session.map')
 def result(self,mode):
  result=self.call('_transfer_session_probe',[mode],limit=1000000)
  return dict(result=result,wire=bytes(self.uc.mem_read(self.symbols['session_wire'],self.get('session_wire_count'))).hex(),delays=self.get('session_delay_calls'),status=self.get('session_status_code'),close=self.get('session_close_calls'),timed=self.get('session_timed_calls'),crc=self.get('session_probe_crc'))
def vectors():
 result=[]
 for protocol,stream,wire in [(4,0,b'C'),(9,0,b'W'),(12,0,b'U'),(10,1,b'G'),(11,1,b'G')]:
  for arrival in (1,2):result.append((f'handshake-{protocol}-{arrival}',0,{'session_protocol':protocol,'session_streaming_mode':stream,'session_arrival_delay':arrival},wire,0x9009 if protocol==9 else 0x900c if protocol==12 else 0))
 result.append(('CRC-fallback-eleven-NAKs-no-input',0,{},b'CCC'+b'\x15'*11,0))
 result.append(('checksum-fallback-arrival',0,{'session_arrival_delay':109},b'CCC\x15',0))
 for mode,count in ((0,36),(1,200),(2,200)):
  result.append((f'waitmode-{mode}',2,{'session_wait_mode':mode},b'',1))
 result.append(('short-wait',2,{'session_short_wait':1},b'',1))
 result.append(('wait-arrival',2,{'session_arrival_delay':1},b'',1))
 for control in (0,1,0xffff):
  result.append((f'wait-local-cancel-{control}',2,{'session_cancel_requested':control},b'',0xffff if control else 1))
 result.append(('wait-carrier-drop',2,{'session_carrier':0},b'',0xffff))
 for retries in (0,14,15,16,65535):result.append((f'retry-limit-{retries}',1,{'session_probe_retries':retries},b'',15 if retries==15 else 0))
 result += [('retry-local-cancel',1,{'session_cancel_requested':1},b'',0x107),('retry-carrier-drop',1,{'session_carrier':0},b'',0x10f),('retry-double-CAN',1,{'session_streaming_mode':1,'session_control_byte':0x18,'session_control_second':0x18},b'',0x107),('retry-single-CAN',1,{'session_streaming_mode':1,'session_control_byte':0x18,'session_control_second':0xffff},b'',0)]
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();cases=[];observed=[]
 for name,mode,settings,wire,result in vectors():
  m=Session()
  for key,value in settings.items():m.put(key,value)
  got=m.result(mode);assert got['result']==result and got['wire']==wire.hex(),(name,got)
  if name=='CRC-fallback-eleven-NAKs-no-input':assert got['delays']==207 and got['crc']==0
  if name.startswith('waitmode-'):assert got['delays']==(36 if settings['session_wait_mode']==0 else 200)
  if name=='short-wait':assert got['delays']==91
  if name=='wait-arrival':assert m.get('session_started_low')==0x1234 and m.get('session_started_high')==0x5678
  if name=='retry-double-CAN':assert got['status']==11 and got['timed']==1
  observed.append(got);cases.append({'case':name,'passed':True})
 for value in (0,1,7,15,32768,65535):
  m=Session();m.put('session_probe_jump_value',value);assert m.result(4)['result']==(value or 1)
  assert m.get('session_probe_returned')==0 and m.get('session_probe_si')==0x1357 and m.get('session_probe_di')==0x2468
  cases.append({'case':f'actual-setjmp-longjmp-stack-register-restoration-{value}','passed':True})
 proof=json.loads((ROOT/'reconstruction/transfer_session/provenance.json').read_text())
 for protocol in range(14):
  m=Session();m.put('session_protocol',protocol)
  for name in ['session_state_cb56','session_state_cb54','session_state_cb3a','session_error_count','session_blocks_accepted','session_state_cd7a','session_file_handle','session_total_low','session_total_high','session_expected_low','session_expected_high','session_bytes_low','session_bytes_high','session_state_cd76','session_state_cd3a']:m.put(name,0xffff)
  assert m.result(3)['result']==0
  assert all(m.get(name)==0 for name in ['session_state_cb56','session_state_cb54','session_state_cb3a','session_error_count','session_blocks_accepted','session_state_cd7a','session_file_handle','session_total_low','session_total_high','session_expected_low','session_expected_high','session_bytes_low','session_bytes_high','session_state_cd76','session_state_cd3a'])
  assert m.get('session_streaming_mode')==int(protocol in (10,11)) and m.get('session_rate_low')==38400 and m.get('session_rate_high')==0 and m.get('session_buffer_pointer')==m.offset('session_payload')
  cases.append({'case':f'native-initialize-protocol-{protocol}','passed':True})
 for prefix,path_test,open_result in [(b'',0,3),(b'C:\\FILES\\',1,3),(b'',0,0)]:
  m=Session();m.put('session_arrival_delay',1);m.put('session_path_test_result',path_test);m.put('session_open_result',open_result);m.uc.mem_write(m.symbols['session_download_prefix'],prefix+b'\0')
  assert m.call('session_receive',[m.offset('session_test_filename')],limit=1000000)==0
  assert m.get('session_open_calls')==1
  pointer=m.get('session_open_path_pointer');assert bytes(m.uc.mem_read(m.data_base+pointer,80)).split(b'\0')[0]==prefix+b'TEST.BIN'
  assert m.get('session_open_mode_pointer')==m.offset('session_open_mode') and m.get('session_file_handle')==open_result
  assert m.get('session_status_code')==(12 if not open_result else 0)
  cases.append({'case':f'actual-receive-preamble-open-prefix-{bool(prefix)}-success-{bool(open_result)}','passed':True})
 if a.original:
  from check_directory_dial_original import Original,DATA,EXPECTED
  image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
  overlays=[x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==21]
  state={v:int(k,16) for k,v in proof['state'].items()}
  class OriginalSession(Original):
   def __init__(self,settings):
    self.settings=settings;self.wire=bytearray();self.delays=0;self.status=0;self.close=0;self.timed=0;self.result=None
    super().__init__(image,overlays)
    for address,value in [(0x3996,4)]+[(state[k],v) for k,v in settings.items() if k in state]:self.put(address,value)
   def hook(self,u,at,size,unused):
    if at in (0x1dc6a,0x1dcf1,0x1d8ae,0x1d734,0x1f000):
     self.result=0 if at in (0x1dc6a,0x1d734) else 15 if at==0x1dcf1 else 0x100+self.get(0xc000-0x12) if at==0x1d8ae else u.reg_read(UC_X86_REG_AX);u.emu_stop();return
    if at not in (0x13f4b,0x14861,0x16b98,0x16bf0,0x177fe,0x1e498,0x1ab0b,0x1aad9,0x15ca0,0x18318,0x1d077,0x1d06b):return
    sp=u.reg_read(UC_X86_REG_SP);ret,arg=struct.unpack('<2H',u.mem_read(DATA+sp,4));cleanup=0;result=0
    if at==0x13f4b:result=self.settings.get('session_cancel_requested',0)
    elif at==0x14861:result=self.settings.get('session_carrier',1)
    elif at==0x16b98:
     cleanup=2;self.delays+=1
     if self.delays==self.settings.get('session_arrival_delay',0):self.put(0x8e20,1)
    elif at==0x16bf0:cleanup=6
    elif at==0x177fe:result=0x1234;u.reg_write(UC_X86_REG_DX,0x5678)
    elif at==0x1e498:self.status=arg
    elif at==0x1ab0b:self.wire.append(arg&255);cleanup=2
    elif at==0x1aad9:self.timed+=1;cleanup=2;result=self.settings.get('session_control_byte',65535)
    elif at==0x15ca0:result=self.settings.get('session_control_second',65535)
    elif at==0x18318:self.close+=1
    elif at==0x1d077:result=0x900c
    elif at==0x1d06b:result=0x9009
    u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)
   def run(self,mode):
    self.uc.reg_write(UC_X86_REG_BP,0xc000);self.uc.reg_write(UC_X86_REG_SP,0xc000-0x5c);self.uc.mem_write(DATA+0xc000-0x5c,struct.pack('<2H',0x1234,0x5678));self.uc.mem_write(DATA+0xc000,struct.pack('<2H',0xbabe,0xf000))
    if mode==2:self.uc.reg_write(UC_X86_REG_SP,0xbf00);self.put(0xbf00,0xf000)
    if mode==1:self.put(0xc000-0x14,self.settings.get('session_probe_retries',0));self.put(0xc000-0x10,65535)
    self.uc.emu_start(0x10000+{0:0xd752,1:0xd87c,2:0xf070}[mode],0x20000,count=1000000)
    assert self.result is not None
    return dict(result=self.result,wire=self.wire.hex(),delays=self.delays,status=self.status,close=self.close,timed=self.timed)
  for vector,want in zip(vectors(),observed):
   name,mode,settings,*_=vector;o=OriginalSession(settings);got=o.run(mode);assert got=={k:want[k] for k in got},(name,got,want)
   cases.append({'case':'original-'+name,'passed':True})
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Exact native session initialization, handshake, retry and genuine setjmp/longjmp cancellation. Explicit diagnostic UART/time/UI/path/file-open checkpoints; no complete transfer or live UART/file commit claim.'}
 (BINARY.parent/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(cases),'native session cases')
if __name__=='__main__':main()
