#!/usr/bin/env python3
"""Explicit analyst step; ordinary builds never read the original executable."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
START,END=0xf05c,0xf1fa
STATE={0x1b84:'line_port_port',0x1b86:'line_port_baud',0x1b88:'line_port_parity',0x1b8a:'line_port_stop',0x1b8c:'line_port_bits'}
CALLS={0x376d:'line_port_bell',0xadba:'line_port_quiesce'}
def main():
 raw=(ROOT/'analysis/pcplus-install/PCPLUS.EXE').read_bytes();digest=hashlib.sha256(raw).hexdigest();assert digest=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 manifest=json.loads((ROOT/'analysis/pcplus-overlay-entry-images/manifest.json').read_text());image=next(x for x in manifest['images']if x['overlay']==20);region=next(x for x in image['source_ranges']if x['role']=='overlay-20')
 offset=region['source_file_offset']+START-region['relative_address'];blob=raw[offset:offset+END-START]
 with tempfile.TemporaryDirectory() as name:
  work=Path(name);(work/'code.bin').write_bytes(blob)
  decoded=subprocess.check_output(['ndisasm','-b16',f'-o{START}',str(work/'code.bin')],text=True)
  def assemble(text,at):
   (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n'+text+'\n')
   p=subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
   return (work/'one.bin').read_bytes()if p.returncode==0 else None
  rows=[]
  for line in decoded.splitlines():
   m=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line);assert m,line
   at,encoded,text=int(m[1],16),bytes.fromhex(m[2]),m[3];assert not text.startswith('db ')
   instruction=text
   if encoded[0]==0xeb:instruction=instruction.replace('jmp ','jmp short ',1)
   elif encoded[0]==0xe9:instruction=instruction.replace('jmp ','jmp near ',1)
   elif 0x70<=encoded[0]<=0x7f:instruction=instruction.replace(' ',' short ',1)
   if assemble(instruction,at)!=encoded:
    candidates=[]
    if len(encoded)==2 and encoded[1]>=0xc0 and encoded[0] in (2,3,10,11,18,19,26,27,34,35,42,43,50,51,58,59,138,139):
     op,args=text.split(' ',1);candidates.append(op+'_load '+args)
    for width in ('word','byte'):candidates.append(re.sub(r',(-?0x[0-9a-f]+)$',rf',strict {width} \1',instruction))
    instruction=next((c for c in candidates if assemble(c,at)==encoded),None);assert instruction is not None,(at,text,encoded.hex())
   rows.append((at,instruction))
  lines=['; Native 2.01 Alt-P key selector; wrapper/save/hardware owners are separate.','BITS 16','CPU 8086','%ifdef LINE_PORT_OMF','GROUP DGROUP _DATA','%ifdef LINE_PORT_FAR_BANK','SEGMENT LINE_PORT_CODE public align=16 class=FARCODE use16','%else','SEGMENT _TEXT public class=CODE use16','%endif','global line_port_key']
  lines+=['extern '+n+':wrt DGROUP' for n in STATE.values()]+['extern '+n for n in CALLS.values()]
  lines+=['%else',f'ORG 0x{START:x}']+['%define '+n+' '+hex(k)for k,n in (STATE|CALLS).items()]+['%endif','%include "encodings.inc"','line_port_key:']
  for at,text in rows:
   for k,n in STATE.items():text=re.sub(r'(?<![0-9a-f])'+hex(k)+r'(?![0-9a-f])',n,text)
   branch=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
   if branch:
    target=int(branch[3],16);symbol=f'L_{target:04x}'if START<=target<END else CALLS[target]
    text=branch[1]+' '+(branch[2]+' 'if branch[2]else'')+symbol
   lines.append(f'L_{at:04x}: '+text)
  lines+=['%ifdef LINE_PORT_OMF','SEGMENT _DATA public class=DATA use16','%endif'];path=ROOT/'reconstruction/line_port/key.asm';path.write_text('\n'.join(lines)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(work/'whole.bin')],check=True)
  assert(work/'whole.bin').read_bytes()==blob
 r=dict(original_sha256=digest,overlay=20,entry=START,end_exclusive=END,source_file_offset=offset,bytes=len(blob),instructions=len(rows),sha256=hashlib.sha256(blob).hexdigest(),state={hex(k):v for k,v in STATE.items()},services={hex(k):v for k,v in CALLS.items()},REA=dict(analysis_image_sha256=image['sha256'],key_dossier='ev_394c7be3e6e48c412d327c081c2588fb78c243c68f1ec47359b8a96b56c5c89b',key_assembly='ev_c0d69340f77c15c75b08ec130b186bfc7478b2f47d575591fedb5914b1c152ca',wrapper_dossier='ev_fa051b50c21b78d453b383b0aed32c34dacdaac5468804f8c93c2ea749f26519',save_dossier='ev_629b21d05031dec974bf7ce423600c150ebd02a169f4e50ec4f121c0245483b0'),limitations=['Static synthetic overlay image was analyzed, never executed. Exact body bytes independently match identified original file region.','Bell and UART quiesce are explicit external boundaries. Popup/frame/render/save/apply/hardware and application integration remain separate.'])
 (ROOT/'reconstruction/line_port/provenance.json').write_text(json.dumps(r,indent=2)+'\n');print('Recovered native Line/Port selector',len(blob),'bytes',len(rows),'instructions')
if __name__=='__main__':main()
