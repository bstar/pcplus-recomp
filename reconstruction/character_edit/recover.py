#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact line editing source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/character_edit'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('insert_character',0xd270,0xd440),('delete_character',0xd440,0xd668),('set_tab',0xdac6,0xdaf2),('cga_restore',0x77ae,0x77bd),('cga_disable',0x77be,0x77d2)]
FUNCTIONS={0xd270:'csi_insert_character',0xd440:'csi_delete_character',0xdac6:'terminal_set_tab',0x77ae:'character_cga_restore',0x77be:'character_cga_disable'}
SERVICES={0x6412:'erase_far_move',0x85b4:'erase_move_bytes',0x6c84:'text_write_char',0x2d98:'erase_repair_attributes'}
STATE={}
for module in ('screen','erase','text','line_edit'):
 proof=json.loads((ROOT/f'reconstruction/{module}/provenance.json').read_text())
 STATE.update({int(k,16):v for k,v in proof.get('state',{}).items()})
STATE.update({0x3342:'csi_wrap_pending',0x3344:'screen_video_offset',0x3346:'screen_attribute_offset',0x399c:'screen_cursor_row',0x399e:'screen_cursor_column',0x3258:'screen_last_column',0x3734:'screen_attribute_checks',0x900c:'screen_cursor_wrap',0x39c4:'screen_attributes_base',0x39c2:'erase_attribute_values_base',0xcf86:'screen_line_flags',0x3256:'screen_viewport_active',0x7a72:'screen_columns',0x7a7e:'screen_viewport_right',0x5dea:'erase_shadow_offset',0x5dec:'erase_shadow_segment',0x7a78:'text_video_segment',0x7a8e:'text_cga_status_port',0xce10:'terminal_tab_stops',0x1d32:'attributes_normal_value'})

def main():
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest={'source_sha256':EXPECTED,'units':[],'state':{f'{k:04x}':v for k,v in STATE.items()},'services':{f'{k:04x}':v for k,v in SERVICES.items()},'limitations':['Recovered names are analyst annotations. Viewport and attribute-boundary/repair helpers remain required external services.']}
 with tempfile.TemporaryDirectory() as temp:
  work=Path(temp)
  def assemble(text,at):
   (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n'+text+'\n')
   p=subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
   return (work/'one.bin').read_bytes() if p.returncode==0 else None
  for name,start,end in UNITS:
   file_start=(89472+start-0xd0d0) if start>=0xd0d0 else 0x1200+start
   blob=image[file_start:file_start+end-start];(work/'part').write_bytes(blob)
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
    for state_at in list(STATE)+[0xcf87]:
     signed=state_at-65536
     if signed<0:instruction=instruction.replace(f'-0x{-signed:x}',f'+0x{state_at:x}')
    instruction=instruction.replace('0xcf87','(0xcf86+1)')
    rows.append((at,instruction))
   header=['; Recovered PCPlus 2.01 character editing instructions; see docs/CHARACTER_EDIT.md.','BITS 16','CPU 8086','%ifdef CHARACTER_EDIT_OMF','SEGMENT _TEXT public class=CODE use16','global '+FUNCTIONS[start]]
   calls=set()
   for _,text in rows:
    m=re.fullmatch(r'(?:call|jmp(?: near)?) (0x[0-9a-f]+)',text)
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
   manifest['units'].append({'file':str(path.relative_to(ROOT)),'start':start,'end':end,'source_file_offset':file_start,'bytes':len(blob),'instructions':len(rows),'sha256':hashlib.sha256(blob).hexdigest(),'matched_original':True})
 manifest['rea_exports']={}
 for start in (0xd270,0xd440,0x77ae,0x77be):
  folder='pcplus-overlay-12' if start>=0xd000 else 'pcplus-main'
  path=ROOT/f'analysis/{folder}/functions/{hex(0x10000+start)}-asm.json'
  evidence=json.loads(path.read_text())['structuredContent']
  manifest['rea_exports'][hex(start)]={'evidence_id':evidence['evidence_id'],'analysis_artifact_sha256':evidence['subject']['digest']['sha256'],'scope':'Static analysis export; instructions independently verified at original-file offsets.'}
 evidence=json.loads((ROOT/'analysis/character-edit/settab-asm.json').read_text())['structuredContent']
 manifest['rea_exports']['0xdac6']={'evidence_id':evidence['evidence_id'],'analysis_artifact_sha256':evidence['subject']['digest']['sha256'],'scope':'Never-executed overlay12 analysis container with only MZ CS:IP changed to0:dac6; code bytes unchanged, independently verified against original.'}
 manifest['limitations']=['Character helpers edit one cell (two in doublewidth) per call; repetition belongs to dispatcher.','Delete character nontrivial900c attribute repair2d98 remains explicit external dependency.','Set-tab44bytes verified from original plus focused REA entry-anchored static container; default Ghidra auto-analysis had left this tiny helper undecoded.','Original state/viewport ranges assumed; exact helpers contain no added range/count/cancellation policy.']
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Recovered',sum(u['bytes'] for u in manifest['units']),'bytes')
if __name__=='__main__':main()
