#!/usr/bin/env python3
"""Explicit analyst-only regeneration from SHA-verified original, never called by builds."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
assert hashlib.sha256(image).hexdigest()==SHA
overlay=next(x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==21)
units=[('parse_telink',0xe4c2,0xe529,None),('parse_ymodem',0xe52a,0xe5d9,None),('send_telink',0xe5da,0xe762,None),('send_ymodem',0xe762,0xe878,None),('end_ymodem',0xefcc,0xf01b,None),('signed_format',0x9ae8,0x9af2,None),('basename',0x3ea4,0x3ed9,None),('send_zero',0x40aa,0x40b1,None),('strncpy',0x9888,0x98b0,None),('decimal_thunk',0x9b32,0x9b35,None)]
state={0x3996:'metadata_protocol',0x39c0:'metadata_buffer_pointer',0x9006:'metadata_size_low',0x9008:'metadata_size_high',0xcbae:'metadata_crc_high',0xcbb2:'metadata_crc_low',0xcd94:'metadata_checkpoint',0xcd76:'metadata_date',0xcd3a:'metadata_time',0xcb68:'metadata_filename',0xcb56:'metadata_batch_end',0x7920:'metadata_identification'}
services={0xe4c2:'metadata_parse_telink',0xe52a:'metadata_parse_ymodem',0xe5da:'metadata_send_telink',0xe762:'metadata_send_ymodem',0xefcc:'metadata_end_ymodem',0x9ae8:'metadata_signed_format',0xa5e8:'meta_keys_decimal_core',0x3ea4:'metadata_basename',0x83c6:'program_strrchr',0x40aa:'metadata_send_zero',0x9888:'metadata_strncpy',0x9b32:'metadata_decimal_thunk',0xa7ce:'directory_dial_integer_original',0x3b56:'metadata_stat_file',0x3f4b:'metadata_local_cancel',0x4861:'metadata_carrier',0x9065:'metadata_unwind',0xf03e:'receive_drain',0xab0b:'metadata_transmit_byte',0xaad9:'metadata_timed_byte',0x5c77:'_transfer_crc_buffer_original',0xee10:'metadata_display_start'}
RESIDENT={'signed_format','basename','send_zero','strncpy','decimal_thunk'}
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
 names={address:f'metadata_at_{address:04x}' for address in alladdresses}
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
  header=['; Exact original transfer metadata instructions; analyst regeneration is explicit.', 'BITS 16','CPU 8086','%ifdef TRANSFER_METADATA_OMF','SEGMENT _TEXT public class=CODE use16','%define short']
  header+=['global '+names[a] for a in sorted(own)]+['extern '+layout[a] for a in sorted(needed-own)]
  if tail:header+=['extern '+tail] if tail not in [layout[a] for a in needed-own] else []
  header+=['%else',f'ORG 0x{start:x}']+['%%define %s 0x%x'%(layout[a],a) for a in sorted(needed-own)]+['%endif','%include "encodings.inc"']
  footer=['%ifdef TRANSFER_METADATA_OMF','jmp '+tail,'%endif'] if tail else []
  (OUT/(name+'.asm')).write_text('\n'.join(header+lines+footer)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(OUT/(name+'.asm')),'-o',str(work/'flat')],check=True)
  assert (work/'flat').read_bytes()==blob,name
 proof={'source_sha256':SHA,'overlay':21,'units':[{'source':n+'.asm','start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'source_file_offset':o,'sha256':hashlib.sha256(b).hexdigest(),'region':'resident' if n in RESIDENT else 'overlay21'} for n,s,e,t,o,b,r in decoded],'state':{hex(a):n for a,n in state.items()},'boundaries':{hex(a):n for a,n in services.items()}}
 proof['supporting_evidence']=[]
 for address in ['1e4c2','1e52a','1e5da','1e762','1efcc']:
  path=ROOT/'analysis/pcplus-overlay-anchored-21/functions'/('0x'+address+'-asm.json');r=json.loads(path.read_text());ev=r.get('structuredContent',{}).get('evidence_id')
  if not ev:ev=json.loads(r['content'][0]['text'])['evidence_id']
  proof['supporting_evidence'].append({'export':str(path.relative_to(ROOT)),'evidence_id':ev})
 for name in ['format-entry','format-core','strncpy','zero','basename']:
  path=ROOT/'analysis/pcplus-transfer-metadata'/(name+'.json');r=json.loads(path.read_text());ev=r.get('structuredContent',{}).get('evidence_id')
  if not ev:ev=json.loads(r['content'][0]['text'])['evidence_id']
  proof['supporting_evidence'].append({'export':str(path.relative_to(ROOT)),'evidence_id':ev})
 proof['reused_sources']=['reconstruction/meta_keys/decimal_core.asm','reconstruction/directory_dial/integer.asm','reconstruction/program_exec/strrchr.asm','reconstruction/transfer_receive/drain.asm','reconstruction/transfer_blocks/crc_update.asm','reconstruction/transfer_blocks/crc_finish.asm','reconstruction/transfer_blocks/crc_buffer.asm','reconstruction/transfer_blocks/crc_table.asm']
 proof['limitations']=['Exact original metadata helpers, not a complete batch protocol owner or live terminal integration.','Original unbounded filename copies, permissive/wrapping signed decimal parse and missing end-header ACK retries remain unchanged; maintained batch_header codec is separate.','Hardware, file-stat, cancel/carrier, nonlocal unwind, timing and display remain explicit diagnostic boundaries.']
 (OUT/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',sum(e-s for n,s,e,t,o,b,r in decoded),'exact new bytes')
