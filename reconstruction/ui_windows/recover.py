#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact text output source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/ui_windows'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('read_byte',0x6fa0,0x6fcf),('read_packed',0x6fd0,0x6feb),('save',0x765c,0x7682),('restore',0x7682,0x76b0),('flow_message',0x31bb,0x3226),('tick_delay',0x6b98,0x6bb6),('write_string',0x6bf0,0x6c1f),('coordinate',0x7e02,0x7e0e),('cga_blank',0x77be,0x77d2),('cga_unblank',0x77ae,0x77bd)]
FUNCTIONS={0x6fa0:'ui_read_byte',0x6fd0:'ui_read_packed',0x765c:'pcplus_screen_save',0x7682:'pcplus_screen_restore',0x31bb:'pcplus_flow_message',0x6b98:'ui_tick_delay',0x6bf0:'ui_write_string',0x7e02:'ui_coordinate_offset',0x77be:'ui_cga_blank',0x77ae:'ui_cga_unblank'}
SERVICES={0x6cb4:'text_write_packed',0x6c20:'text_fill_cells'}
STATE={0x7a78:'text_video_segment',0x7a8e:'text_cga_status_port',0x7a72:'screen_columns',0x3250:'ui_flow_region_cells',0x7a82:'ui_flow_video_base',0x7a84:'ui_flow_coordinate_base',0x1d46:'ui_flow_suppressed',0x1f6e:'ui_flow_attribute'}

def main():
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest={'source_sha256':EXPECTED,'units':[],'state':{f'{k:04x}':v for k,v in STATE.items()},'services':{f'{k:04x}':v for k,v in SERVICES.items()},'limitations':['Recovered names are analyst annotations. State names are analyst annotations; actual configuration initial values are host-provided.']}
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
    rows.append((at,instruction))
   header=['; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.','BITS 16','CPU 8086','%ifdef UI_WINDOWS_OMF','SEGMENT _TEXT public class=CODE use16','global '+','.join(v for k,v in FUNCTIONS.items() if start<=k<end)]
   calls=set()
   for _,text in rows:
    m=re.fullmatch(r'call (0x[0-9a-f]+)',text)
    if m:calls.add(int(m[1],16))
   external={k:v for k,v in (FUNCTIONS|SERVICES).items() if k in calls and not start<=k<end}
   for v in external.values():header.append('extern '+v)
   state_used={k:v for k,v in STATE.items() if any(re.search(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',t) for _,t in rows)}
   for v in state_used.values():header.append('extern '+v)
   header+=['%define short','%else',f'ORG 0x{start:x}']
   for k,v in external.items():header.append(f'%define {v} 0x{k:x}')
   for k,v in state_used.items():header.append(f'%define {v} 0x{k:x}')
   header+=['%endif','%include "encodings.inc"',FUNCTIONS[start]+':']
   for at,text in rows:
    for k,v in state_used.items():text=text.replace('[0x'+f'{k:x}'+']','['+v+']')
    branch=re.fullmatch(r'(j\w+|loop|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
    if branch:
     target=int(branch[3],16)
     symbol=f'L_{target:04x}' if start<=target<end else (FUNCTIONS|SERVICES)[target]
     text=branch[1]+' '+(branch[2]+' ' if branch[2] else '')+symbol

    if at in FUNCTIONS and at != start:header.append(FUNCTIONS[at]+':')
    header.append(f'L_{at:04x}: '+text)
   path=SOURCE/(name+'.asm');path.write_text('\n'.join(header)+'\n')
   subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(work/'whole.bin')],check=True)
   assert (work/'whole.bin').read_bytes()==blob,name
   manifest['units'].append({'file':str(path.relative_to(ROOT)),'start':start,'end':end,'bytes':len(blob),'instructions':len(rows),'sha256':hashlib.sha256(blob).hexdigest(),'matched_original':True})
 manifest['rea_evidence']={}
 for at in [0x16fa0,0x16fd0,0x1765c,0x17682,0x131bb,0x14647,0x16b98,0x16bf0,0x17e02,0x177be,0x177ae]:
  evidence=json.loads((ROOT/f'analysis/pcplus-main/functions/{hex(at)}-asm.json').read_text())['structuredContent']
  assert evidence['subject']['digest']['sha256']==EXPECTED
  manifest['rea_evidence'][hex(at)]={'evidence_id':evidence['evidence_id'],'saved_export':f'analysis/pcplus-main/functions/{hex(at)}.asm'}
 manifest['callers']={'save':['0x131bb','0x14647','0x1ac0e'],'restore':['0x131bb','0x14647','0x1ac0e'],'save_evidence_id':'ev_8c52162e841ddde4985edc5d1639c8d8d99d4532ea0555034020f489d5943a37','restore_evidence_id':'ev_6fa85bbb1c99e891948a77e89afc9d784476a79e6cbbd8f923a5a97549d91e96','scope':'Resolved calls in resident original; appended overlays and unresolved indirect callers outside coverage.'}
 for unit in manifest['units']:unit['file_offset']=0x1200+unit['start']
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Recovered',sum(u['bytes'] for u in manifest['units']),'bytes')
if __name__=='__main__':main()
