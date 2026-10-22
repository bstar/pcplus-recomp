#!/usr/bin/env python3
"""Opt-in original dispatcher replay with modeled recorder/serial/UI callees.

No analysis carrier, complete DOS application, BIOS input or UART is executed.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from check_ansi_freeze import load_image
DIGEST='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
DATA=0x1fb70

def replay(image,key,recording,binding=None):
 u=load_image(image)
 for off,value in [(0xcffa,key),(0x373c,recording),(0x1d6e,0),(0x1d1a,0),(0x1d74,0),(0x1d68,0)]:
  u.mem_write(DATA+off,struct.pack('<H',value))
 if binding is not None:u.mem_write(DATA+0x3720,binding+b'\0')
 u.mem_write(DATA+0xe000,struct.pack('<H',0xeff0));u.reg_write(UC_X86_REG_SP,0xe000);u.reg_write(UC_X86_REG_BP,0xbeef)
 events=[];returned=False
 def boundary(machine,address,size,ignored):
  nonlocal returned
  if address==0x1eff0:returned=True;machine.emu_stop();return
  # Serial/delay pop their argument. Display/status use caller cleanup.
  cleanup={0x1ab0b:2,0x16b72:2,0x1badb:0,0x12f78:0,0x12fb8:0,0x10e4e:0,0x10ca2:0,0x10610:0}.get(address)
  if cleanup is None:return
  sp=machine.reg_read(UC_X86_REG_SP);ip,arg=struct.unpack('<HH',machine.mem_read(DATA+sp,4))
  if address==0x1ab0b:events.append(['serial_service',arg])
  elif address==0x1badb:events.append(['recorder',struct.unpack('<H',machine.mem_read(DATA+0xcffa,2))[0]])
  machine.reg_write(UC_X86_REG_SP,sp+2+cleanup);machine.reg_write(UC_X86_REG_IP,ip)
 u.hook_add(UC_HOOK_CODE,boundary);u.emu_start(0x11604,0,count=20000)
 assert returned,(key,recording,events,'instruction budget')
 assert u.reg_read(UC_X86_REG_SP)==0xe002 and u.reg_read(UC_X86_REG_BP)==0xbeef
 assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x1fb7
 return events

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 output=a.output.resolve();assert output.is_relative_to(ROOT/'build') and not output.exists()
 image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(image).hexdigest()==DIGEST
 cases=[]
 for mode in (0,1):
  for key in range(32,256):
   events=replay(image,key,mode);expected=[['serial_service',key]]
   if mode and key<128:expected.append(['recorder',key])
   assert events==expected,(key,mode,events,expected)
   cases.append(dict(key=key,recording=mode,events=events))
  for binding in (b'A',b'X\xffY',b'^M~'):
   events=replay(image,13,mode,binding);expected=[['serial_service',0 if c==255 else c] for c in binding]
   if mode:expected.append(['recorder',13])
   assert events==expected,(mode,binding,events,expected)
   cases.append(dict(key=13,binding_hex=binding.hex(),recording=mode,events=events))
 header=struct.unpack_from('<14H',image);units=[]
 for entry,length in [(0x1604,0x1a75-0x1604),(0xa62,41)]:
  offset=header[4]*16+entry;units.append(dict(relative_address=hex(entry),file_offset=offset,bytes=length,sha256=hashlib.sha256(image[offset:offset+length]).hexdigest()))
 report=dict(passed=True,original_cases=len(cases),cases=cases,source_sha256=DIGEST,units=units,
  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  loader_sha256=hashlib.sha256((ROOT/'reconstruction/check_ansi_freeze.py').read_bytes()).hexdigest(),
  manifest_sha256=hashlib.sha256((ROOT/'analysis/pcplus-overlays/manifest.json').read_bytes()).hexdigest(),scope=__doc__,
  conclusions=['Literal keys80h..FFh reach serial service but skip recorder tap.','CR binding bytes reach serial service before recorder receives key000Dh.','BindingFF becomes serial-service NUL; caret/pause bytes remain literal.','Recorder tap is not a byte-by-byte serial-output observer.'],
  limitations=['Synthetic normalized key words; no physical BIOS input provenance.','Recorder/serial/UI services modeled; no actual UART or generated script replay.','Only literal20h..FFh and three CR bindings tested; extended/function keys remain open.'])
 output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(passed=True,original_cases=len(cases))))
if __name__=='__main__':main()
