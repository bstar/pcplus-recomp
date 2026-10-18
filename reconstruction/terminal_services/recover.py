#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact cursor source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/terminal_services'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('keyboard_mode',0x0b4e,0x0bc0),('tabs',0x246c,0x24da),('clear_home',0x24e2,0x2506),('reset_region',0x250a,0x2517)]
FUNCTIONS={0x0b4e:'terminal_keyboard_mode',0x246c:'csi_clear_tabs',0x24e2:'terminal_clear_home',0x250a:'csi_reset_scroll_region'}
SERVICES={0x2530:'csi_service_2530',0x24da:'attributes_reset',0x1bbe:'screen_set_cursor'}
STATE={0x8fe8:'terminal_dec_keys',0x3378:'terminal_keymap',0x372c:'terminal_keymap_end',0xce10:'terminal_tab_stops',0xce11:'terminal_tab_stops_next',0x325a:'screen_attribute_row_bytes',0x399e:'screen_cursor_column',0x334a:'csi_last_row',0x3258:'csi_last_column',0x1d32:'attributes_normal_value',0xceb0:'csi_origin_row',0xce0e:'csi_scroll_top',0xce3a:'csi_scroll_bottom'}

def main():
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest={'source_sha256':EXPECTED,'units':[],'state':{f'{k:04x}':v for k,v in STATE.items() if k!=0xce11},'derived_aliases':{'terminal_tab_stops_next':{'base':'terminal_tab_stops','offset':1}},'services':{f'{k:04x}':v for k,v in SERVICES.items()},'limitations':['Recovered names are analyst annotations. Tab initialization assumes a valid column count and an FE-terminated 30-byte table; tested column counts are 0,1,8,80,132. Keyboard mappings are caller-provided; this does not reconstruct the KBD file loader.']}
 with tempfile.TemporaryDirectory() as temp:
  work=Path(temp)
  def assemble(text,at):
   (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n'+text+'\n')
   p=subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
   return (work/'one.bin').read_bytes() if p.returncode==0 else None
  for name,start,end in UNITS:
   blob=image[0x1200+start:0x1200+end];(work/'part').write_bytes(blob)
   decoded=subprocess.check_output(['ndisasm','-b16',f'-o{start}',str(work/'part')],text=True)
   rows=[]
   for line in decoded.splitlines():
    m=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line);assert m,line
    at,raw,text=int(m[1],16),bytes.fromhex(m[2]),m[3];assert not text.startswith('db ')
    instruction=text
    if raw[0]==0xeb:instruction=instruction.replace('jmp ','jmp short ',1)
    elif raw[0]==0xe9:instruction=instruction.replace('jmp ','jmp near ',1)
    elif 0x70<=raw[0]<=0x7f:instruction=instruction.replace(' ',' short ',1)
    if assemble(instruction,at)!=raw:
     candidates=[]
     if len(raw)==2 and raw[1]>=0xc0 and raw[0] in (2,3,10,11,18,19,26,27,34,35,42,43,50,51,58,59,138,139):
      op,operands=text.split(' ',1);candidates.append(op+'_load '+operands)
     for width in ('word','byte'):candidates.append(re.sub(r',(-?0x[0-9a-f]+)$',rf',strict {width} \1',instruction))
     instruction=next((c for c in candidates if assemble(c,at)==raw),None)
     assert instruction is not None,(hex(at),text,raw.hex())
    for state_at in STATE:
     signed=state_at-65536
     if signed<0:instruction=instruction.replace(f'-0x{-signed:x}',f'+0x{state_at:x}')
    rows.append((at,instruction))
   header=['; Recovered PCPlus 2.01 terminal support instructions; see docs/TERMINAL_SERVICES.md.','BITS 16','CPU 8086','%ifdef TERMINAL_SERVICES_OMF','SEGMENT _TEXT public class=CODE use16','global '+FUNCTIONS[start]]
   calls=set()
   for _,text in rows:
    m=re.fullmatch(r'call (0x[0-9a-f]+)',text)
    if m:calls.add(int(m[1],16))
   external={k:v for k,v in (FUNCTIONS|SERVICES).items() if k in calls}
   for v in external.values():header.append('extern '+v)
   state_used={k:v for k,v in STATE.items() if k!=0xce11 if any(re.search(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',t) for _,t in rows)}
   for v in state_used.values():header.append('extern '+v)
   header+=['%define short','%else',f'ORG 0x{start:x}']
   for k,v in external.items():header.append(f'%define {v} 0x{k:x}')
   for k,v in state_used.items():header.append(f'%define {v} 0x{k:x}')
   header+=['%endif','%include "encodings.inc"',FUNCTIONS[start]+':']
   for at,text in rows:
    text=text.replace('0xce11','(terminal_tab_stops+1)')
    for k,v in state_used.items():text=re.sub(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',v,text)
    branch=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
    if branch:
     target=int(branch[3],16)
     symbol=f'L_{target:04x}' if start<=target<end else (FUNCTIONS|SERVICES)[target]
     text=branch[1]+' '+(branch[2]+' ' if branch[2] else '')+symbol
    header.append(f'L_{at:04x}: '+text)
   path=SOURCE/(name+'.asm');path.write_text('\n'.join(header)+'\n')
   subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(work/'whole.bin')],check=True)
   assert (work/'whole.bin').read_bytes()==blob,name
   manifest['units'].append({'file':str(path.relative_to(ROOT)),'start':start,'end':end,'bytes':len(blob),'instructions':len(rows),'sha256':hashlib.sha256(blob).hexdigest(),'matched_original':True})
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Recovered',sum(u['bytes'] for u in manifest['units']),'bytes')
if __name__=='__main__':main()
