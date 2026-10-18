#!/usr/bin/env python3
"""Actual linked nine-word context reader, retained identity and startup owner."""
import hashlib,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_SP,UC_X86_REG_SS,UC_X86_REG_ES
from check_directory_live import Live,ROOT,BINARY,MAP,text,word,plan_expected
MAX_STACK=[0]
class Context(Live):
 def __init__(self):
  self.wrong_tag=None
  super().__init__();self.context=self.offset('terminal_directory_context')
  self.uc.mem_write(self.data_base+self.context,b'\xce'*496)
  self.uc.hook_add(UC_HOOK_CODE,self.stack)
 def stack(self,u,address,size,_):
  assert u.reg_read(UC_X86_REG_SS)==self.ds
  used=self.offset('terminal_stack_top')-u.reg_read(UC_X86_REG_SP)
  assert 0<=used<8192,'Context reader exceeds terminal stack budget'
  MAX_STACK[0]=max(MAX_STACK[0],used)
 def boundary(self,u,address,size,unused):
  selection=None
  if address==self.symbols['_directory_dos_read']:
   words=struct.unpack('<5H',u.mem_read(self.data_base+u.reg_read(UC_X86_REG_SP),10));selection=words[3]
  super().boundary(u,address,size,unused)
  if selection is not None and self.wrong_tag is not None and not self.directory_status:u.mem_write(self.data_base+selection,struct.pack('<H',self.wrong_tag))
 def context_bytes(self):return bytes(self.uc.mem_read(self.data_base+self.context,496))
 def outputs(self):return super().outputs()+(self.context_bytes(),)
 def capture(self,args=None):
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  return self.call('_directory_live_read_context',self.arguments()+[self.context] if args is None else args,limit=1000000)
 def matches(self,args=None):
  before=self.outputs();calls=list(self.calls)
  result=self.call('_directory_live_context_matches',[self.context,self.prm_path,self.directory_path,self.entry,self.codes] if args is None else args,limit=100000)
  assert self.outputs()==before and self.calls==calls
  return result
 def expected_context(self):
  return struct.pack('<H',self.entry)+self.header+self.record+struct.pack('<H',self.codes)+b'SYN.PRM'+bytes(57)+b'SYN.DIR'+bytes(57)
def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 count=0
 for entry in range(1,201):
  for codes in (0,1):
   c=Context();c.entry=entry;c.codes=codes
   c.header=b''.join(bytes([65+(entry+i)%26,0])+bytes([entry%256])*23 for i in range(10))
   c.record=text(c.record,25,21,b'A55b');c.poison()
   assert c.capture()==0 and c.context_bytes()==c.expected_context() and c.matches()==1
   assert [v[0] for v in c.calls]==['prm','directory']
   count+=1
 done('all200-entries-both-code-modes-raw250-byte-header-record-and-exact-path-padding',count)
 c=Context();c.poison();assert c.capture()==0;original=c.context_bytes()
 # Change the modeled external directory AFTER capture; identity matching and
 # use of context never access it. Legacy input deliberately needs code A/B.
 c.header=b'A\0'.ljust(25,b'\0')+b'B\0'.ljust(25,b'\0')+bytes(200)
 c.record=text(c.record,25,21,b'A55b');c.codes=1;assert c.capture()==0
 retained=c.context_bytes();calls=list(c.calls);c.header=b'X'*250;c.record=b'X'*114
 c.poison();c.uc.reg_write(UC_X86_REG_ES,c.ds)
 # Stage raw PRM in a caller-owned stack region as supported by DosImage.
 ptr=c.stage_near(c.prm)
 assert c.call('_directory_live_decode',[ptr,c.context,1,c.serial,c.modem,c.plan,c.result],limit=1000000)==0
 assert c.outputs()[2]==plan_expected(1,retained[252:366],1,b'A55B')
 assert c.context_bytes()==retained and c.calls==calls
 done('retained-selection-redecode-after-external-header-and-record-change-with-no-reread',1)
 # Logical identity accepts case only, and intentionally refuses path aliases.
 c=Context();assert c.capture()==0
 for value,want in [(b'syn.prm',1),(b'OTHER.PRM',0),(b'.\\SYN.PRM',0),(b'C:SYN.PRM',0)]:
  c.uc.mem_write(c.data_base+c.prm_path,value+b'\0');assert c.matches()==want
 c.uc.mem_write(c.data_base+c.prm_path,b'SYN.PRM\0')
 for value,want in [(b'syn.dir',1),(b'OTHER.DIR',0),(b'.\\SYN.DIR',0)]:
  c.uc.mem_write(c.data_base+c.directory_path,value+b'\0');assert c.matches()==want
 c.uc.mem_write(c.data_base+c.directory_path,b'SYN.DIR\0')
 normal=[c.context,c.prm_path,c.directory_path,c.entry,c.codes]
 for index,value in [(0,0),(0,0xff00),(1,0),(1,0xffff),(2,0),(2,0xffff),(3,0),(3,2),(3,201),(4,1),(4,2)]:
  args=normal.copy();args[index]=value;assert c.matches(args)==0
 for at in (368,432):
  c.uc.mem_write(c.data_base+c.context,original);c.uc.mem_write(c.data_base+c.context+at,b'X'*64);assert c.matches()==0
 done('case-insensitive-logical-identity-invalid-strings-and-no-dot-drive-alias-claim',20)
 count=0
 for kind,values in [('prm',range(1,7)),('directory',range(1,6))]:
  for status in values:
   c=Context();setattr(c,kind+'_status',status);c.poison();before=c.outputs();assert c.capture()==(2 if kind=='prm' else 3) and c.outputs()==before;count+=1
 for at,value in [(0,4),(0x198,2),(0x194,5)]:
  c=Context();c.prm=word(c.prm,at,value);c.poison();before=c.outputs();assert c.capture()==4 and c.outputs()==before;count+=1
 for at,value in [(0x68,5),(0x33,1),(0x4a,2),(0x49,5)]:
  c=Context();r=bytearray(c.record);r[at]=value;c.record=bytes(r);c.poison();before=c.outputs();assert c.capture()!=0 and c.outputs()==before;count+=1
 for tag in (0,2,201,65535):
  c=Context();c.wrong_tag=tag;c.poison();before=c.outputs();assert c.capture()==6 and c.outputs()==before;count+=1
 done('all-file-failure-statuses-semantic-failures-and-wrong-selection-tags-four-output-atomic',count)
 count=0
 for target in (0xff00,0xffff):
  c=Context();args=c.arguments()+[target];before=c.outputs();assert c.capture(args)==1 and c.outputs()==before and not c.calls;count+=1
 for index in (0,1,4,5,6,7):
  c=Context();args=c.arguments()+[c.context];args[8]=args[index];before=c.outputs();assert c.capture(args)==1 and c.outputs()==before and not c.calls;count+=1
 for delta in (-495,-1,1,39,367):
  c=Context();args=c.arguments()+[c.serial+delta];before=c.outputs();assert c.capture(args)==1 and c.outputs()==before and not c.calls;count+=1
 c=Context();args=c.arguments()+[0];assert c.capture(args)==0 and c.context_bytes()==b'\xce'*496
 done('context-extent-all-input-output-result-overlaps-and-optional-context-compatibility',count+1)
 # Input paths may alias other plans as in the original API. Capture them before
 # those plans commit; context receives original path spellings, not plan data.
 c=Context();c.uc.mem_write(c.data_base+c.serial,b'SYN.PRM\0');c.uc.mem_write(c.data_base+c.modem,b'SYN.DIR\0')
 c.prm_path=c.serial;c.directory_path=c.modem
 assert c.capture()==0 and c.context_bytes()==c.expected_context()
 done('path-aliases-ordinary-plans-captured-before-four-plan-commit',1)
 for mask in range(16):
  c=Context();assert c.parse(b'@SYN.PRM /E:SYN.DIR /N:17'+b' '+b' '.join(token for bit,token in [(1,b'COM3'),(2,b'115200'),(4,b'8N1'),(8,b'NONE')] if mask&bit))==(0,0)
  c.entry=17;c.poison();assert c.call('terminal_load_configuration',limit=1000000)==0
  assert c.get('terminal_directory_context_valid')==1 and c.context_bytes()==c.expected_context()
  # Failed reload makes old bytes inaccessible as valid; successful non-DIR
  # startup also clears the flag without publishing an old selection.
  retained=c.context_bytes();c.prm_status=2
  assert c.call('terminal_load_configuration',limit=1000000)==8 and c.get('terminal_directory_context_valid')==0 and c.context_bytes()==retained
  c.prm_status=0;assert c.parse(b'@SYN.PRM')==(0,0)
  assert c.call('terminal_load_configuration',limit=1000000)==0 and c.get('terminal_directory_context_valid')==0 and c.context_bytes()==retained
 done('actual-startup-nine-word-ABI-all-CLI-overrides-validity-failed-and-non-directory-reloads',48)
 macros={k:int(v) for k,v in re.findall(r'^%define (DLC_\w+) (\d+)$',(ROOT/'src/directory/directory_live.inc').read_text(),re.M)}
 assert macros==dict(DLC_ENTRY=0,DLC_HEADER=2,DLC_RECORD=252,DLC_CODES=366,DLC_PRM_PATH=368,DLC_DIRECTORY_PATH=432,DLC_SIZE=496)
 done('C-size-offset-assertions-agree-with-NASM-retained-context-layout',1)
 sources=['src/directory/directory_live.c','src/directory/directory_live.h','src/directory/directory_live.inc','src/terminal/configuration.asm','standalone/check_directory_context.py','standalone/check_directory_live.py','standalone/dos_image.py']
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,maximum_CPU_call_stack_bytes=MAX_STACK[0],sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},scope='Actual linked retained-context reader and startup assembly; only PRM/directory I/O boundaries modeled. Pure matches/redecode use no I/O. Every interrupt/IN/OUT forbidden. Preserves raw headers and lexical request identity, not canonical namespace locking or live setup/commit.')
 (ROOT/'build/terminal/directory-context-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
