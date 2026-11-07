#!/usr/bin/env python3
"""Opt-in actual parent/VM ALARM through live native receive and WHEN service."""
import inspect,json,sys,struct
from pathlib import Path
import test_aspect_pause_when_dos as pause
import test_aspect_keys_dos as keys
ROOT=keys.ROOT
PARENT=ROOT/'build/terminal-alarm-policy-first-20261106'
CHILD=ROOT/'build/aspect-alarm-vm-first-20261106'

def main():
 original=pause.definitions
 original_prm=keys.renderer.prm
 def configured_prm():
  settings=bytearray(original_prm())
  for off,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,4),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',settings,off,value)
  return bytes(settings)
 keys.renderer.prm=configured_prm
 observer_text=inspect.getsource(keys.renderer.observer)
 old=" cmp word [PROGRAM_KIND],4\n jne .chain\n"
 assert observer_text.count(old)==1
 observer_text=observer_text.replace(old,"")
 old=" call far [cs:old21]\n save\n push cs"
 new=" call far [cs:old21]\n save\n mov bp,sp\n test word [ss:bp+18],1\n jz .exec_return_recorded\n mov ax,[ss:bp+16]\n mov [cs:exit_code],ax\n.exec_return_recorded:\n push cs"
 assert observer_text.count(old)==1
 observer_text=observer_text.replace(old,new)
 exec(compile(observer_text,str(Path(__file__)),'exec'),keys.renderer.__dict__)
 # The shared peer gained a software-flow block before line.append. Retain
 # that block and insert the existing READY/END hooks at the exact append.
 adapter_text=inspect.getsource(keys.adapter)
 adapter_text=adapter_text.replace("old='if online:\\n       line.append(byte)'", "old='       line.append(byte)'")
 exec(compile(adapter_text,str(Path(__file__)),'exec'),keys.__dict__)
 def definitions():
  rows=original()
  rows=[r for r in rows if r['name']=='pause-when-plain-terminal']
  for row in rows:
   row['name']=row['name'].replace('pause-when','alarm-vm')
   row['source']=row['source'].replace('pause 4','alarm 4')
  return rows
 # Reuse the frozen peer, real native renderer and passive observer. Only
 # declared binary/map paths and authored source definitions differ.
 text=inspect.getsource(keys.main)
 old="source=inspect.getsource(renderer.main)"
 replacement="source=inspect.getsource(renderer.main).replace(\"ROOT/'build/terminal/TERMINAL.EXE'\",\"ROOT/'build/terminal-alarm-policy-first-20261106/TERMINAL.EXE'\").replace(\"ROOT/'build/aspect-runner/ASPECT.EXE'\",\"ROOT/'build/aspect-alarm-vm-first-20261106/ASPECT.EXE'\")"
 assert text.count(old)==1;text=text.replace(old,replacement)
 exec(compile(text,str(Path(__file__)), 'exec'),keys.__dict__)
 scope=dict(pause.__dict__);scope['definitions']=definitions;scope['BASE']=ROOT/'build/aspect-alarm-vm-dos'
 text=inspect.getsource(pause.main).replace("ROOT / 'build/terminal/terminal.map'","ROOT / 'build/terminal-alarm-policy-first-20261106/terminal.map'").replace("ROOT / 'build/aspect-runner/ASPECT.map'","ROOT / 'build/aspect-alarm-vm-first-20261106/ASPECT.map'")
 exec(compile(text,str(Path(__file__)),'exec'),scope);scope['main']()
 report=ROOT/'build/aspect-alarm-vm-dos'/sys.argv[sys.argv.index('--label')+1]/'pause-checks.json'
 assert json.loads(report.read_text())['passed'], 'ALARM VM acceptance remains unproven; inspect preserved captures'
if __name__=='__main__':main()
