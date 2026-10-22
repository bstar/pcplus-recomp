#!/usr/bin/env python3
"""Execute recovered Alt-Z and real keyboard code; window/device calls are modeled."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
CODE,DATA,STOP=0x10000,0x30000,0x1f000
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def build(out):
 out.mkdir(parents=True,exist_ok=True);include=str(ROOT/'reconstruction/uart')+'/'
 source=ROOT/'reconstruction/script_menu/window.asm';proof=json.loads(source.with_name('provenance.json').read_text())
 subprocess.run(['nasm','-fbin','-I',include,str(source),'-o',str(out/'window.bin')],check=True)
 subprocess.run(['nasm','-fobj','-DLOCAL_WINDOW_OMF','-I',include,str(source),'-o',str(out/'window.obj')],check=True)
 assert sha(out/'window.bin')==proof['sha256'] and (out/'window.bin').stat().st_size==176
 regions=[(0x56fe,(out/'window.bin').read_bytes())]
 keyboard=ROOT/'reconstruction/keyboard/core.asm'
 kproof=json.loads(keyboard.with_name('provenance.json').read_text())
 for i,region in enumerate(kproof['ranges']):
  target=out/f'keyboard-{i}.bin'
  subprocess.run(['nasm','-fbin',f'-DKEYBOARD_REGION={i}','-I',include,str(keyboard),'-o',str(target)],check=True)
  assert sha(target)==region['sha256'] and target.stat().st_size==region['size']
  regions.append((int(region['start'],16),target.read_bytes()))
 for name,source,at,flags in [('dispatch','reconstruction/keyboard_mapping/dispatch.asm',0x138a,[]),
   ('when','src/aspect/when.asm',0x4de9,['-DASPECT_WHEN_FLAT','-DASPECT_WHEN_UNIT=4'])]:
  target=out/(name+'.bin')
  subprocess.run(['nasm','-fbin','-I',include,*flags,str(ROOT/source),'-o',str(target)],check=True)
  regions.append((at,target.read_bytes()))
 return proof,regions

def exercise(regions,raw,hook=None,mode=0,delay=0,debug=False,original=None,via_when=False):
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
 for at,blob in regions:
  if original:assert blob==original[0x1200+at:0x1200+at+len(blob)]
  u.mem_write(CODE+at,blob if original is None else original[0x1200+at:0x1200+at+len(blob)])
 for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),
   (UC_X86_REG_SP,0x8800),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),
   (UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x4444),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
 put=lambda at,value:u.mem_write(DATA+at,struct.pack('<H',value))
 word=lambda at:struct.unpack('<H',u.mem_read(DATA+at,2))[0]
 for at,value in [(0x397a,0xffff),(0x1f64,0x17),(0x1f66,0x1f),(0x232a,0x2468),
   (0x2328,0x1357),(0x1d6e,int(hook is not None)),(0x1d70,hook or 0),(0x7ac0,mode)]:put(at,value)
 u.mem_write(DATA+0x8800,struct.pack('<H',STOP-CODE))
 frame=bytes((i*31+7)&255 for i in range(4000));u.mem_write(0xb8000,frame)
 keys=([0x2c00] if via_when else [])+([0x2c00] if debug else [])+[raw,0x2d00];events=[];reads=[];polls=0;done=[]
 # This exact scan2C slot is independently bound to original overlay32 data.
 put(0x44e0+0x2c*2,0x56fe)
 if original is not None:assert original[0x29e88:0x29e8a]==struct.pack('<H',0x56fe)
 # Callee-clean sizes follow the native service contracts, distinct from the
 # caller-clean save/format/status/restore calls visible in recovered56FE.
 calls={0x3fc7:('save',0,1),0x4056:('draw',6,3),0x780e:('keyboard-select',2,1),
   0x6bf0:('write',6,3),0x75e8:('format',0,4),0x3226:('status',0,1),
   0x4015:('restore',0,3),0x57ae:('debug',0,0)}
 if via_when:calls.update({0x0dde:('host',0,0),0x2f78:('cursor',0,1),0x2fb8:('refresh',0,0)})
 def boundary(machine,address,size,_):
  if address==STOP:done.append(True);machine.emu_stop();return
  at=address-CODE
  if at not in calls:return
  name,clean,count=calls[at];sp=machine.reg_read(UC_X86_REG_SP)
  words=struct.unpack('<'+'H'*(count+1),machine.mem_read(DATA+sp,2*(count+1)))
  events.append((name,list(words[1:])))
  if name not in ('host',):assert word(0x397a)==0x29
  if name=='save':
   assert words[1:]==(0x32b2,);assert bytes(machine.mem_read(0xb8000,4000))==frame
   machine.reg_write(UC_X86_REG_AX,0x3456);machine.reg_write(UC_X86_REG_DX,0x4567)
  elif name=='draw':
   assert words[1:]==(0x17,0x44e,0x201);machine.mem_write(0xb8000,b'\x58\x17'*2000)
  elif name=='keyboard-select':assert words[1:]==(0x232c,)
  elif name=='write':assert words[1:]==(0x2468,0x1f,0x1536)
  elif name=='format':assert words[1:]==(0x154c,0x17,0x4eb6,hook if hook<128 else hook|0xff00)
  elif name=='status':assert words[1:]==(0x1357,)
  elif name=='restore':
   assert words[1:]==(0x32b2,0x3456,0x4567);machine.mem_write(0xb8000,frame)
  machine.reg_write(UC_X86_REG_SP,sp+2+clean);machine.reg_write(UC_X86_REG_IP,words[0])
 def interrupt(machine,number,_):
  nonlocal polls
  assert number==0x16,number
  function=machine.reg_read(UC_X86_REG_AX)>>8
  assert function in (mode,mode+1),function
  if function==mode:
   assert keys;value=keys.pop(0);reads.append(value);machine.reg_write(UC_X86_REG_AX,value)
  else:
   polls+=1;ready=polls>delay
   flags=machine.reg_read(UC_X86_REG_EFLAGS)
   machine.reg_write(UC_X86_REG_EFLAGS,(flags&~0x40) if ready else flags|0x40)
   machine.reg_write(UC_X86_REG_AX,keys[0] if ready else 0x7777)
 u.hook_add(UC_HOOK_CODE,boundary);u.hook_add(UC_HOOK_INTR,interrupt)
 u.emu_start(CODE+(0x4de9 if via_when else 0x56fe),0,count=250000)
 assert done,'native window failed to return'
 low=raw&255
 retained=low in (0,0xe0,0x1c,0x1d,0x1f) or (hook is not None and hook<128 and low==hook)
 assert keys==([raw,0x2d00] if retained else [0x2d00]),(hex(raw),hook,keys)
 assert reads==([0x2c00] if via_when else [])+([0x2c00] if debug else [])+([] if retained else [raw])
 assert [name for name,_ in events]==(['host'] if via_when else [])+['save','draw','keyboard-select','write']+(['format'] if hook is not None else [])+['status']+(['debug'] if debug else [])+['restore']+(['cursor','refresh'] if via_when else [])
 assert [u.reg_read(reg) for reg in (UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES)]==[0x8802,0xbabe,0x1234,0x5678,0x3000,0x3000,0x4444]
 assert bytes(u.mem_read(0xb8000,4000))==frame and polls>delay
 if via_when:assert word(0xcffa)==0x2c and u.reg_read(UC_X86_REG_AX)==0
 return dict(raw=raw,hook=hook,mode=mode,empty_polls=delay,debug=debug,via_when=via_when,retained=retained,reads=reads,events=events)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true');a=p.parse_args()
 out=ROOT/'build/aspect-local-window';proof,regions=build(out);original=None
 if a.original:
  original=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
  assert hashlib.sha256(original).hexdigest()==proof['source_sha256']
 cases=[];comparisons=0
 for mode in (0,16):
  for hook in (None,0x61,0x80,0xff):
   for low in range(256):
    raw=0x1e00|low
    # Alt-Z interception is a separate two-key case below.
    case=exercise(regions,raw,hook,mode);cases.append(case)
    if original is not None:
     assert exercise(regions,raw,hook,mode,original=original)==case;comparisons+=1
  for raw,delay,debug in [(0x4800,0,False),(0,0,False),(0x1e61,3000,False),(0x1e61,0,True)]:
   case=exercise(regions,raw,mode=mode,delay=delay,debug=debug);cases.append(case)
   if original is not None:
    assert exercise(regions,raw,mode=mode,delay=delay,debug=debug,original=original)==case;comparisons+=1
  for raw in (0x1e61,0x4800,0x1b,0x2b1c):
   case=exercise(regions,raw,mode=mode,via_when=True);cases.append(case)
   if original is not None:
    assert exercise(regions,raw,mode=mode,via_when=True,original=original)==case;comparisons+=1
 sources=['reconstruction/script_menu/window.asm','reconstruction/script_menu/provenance.json',
  'reconstruction/keyboard/core.asm','reconstruction/keyboard/provenance.json','reconstruction/uart/encodings.inc',
  'standalone/check_aspect_local_window.py','reconstruction/keyboard_mapping/dispatch.asm',
  'reconstruction/keyboard_mapping/provenance.json','src/aspect/when.asm']
 result=dict(passed=True,cases=len(cases),original_comparisons=comparisons,window_sha256=sha(out/'window.bin'),
  sources={name:sha(ROOT/name) for name in sources},cases_sha256=hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest(),
  scope='Recovered176-byte Alt-Z body plus231 recovered keyboard bytes in8086 CPU replay. All low-byte values, hook sign extension, both BIOS modes, delayed input and repeated Alt-Z dispatch execute actual instructions. Eight composed cases enter native WHEN4DE9 and actual1604 dispatcher through the selected original Alt-Z table slot. BIOS and window/status/debug/host callbacks are modeled; frame restoration and callback argument/cleanup contracts are checked. No actual DOS/UI integration, serial continuity or physical acceptance.')
 leaf='original-results.json' if a.original else 'cpu-results.json'
 (out/leaf).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
