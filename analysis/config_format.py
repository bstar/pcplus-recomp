#!/usr/bin/env python3
"""Explicit original-code configuration analysis; never opens installed PRM files.

Reuses retained REA evidence and replays actual overlay3/20 code with declared
synthetic stdio boundaries. Output contains provenance and synthetic hashes only.
"""
import hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_AX
ROOT=Path(__file__).resolve().parents[1]
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
BASE=0x1b84;SIZE=0x4f0
class FatalConfigurationError(Exception):pass

def replay(image,overlay,entry,payload=None,fail_open=False):
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
 u.mem_write(0x10000,image[0x1200:0xe2d0]);start=overlay['relative_load_segment']*16
 pos=overlay['source_file_offset'];u.mem_write(0x10000+start,image[pos:pos+overlay['initialized_bytes']])
 u.mem_write(0x40000,image[153936:153936+60080])
 initial=struct.pack('<5H',0,1,0,1,8)+b'\x55'*(SIZE-10);u.mem_write(0x40000+BASE,initial)
 u.mem_write(0x46000,b'TEST.PRM\0')
 args=[0xf000]+([0x6000] if entry==0xd734 else [])
 for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_SS,0x4000),(UC_X86_REG_SP,0xe000)]:u.reg_write(reg,value)
 u.mem_write(0x4e000,struct.pack('<'+'H'*len(args),*args));calls=[];writes=[];returned=[]
 def string(ptr):
  raw=bytes(u.mem_read(0x40000+ptr,80));return raw.split(b'\0')[0].decode('ascii')
 def hook(uc,at,length,_):
  if at==0x1f000:returned.append(True);uc.emu_stop();return
  if at not in [0x1841a,0x1845a,0x186ac,0x18318,0x1335c]:return
  sp=uc.reg_read(UC_X86_REG_SP);words=struct.unpack('<5H',uc.mem_read(0x40000+sp,10));result=0
  if at==0x1841a:
   mode=string(words[2]);calls.append({'operation':'open','mode':mode,'path':string(words[1])});result=0 if fail_open else 0x7200
  elif at==0x1845a:
   pointer,size,count=words[1:4];requested=size*count;chunk=(payload or b'')[:requested]
   if chunk:uc.mem_write(0x40000+pointer,chunk)
   result=len(chunk)//size if size else 0;calls.append({'operation':'read','destination':pointer,'size':size,'count':count,'returned_elements':result,'synthetic_bytes':len(chunk)})
  elif at==0x186ac:
   pointer,size,count=words[1:4];data=bytes(uc.mem_read(0x40000+pointer,size*count));writes.append(data);result=count
   calls.append({'operation':'write','source':pointer,'size':size,'count':count,'sha256':hashlib.sha256(data).hexdigest()})
  elif at==0x18318:calls.append({'operation':'close'})
  else:
   calls.append({'operation':'fatal','code':words[1],'message':string(words[2])});raise FatalConfigurationError()
  uc.reg_write(UC_X86_REG_AX,result);uc.reg_write(UC_X86_REG_SP,sp+2);uc.reg_write(UC_X86_REG_IP,words[0])
 u.hook_add(UC_HOOK_CODE,hook);fatal=False
 try:u.emu_start(0x10000+entry,0x20000,count=5000)
 except FatalConfigurationError:fatal=True
 assert returned or fatal,'Original code did not terminate within instruction bound'
 return {'calls':calls,'fatal':fatal,'returned':bool(returned)},bytes(u.mem_read(0x40000+BASE,SIZE)),writes,initial

def main():
 image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest=json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text());overlays={o['id']:o for o in manifest['overlays']};results=[]
 result,state,writes,initial=replay(image,overlays[3],0xd60c);assert writes==[initial];results.append({'case':'whole-image-save',**result})
 payload=struct.pack('<5H',7,8,2,1,8)+b'\x6a'*(SIZE-10)
 result,state,writes,initial=replay(image,overlays[3],0xd734,payload);assert state==payload and not writes;results.append({'case':'whole-image-load',**result})
 for payload in [b'',b'\xaa'*7]:
  result,state,writes,initial=replay(image,overlays[3],0xd734,payload)
  assert writes==[payload+initial[len(payload):]];results.append({'case':'zero-element-read-rewrites-current-memory','synthetic_input_bytes':len(payload),**result})
 result,state,writes,initial=replay(image,overlays[3],0xd60c,fail_open=True);assert result['fatal'] and not writes;results.append({'case':'write-open-fatal-error',**result})
 result,state,writes,initial=replay(image,overlays[20],0xf260);assert writes==[initial[:10]];results.append({'case':'serial-prefix-save',**result})
 evidence=[]
 for scope,address in [('pcplus-overlay-anchored-03',0x1d4d0),('pcplus-overlay-anchored-03',0x1d5f8),('pcplus-overlay-anchored-03',0x1d60c),('pcplus-overlay-anchored-03',0x1d647),('pcplus-overlay-anchored-03',0x1d734),('pcplus-overlay-anchored-20',0x1f260),('pcplus-overlay-anchored-20',0x1f05c),('pcplus-overlay-anchored-20',0x1f1fa),('pcplus-main',0x1033e),('pcplus-main',0x10366),('pcplus-main',0x1353d)]:
  p=ROOT/'analysis'/scope/'functions'/(hex(address)+'-asm.json');o=json.loads(json.loads(p.read_text())['content'][0]['text']);evidence.append({'address':hex(address),'context':scope,'evidence_id':o['evidence_id']})
 out=ROOT/'build/config-analysis';out.mkdir(parents=True,exist_ok=True)
 report={'source_sha256':EXPECTED,'configuration_ds_start':BASE,'configuration_bytes':SIZE,'cases':results,'evidence':evidence,'limitations':['Actual original code with explicitly modeled stdio; no real DOS filesystem operations or user configuration read.','Read-failure fallback is demonstrated at caller boundary; short-read memory copying is modeled from the fread contract.','No complete PRM field schema, format-version signature or complete startup/default initializer has been recovered.']}
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('Verified',len(results),'original configuration call-path cases; no installed PRM opened.')
if __name__=='__main__':main()
