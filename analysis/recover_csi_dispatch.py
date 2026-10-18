#!/usr/bin/env python3
"""Recover the known CSI function and its two inline jump tables for review.

Explicit analysis step. Writes under build/recovered-csi, never maintained source.
Instruction boundaries are corroborated by the retained REA export; jump table
bounds come from the indexed CS jumps and their range guards.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
START,END,FILE_OFFSET=0xe4b2,0xec94,94562
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
assert hashlib.sha256(image).hexdigest()==EXPECTED
blob=image[FILE_OFFSET:FILE_OFFSET+END-START]
out=ROOT/'build/recovered-csi';out.mkdir(parents=True,exist_ok=True)
include=ROOT/'reconstruction/uart'
state={0x1d18:'csi_terminal_id',0x1d32:'attributes_normal_value',0x1f70:'attributes_current',
0x321c:'attributes_reverse_active',0x321e:'csi_previous_terminal_id',0x3258:'csi_last_column',
0x325a:'csi_column_count',0x3342:'csi_wrap_pending',0x334a:'csi_last_row',0x334c:'csi_row_count',
0x397c:'attributes_bold_active',0x397e:'attributes_blink_active',0x399c:'screen_cursor_row',
0x399e:'screen_cursor_column',0x8ff6:'attributes_monochrome',0xcb3c:'ansi_parameters',
0xcb5c:'ansi_parameter_count',0xcd38:'ansi_command',0xcdd2:'csi_origin_mode',0xce0e:'csi_scroll_top',
0xce3a:'csi_scroll_bottom',0xceac:'ansi_private',0xceb0:'csi_origin_row',0xcee2:'ansi_secondary',
0xcee4:'csi_origin_bottom',0xd008:'csi_erase_attribute',0x7525:'csi_secondary_prefix',
0x7529:'csi_secondary_7529',0x322c:'csi_secondary_322c'}
services={0x610:'ansi_control_character',0x1bbe:'screen_set_cursor',0x1efc:'screen_cursor_up',
0x1e0c:'screen_cursor_down',0x1ea0:'screen_cursor_right',0x1e30:'screen_cursor_left',
0x1c8c:'attributes_normal',0x1cb2:'attributes_bold',0x1cce:'attributes_underline',
0x1ce4:'attributes_blink',0x1cf0:'attributes_reverse',0x1d6c:'attributes_default_transform',
0x5ca0:'ansi_next_byte',0xabde:'ansi_unread_byte',0xab0b:'csi_transmit_byte',0xabac:'csi_transmit_string',
0x20a4:'csi_reset_terminal',0x246c:'csi_clear_tabs',0x250a:'csi_reset_scroll_region',
0xdd74:'csi_save_cursor',0xddbc:'csi_restore_cursor',0xde04:'csi_device_status',
0xdd58:'csi_primary_attributes',0xde98:'csi_set_modes',0xdf7e:'csi_reset_modes',0xe084:'csi_media_copy'}
tables=[(0xe71c,0xe77c,'csi_sgr_table'),(0xebd8,0xec94,'csi_command_table')]
rows=[]
with tempfile.TemporaryDirectory() as directory:
 work=Path(directory)
 for lower,upper in [(START,0xe71c),(0xe77c,0xebd8)]:
  (work/'input').write_bytes(blob[lower-START:upper-START])
  decoded=subprocess.check_output(['ndisasm','-b16',f'-o{lower}',str(work/'input')],text=True)
  for line in decoded.splitlines():
   match=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line)
   assert match,line
   address,encoded,instruction=int(match[1],16),bytes.fromhex(match[2]),match[3]
   assert not instruction.startswith('db '),line
   rows.append((address,encoded,instruction))
 def assemble(instruction,address):
  (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {address}\n%include "encodings.inc"\n{instruction}\n')
  result=subprocess.run(['nasm','-f','bin','-I',str(include)+'/', '-o',str(work/'one.bin'),str(work/'one.asm')],capture_output=True)
  return (work/'one.bin').read_bytes() if result.returncode==0 else None
 resolved=[]
 for address,encoded,instruction in rows:
  text=instruction
  if encoded[0]==0xeb:text=text.replace('jmp ','jmp short ',1)
  elif encoded[0]==0xe9:text=text.replace('jmp ','jmp near ',1)
  elif 0x70<=encoded[0]<=0x7f:text=text.replace(' ',' short ',1)
  if assemble(text,address)!=encoded:
   candidates=[]
   if len(encoded)==2 and encoded[1]>=0xc0 and encoded[0] in (2,3,10,11,18,19,26,27,34,35,42,43,50,51,58,59,138,139):
    op,operands=instruction.split(' ',1);candidates.append(op+'_load '+operands)
   if re.search(r',(-?0x[0-9a-f]+)$',text):
    for width in ('word','byte'):
     candidates.append(re.sub(r',(-?0x[0-9a-f]+)$',rf',strict {width} \1',text))
   text=next((candidate for candidate in candidates if assemble(candidate,address)==encoded),None)
   assert text is not None,(hex(address),instruction,encoded.hex())
  resolved.append((address,encoded,text))
 addresses={address for address,_,_ in resolved}
 for address,_,instruction in resolved:
  match=re.fullmatch(r'call (0x[0-9a-f]+)',instruction)
  if match:
   target=int(match[1],16)
   if target not in services:services[target]=f'csi_service_{target:04x}'
 definitions=['; Original DS and service locations versus OMF linker symbols.','%ifdef ANSI_OMF']
 definitions+=['extern '+name for name in sorted(set(state.values())|set(services.values()))]
 definitions+=['%else']+['%%define %s 0x%x'%(name,address) for address,name in sorted({**state,**services}.items())]+['%endif']
 (out/'dispatch-layout.inc').write_text('\n'.join(definitions)+'\n')
 lines=['; Recovered CSI dispatcher, overlay 12, including two typed jump tables.',
 '; REA Evidence ev_5054c5700c911ddb639380e599bef490251714e34d8e56b6b3cc7c11b9667ba4.',
 'BITS 16','CPU 8086','%ifdef ANSI_OMF','SEGMENT _TEXT public class=CODE use16',
 'global ansi_dispatch_command','%define short','%else',f'ORG 0x{START:x}','%endif',
 '%include "encodings.inc"','%include "dispatch-layout.inc"','ansi_dispatch_command:']
 for address,encoded,text in resolved:
  for lower,upper,name in tables:
   if address==upper:
    values=struct.unpack('<'+'H'*((upper-lower)//2),blob[lower-START:upper-START])
    assert all(value in addresses for value in values)
    lines.append(name+':')
    for value in values:lines.append(f' dw L_{value:04x}')
  branch=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
  if branch:
   target=int(branch[3],16)
   if target in addresses:text=branch[1]+' '+((branch[2]+' ') if branch[2] else '')+f'L_{target:04x}'
   elif branch[1]=='call':text='call '+services[target]
  for lower,_,name in tables:
   text=text.replace(f'0x{lower:x}',name)
   # ndisasm prints high 16-bit table offsets as negative displacements.
   # These must relocate too when OMF moves the code away from its old CS.
   text=text.replace(f'-0x{0x10000-lower:x}',f'+{name}')
  text=re.sub(r'0xcb3e\b','(ansi_parameters+2)',text)
  for original,name in state.items():
   text=re.sub(rf'0x{original:x}\b',name,text)
   if original>=0x8000:
    text=text.replace(f'-0x{0x10000-original:x}]',f'+{name}]')
  lines.append(f'L_{address:04x}: {text}')
 # The final table follows the last instruction, so insert it explicitly.
 lower,upper,name=tables[-1]
 values=struct.unpack('<'+'H'*((upper-lower)//2),blob[lower-START:upper-START])
 assert all(value in addresses for value in values)
 lines.append(name+':');lines+= [f' dw L_{value:04x}' for value in values]
 source=out/'dispatch.asm';source.write_text('\n'.join(lines)+'\n')
 subprocess.run(['nasm','-f','bin','-I',str(out)+'/', '-I',str(include)+'/', '-o',str(out/'dispatch.bin'),str(source)],check=True)
 assert (out/'dispatch.bin').read_bytes()==blob
 subprocess.run(['nasm','-f','obj','-DANSI_OMF','-I',str(out)+'/', '-I',str(include)+'/', '-o',str(out/'dispatch.obj'),str(source)],check=True)
 manifest={'original_sha256':EXPECTED,'overlay':12,'start':START,'end':END,'file_offset':FILE_OFFSET,
 'bytes':len(blob),'decoded_instructions':len(resolved),'sha256':hashlib.sha256(blob).hexdigest(),
 'matched_original':True,'tables':[{'start':a,'end':b,'entries':(b-a)//2,'name':n} for a,b,n in tables],
 'state':{f'0x{a:04x}':n for a,n in sorted(state.items())},'services':{f'0x{a:04x}':n for a,n in sorted(services.items())},
 'limitations':['Full dispatcher recovered; referenced application services remain separate reconstruction work.',
 'Flat mode preserves original CSI-q payload read; maintained integration must select the historical fix explicitly.']}
 (out/'dispatch-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({k:v for k,v in manifest.items() if k not in ('state','services')},indent=2))
