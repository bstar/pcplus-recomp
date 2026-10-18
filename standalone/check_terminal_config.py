#!/usr/bin/env python3
"""Actual linked C decoder + ASM apply; no DOS, BIOS or port IO allowed."""
import hashlib,itertools,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ES,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
from check_terminal_options import Options,SERIAL_FIELDS
from terminal_config_fixtures import image,change,RATES,BASES,IRQS
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE';MAP=ROOT/'build/terminal/terminal.map'
class Import(Options):
 def __init__(self):
  super().__init__(BINARY,MAP);self.input=self.offset('screen_attribute_cells');self.output=self.input+1408
 def decode(self,payload):
  self.uc.mem_write(self.data_base+self.input,payload)
  self.uc.mem_write(self.data_base+self.output-16,b'\xcc'*74)
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  status=self.call('_terminal_import_decode',[self.input,self.output],limit=100000)
  assert self.uc.mem_read(self.data_base+self.input,1264)==payload
  assert self.uc.mem_read(self.data_base+self.output-16,16)==b'\xcc'*16
  assert self.uc.mem_read(self.data_base+self.output+42,16)==b'\xcc'*16
  for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert self.uc.reg_read(reg)==want
  return status,bytes(self.uc.mem_read(self.data_base+self.output,42))
def main():
 cases=[];counts={}
 def check(name,fn):counts[name]=fn();cases.append({'case':name,'passed':True,'inputs':counts[name]});print(name,'passed',counts[name])
 def serial():
  count=0
  for port,baud in itertools.product(range(1,5),range(9)):
   c=Import();status,data=c.decode(image(port=port,baud=baud));rate=RATES[baud]
   assert status==0 and struct.unpack('<21H',data)==(port,rate&65535,rate>>16,0,8,1,0,1,6,0x1e,0x2f,0x3f,0x70,1,1,1,BASES[port-1],IRQS[port-1],165,0xa5a5,0);count+=1
  return count
 check('all-standard-port-and-32bit-rate-imports-with-opaque-sentinels',serial)
 def flags():
  count=0
  for profile,soft,hard,wrap,scroll in itertools.product([4,6],range(2),range(2),range(2),range(2)):
   c=Import();status,data=c.decode(image(profile=profile,soft=soft,hard=hard,wrap=wrap,scroll=scroll));values=struct.unpack('<21H',data)
   assert status==0 and values[6:9]==(soft,hard,profile) and values[14:16]==(wrap,scroll);count+=1
  return count
 check('independent-flow-bools-two-profiles-and-live-wrap-scroll',flags)
 def mapping_metadata():
  for pause,delay in [(0,0),(255,65535),(94,32768),(165,0xa5a5)]:
   raw=bytearray(image());raw[0x1e2]=pause;struct.pack_into('<H',raw,0x1e4,delay)
   c=Import();status,data=c.decode(bytes(raw));assert status==0
   assert struct.unpack('<21H',data)[18:20]==(pause,delay)
   baseline=bytearray(raw);baseline[0x1e2]=165;struct.pack_into('<H',baseline,0x1e4,0xa5a5)
   other=Import();other_status,other_data=other.decode(bytes(baseline));assert other_status==0 and data[:36]==other_data[:36]
  return 4
 check('mapping-pause-byte-and-delay-word-preserved-without-serial-reinterpretation',mapping_metadata)
 def rejected():
  mutations=[(0,4,2),(0,65535,2),(2,9,2),(4,5,2),(6,0,2),(6,3,2),(8,6,2),(8,9,2),(0x176,0,2),(0x176,0x3f8,2)]
  mutations += [(0x186,irq,2) for irq in [0,2,5,8,65535]]
  mutations += [(0x198,2,3),(0x19a,65535,3)]
  mutations += [(0x194,p,4) for p in [0,5,7,65535]]
  mutations += [(off,256 if off>=0x1ae else 2,5) for off in [0x19c,0x19e,0x1ae,0x1b0,0x1b2,0x1b4,0x1b6]]
  for offset,value,want in mutations:
   c=Import();status,data=c.decode(change(image(),offset,value));assert status==want and data==b'\xcc'*42,(offset,value,status,want)
  c=Import();c.uc.reg_write(UC_X86_REG_ES,c.ds);assert c.call('_terminal_import_decode',[0,c.output])==6
  assert c.call('_terminal_import_decode',[c.input,0])==6
  return len(mutations)+2
 check('unsupported-known-fields-and-null-arguments-never-commit',rejected)
 def precedence():
  for mask in range(16):
   c=Import();tokens=[b'@SYN.PRM']+[token for bit,token in [(1,b'COM3'),(2,b'115200'),(4,b'7E2'),(8,b'NONE')] if mask&bit]
   assert c.parse(b' '.join(tokens))==(0,0)
   status,data=c.decode(image(profile=4,soft=1,hard=1,wrap=0,scroll=0));assert status==0
   c.uc.mem_write(c.symbols['terminal_configuration_values'],data);c.call('terminal_apply_configuration')
   port=3 if mask&1 else 2;rate=115200 if mask&2 else 19200
   wanted={'terminal_port_number':port,'terminal_baud_low':rate&65535,'terminal_baud_high':rate>>16,'terminal_parity':2 if mask&4 else 0,'terminal_data_bits':7 if mask&4 else 8,'terminal_stop_bits':2 if mask&4 else 1,'uart_software_flow':0 if mask&8 else 1,'uart_hardware_flow':0 if mask&8 else 1,'uart_port_rbr':BASES[port-1],'uart_irq_indices':IRQS[port-1],'terminal_irq_vector':IRQS[port-1]+8,'csi_terminal_id':4,'attributes_monochrome':0,'attributes_current':0x1e,'attributes_normal_value':0x1e,'cursor_state_saved_1f70':0x1e,'csi_erase_attribute':0x1e,'render_autowrap':0,'scroll_enabled':0,'terminal_backspace_mode_9058':1}
   for name,value in wanted.items():assert c.get(name,1 if name=='csi_erase_attribute' else 2)==value,(mask,name,c.get(name),value)
   assert c.get('csi_saved_row')==0 and c.get('csi_saved_column')==0,'Opaque PRM live state was applied'
  return 16
 check('actual-CLI-plus-ASM-import-all-category-override-combinations',precedence)
 def skipped():
  c=Import();assert c.parse(b'COM2 19200 HARD')==(0,0);before={k:c.get(k) for k in SERIAL_FIELDS}
  assert c.call('terminal_load_configuration')==0 and {k:c.get(k) for k in SERIAL_FIELDS}==before
  return 1
 check('absent-selector-performs-no-IO-and-retains-CLI-settings',skipped)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual terminal-linked C validation and assembly application, opaque synthetic PRMs, existing CLI parser; interrupts and port IO forbidden. Real DOS loading/IRQ/video tested separately.'}
 (ROOT/'build/terminal/config-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
