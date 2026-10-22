#!/usr/bin/env python3
"""Analyst-only recovery from a verified original; ordinary builds never call it."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
START,END=0x56fe,0x57ae
STATE={0x397a:'local_window_help_context',0x32b2:'local_window_descriptor',
 0x1f64:'local_window_box_attribute',0x232c:'local_window_keyboard_table',
 0x232a:'local_window_text',0x1f66:'local_window_text_attribute',
 0x1d6e:'local_window_hook_enabled',0x1d70:'local_window_hook_character',
 0x2328:'local_window_status'}
SERVICES={0x3fc7:'local_window_save',0x4056:'local_window_draw',
 0x780e:'local_window_keyboard_select',0x6bf0:'local_window_write',
 0x75e8:'local_window_format',0x3226:'local_window_status_draw',
 0x6530:'local_window_key_poll',0x64fe:'local_window_key_read',
 0x4015:'local_window_restore'}

def main():
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 blob=image[0x1200+START:0x1200+END];rows=[]
 with tempfile.TemporaryDirectory() as directory:
  work=Path(directory);(work/'part').write_bytes(blob)
  def assemble(text,at):
   (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n{text}\n')
   r=subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
   return (work/'one.bin').read_bytes() if r.returncode==0 else None
  for line in subprocess.check_output(['ndisasm','-b16',f'-o{START}',str(work/'part')],text=True).splitlines():
   m=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line);assert m,line
   at,raw,text=int(m[1],16),bytes.fromhex(m[2]),m[3]
   assert not text.startswith('db ')
   if raw[0]==0xeb:text=text.replace('jmp ','jmp short ',1)
   elif raw[0]==0xe9:text=text.replace('jmp ','jmp near ',1)
   elif 0x70<=raw[0]<=0x7f:text=text.replace(' ',' short ',1)
   if assemble(text,at)!=raw:
    op,args=text.split(' ',1)
    candidates=[op+'_load '+args]+[re.sub(r',(-?0x[0-9a-f]+)$',rf',strict {width} \1',text) for width in ('word','byte')]
    text=next((candidate for candidate in candidates if assemble(candidate,at)==raw),None)
    assert text is not None,(hex(at),raw.hex())
   rows.append((at,text))
  names={at:f'local_window_at_{at:04x}' for at,_ in rows};names[START]='aspect_local_window'
  names.update(SERVICES)
  lines=['; Recovered native Alt-Z window, not original source. See provenance.json.',
   'BITS 16','CPU 8086','%ifdef LOCAL_WINDOW_OMF','%ifdef LOCAL_WINDOW_FAR',
   'SEGMENT ASPECT_CODE public class=FARCODE use16','%else','SEGMENT _TEXT public class=CODE use16','%endif',
   'global aspect_local_window']+['extern '+name for name in [*STATE.values(),*SERVICES.values()]]
  lines+=['%else',f'ORG 0x{START:x}']+[f'%define {name} 0x{at:x}' for at,name in {**STATE,**SERVICES}.items()]
  lines+=['%endif','%include "encodings.inc"']
  for at,text in rows:
   branch=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
   if branch:text=branch[1]+' '+((branch[2]+' ') if branch[2] else '')+names[int(branch[3],16)]
   for address,name in STATE.items():text=re.sub(rf'0x{address:x}\b',name,text)
   lines.append(names[at]+': '+text)
  source=OUT/'window.asm';source.write_text('\n'.join(lines)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(work/'flat')],check=True)
  assert (work/'flat').read_bytes()==blob
 proof=dict(source_sha256=EXPECTED,start=hex(START),end_exclusive=hex(END),file_offset=0x1200+START,
  bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),instructions=len(rows),
  state={hex(k):v for k,v in STATE.items()},services={hex(k):v for k,v in SERVICES.items()},
  evidence_id='ev_8c6397f7450acd0fef77d580471c22c3d1d6365d1693861c4ba15c016a200e06',
  limitations=['Recovered instruction source only; window/status/formatting and keyboard-table callbacks are explicit external services.','No modal UI integration, physical BIOS/UART or complete application acceptance.'])
 (OUT/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',len(blob),'exact native local-window bytes')

if __name__=='__main__':main()
