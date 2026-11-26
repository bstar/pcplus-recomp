#!/usr/bin/env python3
"""Source-only native local-screen bank with explicit resident ABI adapters."""
import hashlib
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ALIASES={
 'aspect_string_bounded_integer':'screen_bounded_integer',
 'aspect_string_byte_operand':'screen_byte_operand',
 'aspect_string_option_flag':'screen_option_flag',
 'aspect_string_store_integer':'screen_store_integer',
}

def build(output,flags,overlay_ready=False):
 output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
 sources=[Path(__file__).resolve(),ROOT/'src/aspect/screen_runtime.h',
          ROOT/'reconstruction/uart/encodings.inc']
 objects=[]
 for name in ('screen_commands','screen_bank'):
  source=ROOT/'src/aspect'/(name+'.asm');sources.append(source)
  extra=['-DASPECT_SCREEN_FAR',*['-D'+k+'='+v for k,v in ALIASES.items()]] if name=='screen_commands' else []
  modes=[('screen-bank-root','SCREEN_BANK_ROOT_ONLY'),('screen-bank-overlay','SCREEN_BANK_OVERLAY_ONLY')] if overlay_ready and name=='screen_bank' else [(name,None)]
  for leaf,mode in modes:
   obj=output/(leaf+'.obj')
   subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*flags,*extra,
                   *(['-D'+mode] if mode else []),str(source),'-o',str(obj)],check=True);objects.append(str(obj))
 for name in ('screen_runtime','screen_client'):
  source=ROOT/'src/aspect'/(name+'.c');obj=output/(name.replace('_','-')+'.obj');sources.append(source)
  subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we',
    *[f.replace('-D','-d',1) for f in flags],'-nt=SCRIPT_SCREEN_CODE','-nc=FARCODE',
    '-i='+str(ROOT/'src/aspect'),'-fo='+str(obj),str(source)],check=True)
  objects.append(str(obj))
 return objects,sources

def audit(output):
 text=(Path(output)/'ASPECT.map').read_text()
 segments={n:(int(s,16),int(o,16),int(z,16)) for n,s,o,z in re.findall(
  r'^(\w+)\s+\w+\s+\w+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)\s*$',text,re.M|re.I)}
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
  r'^\s*([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+(\w+)\s*$',text,re.M|re.I)}
 near=segments['_TEXT'];bank=segments['SCRIPT_SCREEN_CODE']
 assert near[2]<=65536 and bank[2]<65536 and near[0]!=bank[0]
 for name in ('box','clear','locate','scroll','getvattr','putvattr','home'):
  assert symbols['aspect_screen_'+name+'_entry'][0]==near[0]
 for name in ('box','clear','locate','scroll','getvattr','putvattr'):
  assert symbols['aspect_screen_'+name][0]==bank[0]
 for name in ('_runtime_screen_enter','_runtime_screen_scroll','_runtime_screen_read'):
  assert symbols[name][0]==bank[0]
 if '_aspect_render_screen_scalar' in symbols:
  assert symbols['_aspect_render_screen_scalar'][0]==bank[0]
  assert symbols['_aspect_render_screen_ready'][0]==near[0]
 return dict(passed=True,screen_bank_bytes=bank[2],near_code_bytes=near[2],
             near_code_spare=65536-near[2],native_handler_bytes=220,
             scope='Linked code-bank placement only; DOS execution and native display state need separate acceptance.')
