#!/usr/bin/env python3
"""Relocate actual CSI code and DS fixtures, then exercise both inline tables.

This source-only regression intentionally moves code and data independently.
It catches original absolute table displacements and indexed-parameter offsets
that a byte-exact flat recovery can accidentally preserve in an OMF build.
"""
from pathlib import Path
import hashlib,json,re,subprocess
from unicorn import UC_HOOK_INTR
from dos_image import DosImage
from check_csi import Csi
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/csi-relocation'

class RelocatedCsi(Csi):
 def __init__(self,binary,mapping):
  DosImage.__init__(self,binary,mapping)
  self.positions=[]
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=ROOT/'reconstruction/ansi/dispatch.asm'
 text=source.read_text()
 # Stack locals may remain numeric; original absolute data references may not.
 for operand in re.findall(r'\[([^\]]+)\]',text):
  assert not re.search(r'0x[0-9a-f]{3,}',operand),operand
 assert '[cs:bx+csi_sgr_table]' in text and '[cs:bx+csi_command_table]' in text
 assert re.search(r'\[(?:bx|si)\+ansi_parameters\]',text), 'indexed SGR data must relocate'
 proof=json.loads((source.parent/'dispatch-provenance.json').read_text())
 flat=OUT/'dispatch.bin'
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(source.parent)+'/',str(source),'-o',str(flat)],check=True)
 assert hashlib.sha256(flat.read_bytes()).hexdigest()==proof['sha256'] and len(flat.read_bytes())==proof['bytes']
 # Use the normal build's authoritative input list so new recovered services
 # participate automatically, rather than duplicating its linker inventory.
 manifest_path=ROOT/'build/csi/manifest.json'
 assert manifest_path.exists(), 'Run standalone/build_csi.py before the relocation regression'
 manifest=json.loads(manifest_path.read_text())
 sources=[ROOT/name for name in manifest['sources'] if name.endswith('.asm')]
 assert source in sources and ROOT/'standalone/csi_host.asm' in sources
 objects=[]
 for index,item in enumerate(sources):
  obj=OUT/f'unit-{index}.obj';objects.append(str(obj));options=[]
  if item.parent.parent==ROOT/'reconstruction':
   options=['-D'+item.parent.name.upper()+'_OMF']
  subprocess.run(['nasm','-f','obj',*options,'-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(ROOT/'reconstruction/ansi')+'/',str(item),'-o',str(obj)],check=True)
 results=[]
 for code_pad,data_pad in [(0,0),(0x137,0x251),(0x2137,0x1234)]:
  case=OUT/f'{code_pad:x}-{data_pad:x}';case.mkdir(exist_ok=True)
  padding=case/'padding.asm'
  padding.write_text(f'BITS 16\nSEGMENT _TEXT public class=CODE use16\ntimes {code_pad} db 0xcc\nSEGMENT _DATA public align=16 class=DATA use16\ntimes {data_pad} db 0xa5\n')
  padobj=case/'padding.obj'
  subprocess.run(['nasm','-f','obj',str(padding),'-o',str(padobj)],check=True)
  binary=case/'CSI.EXE';mapping=case/'csi.map'
  subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(mapping),'name',str(binary),'file',','.join([str(padobj)]+objects)],check=True)
  c=RelocatedCsi(binary,mapping)
  for seq,want in [(b'[0;31;42m',0x24),(b'[0;34;43;1;5m',0xe9),(b'[0;35;46m',0x35),(b'[0;37;40m',7)]:
   c.sequence(seq);assert c.get('attributes_current')==want,(code_pad,data_pad,seq,hex(c.get('attributes_current')),hex(want))
  for seq,want in [(b'[10;20H',(9,19)),(b'[3C',(9,22)),(b'[2A',(7,22)),(b'[H',(0,0))]:
   assert c.sequence(seq)==want,(code_pad,data_pad,seq,want)
  # Device-string immediate pointers must follow DS too.
  c.put('csi_terminal_id',4);c.sequence(b'[>0c')
  assert bytes(c.uc.mem_read(c.symbols['csi_output_buffer'],c.get('csi_output_length')))==b'\x1b[>1;10;0c'
  result={'code_padding':code_pad,'data_padding':data_pad,'dispatcher_offset':c.symbols['ansi_dispatch_command']-c.base,'parameter_offset':c.offset('ansi_parameters'),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'passed':True}
  results.append(result);print('relocation',hex(code_pad),hex(data_pad),'passed',flush=True)
 assert len({r['dispatcher_offset'] for r in results})==3
 assert len({r['parameter_offset'] for r in results})==3
 result={'passed':True,'flat_sha256':proof['sha256'],'cases':results,'scope':'Actual linked dispatcher jump tables, indexed SGR data, cursor commands and immediate DS string pointers at independently shifted code/data offsets; no original binary required.'}
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 return result
if __name__=='__main__':main()
