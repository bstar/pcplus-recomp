#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact text output source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/program_exec'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('executor',0x433d,0x456a),('system',0x896a,0x89f9),('getenv',0x8e12,0x8e6b),('environment_tail',0x65ca,0x684a),('spawn_extension',0x684a,0x68ee),('spawnv',0x68ee,0x6a17),('exec',0x6a22,0x6b0a),('spawnl',0x8d34,0x8d48),('spawnlp',0xa64e,0xa66a),('spawn_search',0xa4a6,0xa5e8),('stack_probe',0xa8bc,0xa8d3),('access',0x93aa,0x93c9),('error_access',0x9420,0x9428),('error_exec',0x9435,0x9442),('map_error',0x9448,0x9475),('strcpy',0x8268,0x829a),('strcat',0x8bea,0x8c29),('strlen',0x8d18,0x8d33),('strchr',0x8c2a,0x8c54),('strrchr',0x83c6,0x83f1),('strcmpi',0x93de,0x9420),('strncmp',0x9c06,0x9c40),('path_component',0xa8e6,0xa930),('validate_name',0x4748,0x476a),('get_ds',0x76b0,0x76b3)]
FUNCTIONS={0x4748:'program_validate_name',0x76b0:'program_get_ds',0x9437:'program_error_failure',0x433d:'program_execute',0x896a:'program_system',0x8e12:'program_getenv',0x65ca:'program_environment_tail',0x684a:'program_spawn_extension',0x68ee:'program_spawnv',0x6a22:'program_exec',0x8d34:'program_spawnl',0xa64e:'program_spawnlp',0xa4a6:'program_spawn_search',0xa8bc:'program_stack_probe',0x93aa:'program_access',0x9420:'program_access_result',0x9435:'program_exec_result',0x9448:'program_map_error',0x8268:'program_strcpy',0x8bea:'program_strcat',0x8d18:'program_strlen',0x8c2a:'program_strchr',0x83c6:'program_strrchr',0x93de:'program_strcmpi',0x9c06:'program_strncmp',0xa8e6:'program_path_component'}
SERVICES={}
STATE={0x6a18:'program_saved_sp',0x6a1a:'program_saved_ss',0x6a1c:'program_saved_pair_low',0x6a1e:'program_saved_pair_high',0x6a20:'program_saved_ds',0x2e:'program_pair_low',0x30:'program_pair_high',0x333c:'program_busy',0x7b43:'program_environ',0x7b1c:'program_errno',0x7b27:'program_dos_error',0x7b56:'program_error_map',0x7b24:'program_dos_major',0x7dc4:'program_path_name',0x7ae8:'program_comspec_name',0x7af0:'program_switch_c',0x7af3:'program_default_shell',0x5e14:'program_batch_prefix',0x5e18:'program_comspec_name2',0x5e30:'program_extensions',0x5e32:'program_extension1',0x5e34:'program_extension2',0x5e20:'program_ext_bat',0x5e25:'program_ext_exe',0x5e2a:'program_ext_com',0x5e36:'program_exec_block',0x5e38:'program_exec_tail',0x5e3a:'program_exec_tail_segment',0x5e3c:'program_exec_fcb1',0x5e3e:'program_exec_fcb1_segment',0x5e40:'program_exec_fcb2',0x5e42:'program_exec_fcb2_segment',0x5e44:'program_fcb1',0x5e54:'program_fcb2',0x7b4a:'program_exec_active',0x8e24:'program_overlay_gate',0x8e26:'program_overlay_callback',0x9062:'program_fallback_environment',0x7b54:'program_heap_mode'}

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
    for address in STATE:
     if address>=32768:instruction=instruction.replace(f'-0x{65536-address:x}',f'+0x{address:x}')
    rows.append((at,instruction))
   # Names describe integration addresses without pretending unrecovered UI semantics.
   for _,instruction in rows:
    branch=re.fullmatch(r'(?:call|j\w+) (?:short |near )?(0x[0-9a-f]+)',instruction)
    if branch:
     target=int(branch[1],16)
     if not start<=target<end and target not in FUNCTIONS:SERVICES.setdefault(target,f'program_service_{target:04x}')
    for bracket in re.findall(r'\[([^]]+)\]',instruction):
     for token in re.findall(r'0x[0-9a-f]+',bracket):
      address=int(token,16)
      if address>=0x100 and address not in STATE:STATE[address]=f'program_state_{address:04x}'
   for _,instruction in rows:
    pointer=re.fullmatch(r'mov (?:ax|bx|cx|dx|si|di),(0x[0-9a-f]+)',instruction)
    if pointer:
     address=int(pointer[1],16)
     if address in (0x7b00,0x7dc9,0x7dd6,0x7ae8,0x7af0,0x7af3,0x5e18,0x5e14,0x9062):STATE.setdefault(address,f'program_state_{address:04x}')
   header=['; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.','BITS 16','CPU 8086','%ifdef PROGRAM_EXEC_OMF','SEGMENT _TEXT public class=CODE use16','global '+','.join(v for k,v in FUNCTIONS.items() if start<=k<end)]
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
   entry=FUNCTIONS.get(start,f'program_region_{start:04x}'); FUNCTIONS[start]=entry
   header+=['%endif','%include "encodings.inc"',entry+':']
   for at,text in rows:
    for k,v in state_used.items():
     if k<0x100:
      text=text.replace('[0x'+f'{k:x}'+']','['+v+']')
      if at in (0x6a93,0x6add):text=text.replace('0x2e','program_pair_low')
     else:text=re.sub(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',v,text)
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
 for _,start,_ in UNITS:
  path=ROOT/f'analysis/pcplus-main/functions/{hex(0x10000+start)}-asm.json'
  if path.exists():
   evidence=json.loads(path.read_text())['structuredContent'];assert evidence['subject']['digest']['sha256']==EXPECTED
   manifest['rea_evidence'][hex(start)]={'evidence_id':evidence['evidence_id'],'saved_export':str(path.relative_to(ROOT))}
 manifest['current_rea_queries']={'433d':'ev_a5c189826e129ae1c8a59c464a4fb7be362d61aaeadcb2317f2c1b78b19768ad','6a22':'ev_9f941d3453b6171221a7e708d17f2865fe383265f41d1677002ac5dbdf5b672f','65ca':'ev_82bb269d504574be861a5035336ab5e3340081fba03629135fefb05784cf78d8'}
 manifest['state']={f'{k:04x}':v for k,v in STATE.items()}
 manifest['services']={f'{k:04x}':v for k,v in SERVICES.items()}
 manifest['limitations']=['Original runtime heap allocation/free/farheap, UI/screen/mouse/vector/serial services remain explicit dependencies.','Standalone actualDOS diagnostic calls original EXEC core with maintained startup memory shrink and source-built synthetic child, not complete application executor.','Original command-tail builder rejects concatenated arguments exceeding125bytes; environment and heap behavior retains legacy assumptions.']
 for unit in manifest['units']:unit['file_offset']=0x1200+unit['start']
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Recovered',sum(u['bytes'] for u in manifest['units']),'bytes')
def scratch():
 import json,hashlib
 path=SOURCE/'scratch.asm'
 text=['; Exact zero-initialized original CS6a18..6a21 execution save cells.','BITS 16','%ifdef PROGRAM_EXEC_OMF','SEGMENT _TEXT public class=CODE use16','%else','ORG 0x6a18','%endif']
 for name in ['program_saved_sp','program_saved_ss','program_saved_pair_low','program_saved_pair_high','program_saved_ds']:
  text+=['%ifdef PROGRAM_EXEC_OMF','global '+name,'%endif',name+': dw 0']
 path.write_text('\n'.join(text)+'\n')
 image=ORIGINAL.read_bytes();data=image[0x1200+0x6a18:0x1200+0x6a22];assert data==bytes(10)
 proof=json.loads((SOURCE/'provenance.json').read_text());proof['units'].append({'file':str(path.relative_to(ROOT)),'start':0x6a18,'end':0x6a22,'file_offset':0x1200+0x6a18,'bytes':10,'instructions':0,'sha256':hashlib.sha256(data).hexdigest(),'matched_original':True,'kind':'CS-owned writable save cells, not instructions'})
 data=ORIGINAL.read_bytes()[153936+0x7b56:153936+0x7b56+20]
 lookup=SOURCE/'error_lookup.asm';lookup.write_text('; Recovered DOS-to-CRT error mapping, originalDS7b56.\nBITS 16\n%ifdef PROGRAM_EXEC_OMF\nSEGMENT _DATA public align=16 class=DATA use16\nglobal program_error_map\n%endif\nprogram_error_map: db '+','.join(str(v) for v in data)+'\n')
 proof['units'].append({'file':str(lookup.relative_to(ROOT)),'start':0x7b56,'end':0x7b6a,'file_offset':153936+0x7b56,'bytes':20,'instructions':0,'sha256':hashlib.sha256(data).hexdigest(),'matched_original':True,'kind':'overlay32 DSdata table, not resident instructions'})
 (SOURCE/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main();scratch()
