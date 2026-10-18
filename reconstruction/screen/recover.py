#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact cursor source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/screen'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('set_cursor',0x1bbe,0x1c66),('down',0x1e0c,0x1e2f),('left',0x1e30,0x1e9f),('right',0x1ea0,0x1efc),('up',0x1efc,0x1f55),('width_transition',0x2a90,0x2adc),('cursor_pack',0x6e66,0x6e77),('cursor_output',0x6e78,0x6ec2)]
FUNCTIONS={0x1bbe:'screen_set_cursor',0x1e0c:'screen_cursor_down',0x1e30:'screen_cursor_left',0x1ea0:'screen_cursor_right',0x1efc:'screen_cursor_up',0x2a90:'screen_width_transition',0x6e66:'screen_cursor_pack',0x6e78:'screen_cursor_output'}
SERVICES={0x482a:'screen_viewport_enter',0x4850:'screen_viewport_leave',0x2fb8:'screen_viewport_refresh',0x2adc:'screen_adjust_attribute_boundary',0x12c8:'screen_wrap_forward'}
STATE={0xcdfa:'screen_viewport_enabled',0xce2e:'screen_viewport_left',0x3256:'screen_viewport_active',0x39a4:'screen_viewport_offset',0x7a7e:'screen_viewport_right',0x39a0:'screen_visible_column',0x3344:'screen_video_offset',0x3348:'screen_previous_column',0x3346:'screen_attribute_offset',0x399e:'screen_cursor_column',0x39a2:'screen_previous_row',0x7a7a:'screen_video_row_bytes',0x325a:'screen_attribute_row_bytes',0x399c:'screen_cursor_row',0xceb0:'screen_top_margin',0xd122:'screen_doublewidth_enabled',0xce3a:'screen_last_row',0x9018:'screen_vertical_attribute_check',0x3734:'screen_attribute_checks',0x39c4:'screen_attributes_base',0xcee4:'screen_bottom_margin',0x3258:'screen_last_column',0xcf86:'screen_line_flags',0x900c:'screen_cursor_wrap',0xce0e:'screen_first_row',0x9038:'screen_reverse_wrap_blocked',0x7a66:'screen_use_bios_cursor',0x7a72:'screen_columns'}

def main():
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest={'source_sha256':EXPECTED,'units':[],'state':{f'{k:04x}':v for k,v in STATE.items()},'services':{f'{k:04x}':v for k,v in SERVICES.items()},'limitations':['Recovered names are analyst annotations. External viewport, attribute and wrap implementations remain required.']}
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
   header=['; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.','BITS 16','CPU 8086','%ifdef SCREEN_OMF','SEGMENT _TEXT public class=CODE use16','global '+FUNCTIONS[start]]
   calls=set()
   for _,text in rows:
    m=re.fullmatch(r'call (0x[0-9a-f]+)',text)
    if m:calls.add(int(m[1],16))
   external={k:v for k,v in (FUNCTIONS|SERVICES).items() if k in calls}
   for v in external.values():header.append('extern '+v)
   state_used={k:v for k,v in STATE.items() if any(re.search(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',t) for _,t in rows)}
   for v in state_used.values():header.append('extern '+v)
   header+=['%define short','%else',f'ORG 0x{start:x}']
   for k,v in external.items():header.append(f'%define {v} 0x{k:x}')
   for k,v in state_used.items():header.append(f'%define {v} 0x{k:x}')
   header+=['%endif','%include "encodings.inc"',FUNCTIONS[start]+':']
   for at,text in rows:
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
