#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact line editing source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/terminal_reset'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('bios_rectangle',0x6edc,0x6ef5),('reset',0x20a4,0x246c),('clear_video',0x6f60,0x6f76),('clear_shadow',0x27ea,0x280a),('cursor_default',0x2518,0x2530),('protected_home',0x1f56,0x1f6f),('status_fill',0x4097,0x40aa),('underline_default',0x40c9,0x40df),('underline_configured',0x40df,0x40f6),('underline_crtc',0x5c20,0x5c41),('geometry',0x281c,0x2a35),('width',0x2a36,0x2a6e),('status_refresh',0x2fb8,0x31bb)]
FUNCTIONS={0x6edc:'terminal_reset_bios_rectangle',0x20a4:'terminal_reset_native',0x6f60:'terminal_reset_clear_video',0x27ea:'terminal_reset_clear_shadow',0x2518:'terminal_reset_cursor_default',0x1f56:'terminal_reset_protected_home',0x4097:'terminal_reset_status_fill',0x40c9:'terminal_reset_underline_default',0x40df:'terminal_reset_underline_configured',0x5c20:'terminal_set_underline_scanline',0x281c:'terminal_reset_geometry',0x2a36:'terminal_reset_width',0x2fb8:'terminal_reset_status_refresh'}
SERVICES={0x6c20:'text_fill_cells',0x63fa:'erase_far_fill',0x2f78:'modes_cursor_shape',0x1bbe:'screen_set_cursor',0x2adc:'screen_adjust_attribute_boundary',0xb4e:'terminal_keyboard_mode',0xcd2:'terminal_reset_load_keymap',0x24e2:'terminal_clear_home',0x6edc:'terminal_reset_bios_rectangle',0x246c:'csi_clear_tabs',0x85b4:'erase_move_bytes',0x85fc:'terminal_reset_free_far',0x860f:'terminal_reset_allocate_far',0x427f:'terminal_reset_application_error',0x2d98:'erase_repair_attributes',0x3226:'terminal_reset_status_message',0x6cb4:'text_write_packed',0x75e8:'terminal_reset_ui_75e8',0x7630:'terminal_reset_ui_7630',0x82b6:'terminal_reset_sprintf',0xaa5c:'terminal_reset_uart_status'}
STATE={}
for directory in (ROOT/'reconstruction').iterdir():
 path=directory/'provenance.json'
 if path.is_file() and directory.name!='terminal_reset':
  proof=json.loads(path.read_text());STATE.update({int(k,16):v for k,v in proof.get('state',{}).items() if isinstance(v,str) and re.fullmatch(r'[0-9a-f]{4}',k) and int(k,16)>=0x1000})
STATE.update({0x1d18:'csi_terminal_id',0x1d32:'attributes_normal_value',0x7a8c:'reset_video_cells',0xce02:'reset_shadow_bytes',0x1d46:'reset_status_hidden',0x3254:'reset_wide_mode',0x469a:'reset_geometry_initialized',0x7a6e:'reset_underline_supported',0x7a90:'reset_crtc_port',0x1d2c:'reset_underline_enabled',0x7a86:'reset_underline_suppressed',0x1d2e:'reset_configured_wide',0x9016:'reset_saved_scroll',0x903c:'reset_saved_duplex',0x1d26:'reset_duplex',0xcc4a:'reset_scratch',0xcf86:'screen_line_flags'})
CODE_POINTERS={0xbb8f:'terminal_reset_input_attribute',0xbb9b:'terminal_reset_input_plain'}
# This pointer is stored directly in a BP local, rather than first loaded into
# AX/BX/etc. The generic immediate scan below must not omit its relocation.
STATE[0xd464]='terminal_reset_script_label'
# Discover all native DS references and immediate data pointers for relocatable
# OMF storage. Unknown semantics retain address-based names, never guessed data.
for _,start,end in UNITS:
 p=ROOT/f'analysis/pcplus-main/functions/{hex(0x10000+start)}.asm';listing=p.read_text()
 for address in re.findall(r'\[([^]\n]+)\]',listing):
  if 'BP' in address:continue
  for token in re.findall(r'0x([0-9a-f]+)',address):
   value=int(token,16)
   if value>=0x1000:STATE.setdefault(value,f'reset_data_{value:04x}')
 for value in re.findall(r'(?:MOV|LEA) (?:AX|BX|CX|DX|SI|DI), (0x[0-9a-f]+)',listing):
  address=int(value,16)
  if 0x1000<=address<0xf000 and address not in CODE_POINTERS:STATE.setdefault(address,f'reset_data_{address:04x}')

def main():
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 used_state=set()
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
   header=['; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.','BITS 16','CPU 8086','%ifdef TERMINAL_RESET_OMF','SEGMENT _TEXT public class=CODE use16','global '+FUNCTIONS[start]]
   calls=set()
   for _,text in rows:
    m=re.fullmatch(r'(?:call|jmp(?: near)?) (0x[0-9a-f]+)',text)
    if m:calls.add(int(m[1],16))
   external={k:v for k,v in (FUNCTIONS|SERVICES).items() if k in calls}
   external.update({k:v for k,v in CODE_POINTERS.items() if any(f'0x{k:x}' in text for _,text in rows)})
   for v in external.values():header.append('extern '+v)
   state_used={k:v for k,v in STATE.items() if any(re.search(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',t) for _,t in rows if not re.match(r'(?:j\w+|call)\s',t))}
   used_state.update(state_used)
   for v in state_used.values():header.append('extern '+v)
   header+=['%define short','%else',f'ORG 0x{start:x}']
   for k,v in external.items():header.append(f'%define {v} 0x{k:x}')
   for k,v in state_used.items():header.append(f'%define {v} 0x{k:x}')
   header+=['%endif','%include "encodings.inc"',FUNCTIONS[start]+':']
   for at,text in rows:
    if not re.match(r'(?:j\w+|call)\s',text):
     for k,v in state_used.items():text=re.sub(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',v,text)
    branch=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
    if branch:
     target=int(branch[3],16)
     symbol=f'L_{target:04x}' if start<=target<end else (FUNCTIONS|SERVICES)[target]
     text=branch[1]+' '+(branch[2]+' ' if branch[2] else '')+symbol
    for k,v in CODE_POINTERS.items():text=text.replace(f'0x{k:x}',v)
    header.append(f'L_{at:04x}: '+text)
   path=SOURCE/(name+'.asm');path.write_text('\n'.join(header)+'\n')
   subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(work/'whole.bin')],check=True)
   assert (work/'whole.bin').read_bytes()==blob,name
   manifest['units'].append({'file':str(path.relative_to(ROOT)),'start':start,'end':end,'source_file_offset':file_start,'bytes':len(blob),'instructions':len(rows),'sha256':hashlib.sha256(blob).hexdigest(),'matched_original':True})
 manifest['state']={f'{k:04x}':STATE[k] for k in sorted(used_state)}
 manifest['rea_exports']={}
 for _,start,_ in UNITS:
  path=ROOT/f'analysis/pcplus-main/functions/{hex(0x10000+start)}-asm.json'
  evidence=json.loads(path.read_text())['structuredContent']
  manifest['rea_exports'][hex(start)]={'evidence_id':evidence['evidence_id'],'analysis_artifact_sha256':evidence['subject']['digest']['sha256'],'scope':'Saved static REA export, independently verified against original file bytes.'}
 manifest['limitations']=['Nonzero reset requires original profile KEY loader0cd2; no fake replacement linked.','Geometry far allocation/free/application errors and visible status formatting remain explicit dependencies.','Soft reset can complete only on tested stable geometry/status-hidden path; full profile reset currently stops at mandatory keymap boundary.','Unknown data semantics retain address-based symbols; diagnostic storage/strings synthetic, no private/original data copied.']
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Recovered',sum(u['bytes'] for u in manifest['units']),'bytes')
if __name__=='__main__':main()
