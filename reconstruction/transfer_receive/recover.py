#!/usr/bin/env python3
"""Explicit analyst-only regeneration from SHA-verified original, never called by builds."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
assert hashlib.sha256(image).hexdigest()==SHA
overlay=next(x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==21)
units=[('validate',0xd8e8,0xda31,'receive_validated'),('accept',0xdaea,0xdb2a,'receive_buffer_full'),('reject',0xdbbc,0xdc28,'receive_complete'),('header',0xdc6a,0xdcfd,'receive_eot'),('ack',0x40b1,0x40c1,None),('drain',0xf03e,0xf050,None),('eot',0xdd4a,0xddf6,'receive_disk_commit'),('cancel',0xf050,0xf070,None)]
state={0x3996:'receive_protocol',0x39c0:'receive_buffer_pointer',0x40b1:'receive_ack',0x40b9:'receive_nak',0x8e20:'receive_queued_count',0x8ffa:'receive_total_low',0x8ffc:'receive_total_high',0xcb2c:'receive_session_low',0xcb2e:'receive_session_high',0xcb5e:'receive_block_size',0xcbae:'receive_crc_high',0xcbb2:'receive_crc_low',0xcc46:'receive_wire_high',0xcc94:'receive_wire_low',0xcc9a:'receive_last_block',0xcc9c:'receive_wire_block',0xcd32:'receive_wire_complement',0xcd34:'receive_buffer_used',0xcd80:'receive_blocks_accepted',0xcd8a:'receive_error_count',0xcdcc:'receive_streaming_mode',0xcd94:'receive_jump_context'}
services={0x5c42:'transfer_crc_update_original',0x5c5c:'transfer_crc_finish_original',0xaad9:'receive_timed_byte',0x5ca0:'receive_header_byte',0xabca:'receive_flush_input',0x40b9:'receive_nak',0x40b1:'receive_ack',0xe498:'receive_status',0xf03e:'receive_drain',0xe322:'receive_progress',0xab0b:'receive_transmit_byte',0x6b72:'receive_delay',0xf050:'receive_control_status',0x9065:'receive_longjmp_boundary'}
exits={0xda31:'receive_validated',0xdb2a:'receive_buffer_full',0xdc28:'receive_complete',0xdcf1:'receive_retry_limit',0xd734:'receive_unsupported_control',0xdd4a:'receive_other_control',0xddf6:'receive_disk_commit'}
alladdresses=set();decoded=[]
with tempfile.TemporaryDirectory() as directory:
 work=Path(directory)
 def assemble(text,address):
  (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {address}\n%include "encodings.inc"\n{text}\n')
  p=subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
  return (work/'one.bin').read_bytes() if p.returncode==0 else None
 for name,start,end,tail in units:
  offset=0x1200+start if name=='ack' else overlay['source_file_offset']+start-overlay['relative_load_segment']*16
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
 names={address:f'receive_at_{address:04x}' for address in alladdresses}
 names.update(services);names.update(exits)
 # Entry services correspond to exact instruction labels, not duplicate callback bodies.
 layout={**state,**services,**exits,**{a:n for a,n in names.items() if a in alladdresses}}
 for name,start,end,tail,offset,blob,rows in decoded:
  own={a for a,_ in rows};needed=set();lines=[]
  for address,text in rows:
   m=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
   if m:
    target=int(m[3],16);symbol=names[target];needed.add(target);text=m[1]+' '+((m[2]+' ') if m[2] else '')+symbol
   for original,symbol in state.items():
    if original in (0x40b1,0x40b9):continue
    if re.search(rf'0x{original:x}\b',text) or (original>=0x8000 and f'-0x{0x10000-original:x}]' in text):needed.add(original)
    text=re.sub(rf'0x{original:x}\b',symbol,text)
    if original>=0x8000:text=text.replace(f'-0x{0x10000-original:x}]',f'+{symbol}]')
   lines.append(names[address]+': '+text)
  header=['; Exact original receiver instructions; analyst regeneration is explicit.', 'BITS 16','CPU 8086','%ifdef TRANSFER_RECEIVE_OMF','SEGMENT _TEXT public class=CODE use16','%define short']
  header+=['global '+names[a] for a in sorted(own)]+['extern '+layout[a] for a in sorted(needed-own)]
  if tail:header+=['extern '+tail] if tail not in [layout[a] for a in needed-own] else []
  header+=['%else',f'ORG 0x{start:x}']+['%%define %s 0x%x'%(layout[a],a) for a in sorted(needed-own)]+['%endif','%include "encodings.inc"']
  footer=['%ifdef TRANSFER_RECEIVE_OMF','jmp '+tail,'%endif'] if tail else []
  (OUT/(name+'.asm')).write_text('\n'.join(header+lines+footer)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(OUT/(name+'.asm')),'-o',str(work/'flat')],check=True)
  assert (work/'flat').read_bytes()==blob,name
 evidence=json.loads(json.loads((ROOT/'analysis/pcplus-overlay-anchored-21/functions/0x1d6a4-asm.json').read_text())['content'][0]['text'])['evidence_id']
 proof={'source_sha256':SHA,'overlay':21,'receiver_evidence_id':evidence,'units':[{'source':n+'.asm','start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'source_file_offset':o,'sha256':hashlib.sha256(b).hexdigest()} for n,s,e,t,o,b,r in decoded],'state':{hex(a):n for a,n in state.items() if a not in (0x40b1,0x40b9)},'boundaries':{hex(a):n for a,n in {**services,**exits}.items()}}
 proof['supporting_evidence']=[]
 for address,name in [('1f03e','input-drain'),('1f050','double-CAN-longjmp-request'),('15ca0','header-timeout-reader')]:
  path=ROOT/('analysis/pcplus-overlay-anchored-21/functions' if address.startswith('1f') else 'analysis/pcplus-main/functions')/(f'0x{address}-asm.json')
  evidence=json.loads(json.loads(path.read_text())['content'][0]['text'])['evidence_id']
  proof['supporting_evidence'].append({'name':name,'export':str(path.relative_to(ROOT)),'evidence_id':evidence})
 proof['limitations']=['Exact fragments preserve original behavior; OMF-only fallthrough jumps expose explicit diagnostic checkpoints.','The standalone host is a bounded memory UART/time/UI fixture, not a production transfer implementation.','Continued session, file flush/close, batch metadata application and original UI/nonlocal cancellation consumption are not implemented.']
 (OUT/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',sum(e-s for n,s,e,t,o,b,r in decoded),'exact bytes')
