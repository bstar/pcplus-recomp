#!/usr/bin/env python3
"""Execute linked one-read startup display capture; DOS/file effects modeled.
Raw preferences remain separate from BIOS, canonical geometry and live selection.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EFLAGS,UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES
import check_startup_import as startup
import check_directory_live as directory
from check_directory_context import Context
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
OFFSETS=(0x1c2,0x1c8,0x1ca,0x4ec)
def patch(raw,values):
 raw=bytearray(raw)
 for at,value in zip(OFFSETS,values):struct.pack_into('<H',raw,at,value)
 return bytes(raw)
def expected(raw):return b''.join(raw[at:at+2] for at in OFFSETS)
def new(kind):
 m=Context() if kind=='directory' else startup.Startup()
 raw=bytearray(m.prm if kind=='directory' else m.payload)
 struct.pack_into('<HH',raw,0x4e4,8,4)
 if kind=='directory':m.prm=bytes(raw)
 else:m.payload=bytes(raw)
 return m
def capture(m):return bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8)),m.get('_terminal_display_preferences_ready')
def seed(m):
 m.uc.mem_write(m.symbols['_terminal_display_preferences'],b'OLDPREF!');m.put('_terminal_display_preferences_ready',0x5aa5)
def args(m,kind):
 prefs=m.offset('_terminal_transfer_preferences')
 return [m.path,m.serial,m.modem if kind=='modem' else 0,prefs,m.result] if kind!='directory' else m.arguments()+[m.context,prefs]
def invoke(m,kind,arguments=None):
 return m.call('_terminal_directory_preferences_read' if kind=='directory' else '_terminal_preferences_read',args(m,kind) if arguments is None else arguments,limit=3000000)
def planes(m):
 return {n:bytes(m.uc.mem_read(m.symbols[n],size)) for n,size in [('erase_shadow_cells',8192),('screen_attribute_cells',4096),('erase_attribute_values',4096),('terminal_history_buffer',63000)]}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();mfest=json.loads((binary.parent/'manifest.json').read_text());assert mfest['experimental_display_preferences'] and sha(binary)==mfest['binary_sha256']
 for path,h in mfest['sources'].items():assert sha(ROOT/path)==h,path
 startup.BINARY=directory.BINARY=binary;startup.MAP=directory.MAP=binary.parent/'terminal.map'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[]
 def done(name,count):cases.append(dict(case=name,inputs=count,passed=True));print('PASS',name,count,flush=True)
 count=0
 for kind in ('serial','modem','directory'):
  for field in range(4):
   for value in (0,1,4,25,28,43,50,127,128,0x8000,0xffff):
    m=new(kind);raw=m.prm if kind=='directory' else m.payload
    values=[0xffff,4,43,0x12];values[field]=value;raw=patch(raw,values)
    if kind=='directory':m.prm=raw
    else:m.payload=raw
    seed(m);before_planes=planes(m);before=capture(m);at_publish=[]
    def boundary(u,address,size,data):
     if address==m.symbols['_hook_baseline_publish']:assert capture(m)==before;at_publish.append(True)
    hook=m.uc.hook_add(UC_HOOK_CODE,boundary)
    try:assert invoke(m,kind)==0,(kind,field,value)
    finally:m.uc.hook_del(hook)
    assert at_publish==[True] and capture(m)==(expected(raw),1)
    assert planes(m)==before_planes and not getattr(m,'tx',[])
    assert len(m.calls)==(2 if kind=='directory' else 1)
    count+=1
 done('single-PRM-serial-modem-and-directory-publication-after-baseline-with-raw-words',count)
 count=0
 for kind in ('modem','directory'):
  for fault in ('io','serial','modem','transfer','mouse','baseline'):
   m=new(kind);seed(m);before=capture(m)
   if fault=='io':
    if kind=='directory':m.prm_status=1
    else:m.load_status=1
   elif fault!='baseline':
    at,value={'serial':(0,8),'modem':(0xe,2),'transfer':(0x31c,0x4f43),'mouse':(0x4e4,0)}[fault]
    raw=bytearray(m.prm if kind=='directory' else m.payload);struct.pack_into('<H',raw,at,value)
    if fault=='transfer':raw[0x31c:0x320]=b'CON\0'
    if kind=='directory':m.prm=bytes(raw)
    else:m.payload=bytes(raw)
   reached=[]
   def failure(u,address,size,data):
    if fault=='baseline' and address==m.symbols['_hook_baseline_publish']:
     reached.append(True);u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)&~0x200)
   hook=m.uc.hook_add(UC_HOOK_CODE,failure)
   try:status=invoke(m,kind)
   finally:m.uc.hook_del(hook)
   assert status and capture(m)==before,(kind,fault,status)
   if fault=='baseline':assert reached==[True] and status==16
   count+=1
 done('read-decode-mouse-and-late-baseline-refusals-retain-previous-display-capture',count)
 count=0
 for kind in ('serial','modem','directory'):
  for symbol in ('_terminal_display_preferences','_terminal_display_preferences_ready'):
   positions=(0,1,2,3,4) if kind!='directory' else range(10)
   for i in positions:
    m=new(kind);seed(m);before=capture(m);arguments=args(m,kind);arguments[i]=m.offset(symbol)
    # Directory entry/codes are values, rather than pointers.
    if kind=='directory' and i in (2,3):continue
    assert invoke(m,kind,arguments)!=0 and capture(m)==before and not m.calls
    count+=1
 done('capture-and-readiness-aliases-refuse-before-IO',count)
 m=startup.Startup();seed(m);before=capture(m);ip,cs=struct.unpack_from('<HH',binary.read_bytes(),0x14);u=m.uc;stopped=[]
 def stop(u,address,size,data):
  if address==m.symbols['_terminal_mouse_bootstrap']:stopped.append(True);u.emu_stop()
 hook=u.hook_add(UC_HOOK_CODE,stop)
 for reg,value in [(UC_X86_REG_CS,m.base_segment+cs),(UC_X86_REG_DS,0x2000),(UC_X86_REG_SS,0x2000),(UC_X86_REG_ES,0x2000)]:u.reg_write(reg,value)
 try:u.emu_start((m.base_segment+cs)*16+ip,0,count=100)
 finally:u.hook_del(hook)
 assert stopped and capture(m)==(before[0],0)
 done('actual-MZ-entry-clears-readiness-before-startup-owners',1)
 for path,h in mfest['sources'].items():assert sha(ROOT/path)==h,path
 result=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),cases=cases,checker_sha256=sha(Path(__file__)),scope=__doc__+' Actual C/ASM public startup readers, decoder/validators, mouse staging and baseline publication execute. File/DOS effects modeled; late publish fault clears IF at its real boundary. No function/instruction replacement, geometry apply, normal keys, online/BBS/physical or deployment acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
