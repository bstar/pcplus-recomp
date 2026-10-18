#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact text output source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/meta_keys'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('invoke',0x47b6,0x4816),('text',0x48cc,0x4934),('caret',0x4934,0x498b),('alt_digit',0x1594,0x15b6),('hook',0x414c,0x427f),('validate_name',0x4748,0x476a),('get_ds',0x76b0,0x76b3),('decimal32',0x89fa,0x8a04),('decimal_core',0xa5e8,0xa647),('decimal16',0x8e6c,0x8e87),('strcpy',0x8268,0x829a),('strcat',0x8bea,0x8c29),('tick_delay',0x6b98,0x6bb6),('pace',0x6b72,0x6b98)]
FUNCTIONS={0x47b6:'meta_keys_invoke',0x48cc:'meta_keys_send_text',0x4934:'meta_keys_expand',0x1594:'meta_keys_alt_digit',0x414c:'meta_keys_hook',0x4748:'meta_keys_validate_name',0x76b0:'meta_keys_get_ds',0x89fa:'meta_keys_decimal32',0xa5e8:'meta_keys_decimal_core',0xa5f4:'meta_keys_decimal_body',0x8e6c:'meta_keys_decimal16',0x8268:'meta_keys_strcpy',0x8bea:'meta_keys_strcat',0x6b98:'meta_keys_tick_delay',0x6b72:'meta_keys_pace'}
SERVICES={0x427f:'meta_keys_message',0x4b1f:'meta_keys_aspect_service',0x433d:'meta_keys_program_service',0x353d:'meta_keys_resolve_program',0x0610:'meta_keys_echo',0xab0b:'meta_keys_transmit'}
STATE={0x4b02:'meta_script_active',0x4430:'meta_script_busy_message',0x4416:'meta_missing_name_message',0x1d66:'meta_pause_byte',0x1d68:'meta_pacing',0x1d1a:'meta_local_echo',0xcffa:'meta_normalized_scan',0x3756:'meta_actions',0x3758:'meta_actions_text0',0xd124:'meta_hook_result',0xd126:'meta_hook_exchange_a',0xd13a:'meta_hook_exchange_b',0x1b84:'meta_prm_image',0x4765:'meta_hook_prefix',0x476e:'meta_hook_space_a',0x4770:'meta_hook_space_b',0x4772:'meta_hook_space_c',0x4774:'meta_hook_space_d',0x7a4e:'meta_pace_counter',0x7ac4:'meta_pace_calibration'}

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
    for state_at in STATE:
     signed=state_at-65536
     if signed<0:instruction=instruction.replace(f'-0x{-signed:x}',f'+0x{state_at:x}')
    rows.append((at,instruction))
   header=['; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.','BITS 16','CPU 8086','%ifdef META_KEYS_OMF','SEGMENT _TEXT public class=CODE use16','global '+','.join(v for k,v in FUNCTIONS.items() if start<=k<end)]
   calls=set()
   for _,text in rows:
    m=re.fullmatch(r'(?:call|jmp(?: near)?) (0x[0-9a-f]+)',text)
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
 for at in [0x147b6,0x148cc,0x14934,0x1414c,0x14748,0x115b6,0x176b0,0x189fa,0x1a5e8,0x18e6c,0x18268,0x18bea,0x16b98,0x16b72,0x1433d,0x1896a,0x13745,0x1353d]:
  evidence=json.loads((ROOT/f'analysis/pcplus-main/functions/{hex(at)}-asm.json').read_text())['structuredContent']
  assert evidence['subject']['digest']['sha256']==EXPECTED
  manifest['rea_evidence'][hex(at)]={'evidence_id':evidence['evidence_id'],'saved_export':f'analysis/pcplus-main/functions/{hex(at)}.asm'}
 manifest['current_rea_queries']={'0x1414c':'ev_8577afa849cd9ce96e9e01938bdba7ddb19a8a19dd44b7dada8d79c032bcd669','0x148cc':'ev_3a29c9753cf6188658686eb46944e813fddeb172758c9bded7dc265f9aeac907','0x14934':'ev_059b2b6f9c5a4c8603920897ea8ceb541feea65be2c5787a294ab008abf9155d'}
 manifest['hook_command_protocol']={'prefix':' PCPLUS ','unsigned_decimal':'Packed (DS << 16) | offset; not physical address or value read from that pointer','kind2_offsets':['d126','d13a','1b84'],'context':'signed16 decimal, Alt digit caller passes3','PROGRAM_native_route':'433d third argument1 ->896a uses COMSPEC /c, fallback command.com; retained external service'}
 manifest['limitations']=['ASPECT interpreter, external program executor/resolver and message UI remain explicit external services.','Original caret parser and stack sender have no input bounds; malformed trailing caret can read beyond NUL.','Original TEXT pauses are blocking, count argument9 waits10 BIOS transitions; calibrated pacing separate.']
 for unit in manifest['units']:unit['file_offset']=0x1200+unit['start']
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Recovered',sum(u['bytes'] for u in manifest['units']),'bytes')
if __name__=='__main__':main()
