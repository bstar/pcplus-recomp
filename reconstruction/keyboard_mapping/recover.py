#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact text output source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/keyboard_mapping'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('emit',0x0a62,0x0a8b),('echo',0x0e4e,0x0e61),('dispatch',0x138a,0x1a75),('pace',0x6b72,0x6b98)]
FUNCTIONS={0x0a62:'keyboard_mapping_emit',0x0e4e:'keyboard_mapping_echo',0x0e60:'keyboard_mapping_noop',0x1604:'keyboard_mapping_dispatch',0x138a:'keyboard_mapping_shift_tab',0x6b72:'keyboard_mapping_pace'}
SERVICES={}
STATE={0x3378:'terminal_keymap',0x44e0:'keyboard_dispatch_table',0xcffa:'keyboard_mapping_key',0x1d74:'keyboard_mapping_scrollback_mode',0x1d6e:'keyboard_mapping_hook_enabled',0x1d70:'keyboard_mapping_hook_character'}

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
   # Names describe integration addresses without pretending unrecovered UI semantics.
   for _,instruction in rows:
    branch=re.fullmatch(r'(?:call|j\w+) (?:short |near )?(0x[0-9a-f]+)',instruction)
    if branch:
     target=int(branch[1],16)
     if not start<=target<end and target not in FUNCTIONS:SERVICES.setdefault(target,f'keyboard_service_{target:04x}')
    for bracket in re.findall(r'\[([^]]+)\]',instruction):
     for token in re.findall(r'0x[0-9a-f]+',bracket):
      address=int(token,16)
      if address>=0x100 and address not in STATE:STATE[address]=f'keyboard_state_{address:04x}'
   header=['; Recovered PCPlus 2.01 terminal keyboard mapping instructions; see docs/KEYBOARD_MAPPING.md.','BITS 16','CPU 8086','%ifdef KEYBOARD_MAPPING_OMF','SEGMENT _TEXT public class=CODE use16','global '+','.join(v for k,v in FUNCTIONS.items() if start<=k<end)]
   calls=set()
   for _,text in rows:
    m=re.fullmatch(r'call (0x[0-9a-f]+)',text)
    if m:calls.add(int(m[1],16))
    m=re.fullmatch(r'j\w+ (?:short |near )?(0x[0-9a-f]+)',text)
    if m:calls.add(int(m[1],16))
   external={k:v for k,v in (FUNCTIONS|SERVICES).items() if k in calls and not start<=k<end}
   for v in external.values():header.append('extern '+v)
   state_used={k:v for k,v in STATE.items() if any(re.search(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',t) for _,t in rows)}
   for v in state_used.values():header.append('extern '+v)
   header+=['%define short','%else',f'ORG 0x{start:x}']
   for k,v in external.items():header.append(f'%define {v} 0x{k:x}')
   for k,v in state_used.items():header.append(f'%define {v} 0x{k:x}')
   entry=FUNCTIONS.get(start,f'keyboard_region_{start:04x}'); FUNCTIONS[start]=entry
   header+=['%endif','%include "encodings.inc"',entry+':']
   for at,text in rows:
    for k,v in state_used.items():text=re.sub(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',v,text)
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
 for at in [0x11604,0x10a62,0x10e4e,0x115b6,0x115d6,0x16b72]:
  evidence=json.loads((ROOT/f'analysis/pcplus-main/functions/{hex(at)}-asm.json').read_text())['structuredContent']
  assert evidence['subject']['digest']['sha256']==EXPECTED
  manifest['rea_evidence'][hex(at)]={'evidence_id':evidence['evidence_id'],'saved_export':f'analysis/pcplus-main/functions/{hex(at)}.asm'}
 manifest['helper_listing_limit']='REA resident Listing left indirect helper138a undefined; actual original file offset confirmed by REA address_to_file_offset evidence ev_fed07cee314ea4408ae7f955c2b21d040fc7a9ffdbc91efbad33596d7c6d65b9. SHA-verified bytes decoded independently with ndisasm.'
 manifest['state']={f'{k:04x}':v for k,v in STATE.items()}
 manifest['services']={f'{k:04x}':v for k,v in SERVICES.items()}
 for unit in manifest['units']:unit['file_offset']=0x1200+unit['start']
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Recovered',sum(u['bytes'] for u in manifest['units']),'bytes')
def finish():
 import struct
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 raw=image[153936+0x44e0:153936+0x44e0+282];table=struct.unpack('<141H',raw)
 proof=json.loads((SOURCE/'provenance.json').read_text())
 for path in [SOURCE/(unit[0]+'.asm') for unit in UNITS]:
  text=path.read_text()
  for addr in [0x3150,0x3174,0x31e0,0x3758,0x3262,0x4675,0xce6a,0x467b]:
   token=f'0x{addr:x}';name=f'keyboard_state_{addr:04x}'
   if token not in text:continue
   text=text.replace(token,name).replace('%define short',f'extern {name}\n%define short').replace('%endif\n%include',f'%define {name} 0x{addr:x}\n%endif\n%include')
   proof['state'][f'{addr:04x}']=name
  if path.name=='dispatch.asm':
   pos=text.index('%define short')
   text=text[:pos]+''.join(f'global keyboard_original_{t:04x}\n' for t in sorted(set(table)) if 0x138a<=t<0x1a75)+text[pos:]
   for target in sorted(set(table)):
    if 0x138a<=target<0x1a75:text=text.replace(f'L_{target:04x}:',f'keyboard_original_{target:04x}:\nL_{target:04x}:')
  path.write_text(text)
 lines=['; Exact original DS44e0 indirect near-code targets, not live profile bindings.','BITS 16','%ifdef KEYBOARD_MAPPING_OMF','SEGMENT _DATA public class=DATA use16','global keyboard_dispatch_table']
 symbol=lambda target:'keyboard_mapping_noop' if target==0xe60 else f'keyboard_original_{target:04x}'
 for target in sorted(set(table)):lines+=['extern '+symbol(target)]
 lines+=['keyboard_dispatch_table:']
 for scan,target in enumerate(table):lines.append(' dw '+symbol(target)+f' ; scan{scan:02x}')
 lines+=['%else']+['dw '+','.join(f'0x{x:04x}' for x in table[i:i+10]) for i in range(0,len(table),10)]+['%endif']
 (SOURCE/'dispatch_table.asm').write_text('\n'.join(lines)+'\n')
 proof['dispatch_table']={'original_DS':0x44e0,'overlay':32,'file_offset':153936+0x44e0,'bytes':282,'sha256':hashlib.sha256(raw).hexdigest(),'entries':141}
 (SOURCE/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main();finish()
