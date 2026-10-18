#!/usr/bin/env python3
"""Explicit analyst-only regeneration from SHA-verified original, never called by builds."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
assert hashlib.sha256(image).hexdigest()==SHA
units=[('controller',0xd0d0,0xd270,None)]
state={0x7a82:'controller_rows',0x7a72:'controller_columns',0x2b6c:'controller_status_text',0x7500:'controller_open_mode',0x1d50:'printer_device',0x8ff0:'printer_stream',0x8e20:'controller_rx_count',0x1d18:'controller_terminal_id',0x8fe8:'controller_dec_family',0x9004:'controller_other_family',0x333e:'controller_cursor_flags'}
services={0xd0d0:'print_controller_original',0x6e5a:'controller_hide_cursor',0x765c:'controller_save',0x7682:'controller_restore',0x3226:'controller_status',0x841a:'printer_open',0x6530:'controller_key_available',0x64fe:'controller_read_key',0x0401:'controller_break',0xab0b:'controller_send_key',0xaa65:'controller_dequeue',0x36fc:'printer_byte_original',0x5ca0:'controller_next_byte',0x2f78:'controller_cursor_shape',0x8318:'printer_close'}
RESIDENT=set()
overlay={'source_file_offset':36016,'relative_load_segment':0}
exits={}
alladdresses=set();decoded=[]
with tempfile.TemporaryDirectory() as directory:
 work=Path(directory)
 def assemble(text,address):
  (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {address}\n%include "encodings.inc"\n{text}\n')
  p=subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
  return (work/'one.bin').read_bytes() if p.returncode==0 else None
 for name,start,end,tail in units:
  offset=0x1200+start if name in RESIDENT else overlay['source_file_offset']+start-overlay['relative_load_segment']*16
  blob=image[offset:offset+end-start];(work/'blob').write_bytes(blob)
  rows=[]
  for line in subprocess.check_output(['ndisasm','-b16',f'-o{start}',str(work/'blob')],text=True).splitlines():
   m=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line);assert m,line
   address,encoded,text=int(m[1],16),bytes.fromhex(m[2]),m[3]
   if encoded[0]==0xeb:text=text.replace('jmp ','jmp short ',1)
   elif encoded[0]==0xe9:text=text.replace('jmp ','jmp near ',1)
   elif 0x70<=encoded[0]<=0x7f:text=text.replace(' ',' short ',1)
   if assemble(text,address)!=encoded:
    candidates=[]
    if len(encoded)==2 and encoded[1]>=0xc0 and encoded[0] in (2,3,10,11,18,19,26,27,34,35,42,43,50,51,58,59,138,139):
     op,args=text.split(' ',1);candidates.append(op+'_load '+args)
    for width in ['word','byte']:candidates.append(re.sub(r',(-?0x[0-9a-f]+)$',rf',strict {width} \1',text))
    text=next((x for x in candidates if assemble(x,address)==encoded),None);assert text,(hex(address),encoded.hex())
   rows.append((address,text));alladdresses.add(address)
  decoded.append((name,start,end,tail,offset,blob,rows))
 names={address:f'print_at_{address:04x}' for address in alladdresses}
 names.update(services);names.update(exits)
 # Entry services correspond to exact instruction labels, not duplicate callback bodies.
 layout={**state,**services,**exits,**{a:n for a,n in names.items() if a in alladdresses}}
 for name,start,end,tail,offset,blob,rows in decoded:
  own={a for a,_ in rows};needed=set();lines=[]
  for address,text in rows:
   m=re.fullmatch(r'(j\w+|loop\w*|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
   if m:
    target=int(m[3],16);symbol=names[target];needed.add(target);text=m[1]+' '+((m[2]+' ') if m[2] else '')+symbol
   for original,symbol in state.items():
    if original in (0x40b1,0x40b9):continue
    if re.search(rf'0x{original:x}\b',text) or (original>=0x8000 and f'-0x{0x10000-original:x}]' in text):needed.add(original)
    text=re.sub(rf'0x{original:x}\b',symbol,text)
    if original>=0x8000:text=text.replace(f'-0x{0x10000-original:x}]',f'+{symbol}]')
   lines.append(names[address]+': '+text)
  header=['; Exact original dedicated-printer controller instructions; analyst regeneration is explicit.', 'BITS 16','CPU 8086','%ifdef PRINT_CONTROLLER_OMF','SEGMENT _TEXT public class=CODE use16','%define short']
  header+=['global '+names[a] for a in sorted(own)]+['extern '+layout[a] for a in sorted(needed-own)]
  if tail:header+=['extern '+tail] if tail not in [layout[a] for a in needed-own] else []
  header+=['%else',f'ORG 0x{start:x}']+['%%define %s 0x%x'%(layout[a],a) for a in sorted(needed-own)]+['%endif','%include "encodings.inc"']
  footer=['%ifdef PRINT_CONTROLLER_OMF','jmp '+tail,'%endif'] if tail else []
  (OUT/(name+'.asm')).write_text('\n'.join(header+lines+footer)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(OUT/(name+'.asm')),'-o',str(work/'flat')],check=True)
  assert (work/'flat').read_bytes()==blob,name
 proof={'source_sha256':SHA,'units':[{'source':n+'.asm','start':hex(st),'end_exclusive':hex(e),'bytes':e-st,'source_file_offset':o,'sha256':hashlib.sha256(b).hexdigest(),'region':'overlay12'} for n,st,e,t,o,b,rows in decoded],'state':{hex(a):n for a,n in state.items()},'boundaries':{hex(a):n for a,n in services.items()},'reused_sources':['reconstruction/printer/byte.asm']}
 proof['supporting_evidence']=[]
 for address in ['1d0d0']:
  path=ROOT/'analysis/pcplus-overlay-anchored-12/functions'/('0x'+address+'-asm.json');data=json.loads(path.read_text());ev=data.get('structuredContent',{}).get('evidence_id')
  if not ev:ev=json.loads(data['content'][0]['text'])['evidence_id']
  proof['supporting_evidence'].append({'export':str(path.relative_to(ROOT)),'evidence_id':ev})
 proof['limitations']=['Diagnostic CRT/UI/cursor boundaries are explicit fixtures, not a live printer.','Native null-open, ignored IO errors, blocking waits and unchecked escape buffering preserved.']
 (OUT/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',sum(e-st for n,st,e,t,o,b,rows in decoded),'exact new bytes')
