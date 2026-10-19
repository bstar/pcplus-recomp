#!/usr/bin/env python3
"""Actual linked parent validator: authored child allocation and callback bounds."""
import hashlib,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/terminal/TERMINAL.EXE';MAP=ROOT/'build/terminal/terminal.map'

def main():
 symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',MAP.read_text(),re.M|re.I)}
 cases=['valid','Z-owner','wrong-PSP','parent-PSP','DS-before-PSP','near-client-wrap','bad-signature','wrong-owner','zero-allocation','physical-overflow','client-outside','client-in-PSP','bad-magic','bad-version','zero-token','wrong-token','callback-in-PSP','callback-after-end','callback-physical-overflow','callback-alias','null-output','output-near-wrap']
 results=[]
 for name in cases:
  image=DosImage(BINARY,MAP);u=image.uc
  psp,parent,ds,offset,token=0x8000,0xff0,0x8200,0x1000,0x1432
  mcb=bytearray(b'M'+struct.pack('<HH',psp,0x800)+b'\0'*11)
  client=[0x5243,3,token,0x20,0x8010]
  output=image.stage_near(b'\xa5'*4)
  if name=='Z-owner':mcb[0]=ord('Z')
  if name=='wrong-PSP':psp=0xff
  if name=='parent-PSP':parent=psp
  if name=='DS-before-PSP':ds=psp-1
  if name=='near-client-wrap':offset=65530
  if name=='bad-signature':mcb[0]=ord('Q')
  if name=='wrong-owner':struct.pack_into('<H',mcb,1,0x1234)
  if name=='zero-allocation':struct.pack_into('<H',mcb,3,0)
  if name=='physical-overflow':struct.pack_into('<H',mcb,3,0xffff)
  if name=='client-outside':ds=0x9000
  if name=='client-in-PSP':ds,offset=0x8000,0x80
  if name=='bad-magic':client[0]=0
  if name=='bad-version':client[1]=2
  if name=='zero-token':token=0
  if name=='wrong-token':client[2]^=1
  if name=='callback-in-PSP':client[3:]=[0x80,0x8000]
  if name=='callback-after-end':client[3:]=[0,0x8800]
  if name=='callback-physical-overflow':client[3:]=[0xffff,0xffff]
  if name=='callback-alias':client[3:]=[offset,ds]
  if name=='null-output':output=0
  if name=='output-near-wrap':output=65534
  u.mem_write(0x7fff0,bytes(mcb));u.mem_write(ds*16+offset,struct.pack('<5H',*client))
  before=bytes(u.mem_read(image.data_base+output,4))
  seg,off=symbols['_aspect_render_client_admit'];return_seg,return_off=symbols['terminal_render_prepare']
  assert return_seg==seg
  stopped=[]
  def stop(machine,address,size,unused):
   if address==image.base+return_seg*16+return_off:stopped.append(True);machine.emu_stop()
  u.hook_add(UC_HOOK_CODE,stop)
  args=[return_off,psp,parent,ds,offset,token,output];sp=image.offset('terminal_stack_top')-14
  u.mem_write(image.data_base+sp,struct.pack('<7H',*args))
  for reg,value in [(UC_X86_REG_CS,image.base_segment+seg),(UC_X86_REG_DS,image.ds),(UC_X86_REG_SS,image.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
  u.emu_start(image.symbols['_aspect_render_client_admit'],0,count=100000)
  expected=0 if name in ('valid','Z-owner') else 10
  assert stopped and u.reg_read(UC_X86_REG_AX)==expected,(name,u.reg_read(UC_X86_REG_AX))
  assert u.reg_read(UC_X86_REG_SP)==sp+2,name
  assert bytes(u.mem_read(image.data_base+output,4))==(struct.pack('<2H',*client[3:]) if not expected else before),name
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,image.ds),(UC_X86_REG_SS,image.ds)]:assert u.reg_read(reg)==value,name
  results.append(dict(case=name,result=expected,passed=True))
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report=dict(passed=True,cases=results,binary_sha256=sha(BINARY),manifest_sha256=sha(ROOT/'build/terminal/manifest.json'),checker_sha256=sha(Path(__file__)),source_sha256=sha(ROOT/'src/aspect/renderer_client.c'),scope='Actual linked parent C validator on synthetic child MCB/client bytes. Near C caller boundary modeled, no product instruction patched; no bridge, parser, child execution or hardware claim.')
 (ROOT/'build/terminal/aspect-render-parent-client-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Parent render client admission:',len(results),'cases passed')
if __name__=='__main__':main()
