#!/usr/bin/env python3
"""Explicit analyst-only regeneration from SHA-verified original, never called by builds."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
assert hashlib.sha256(image).hexdigest()==SHA
overlay=next(x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==21)
units=[('fwrite',0x86ac,0x87ad,None),('fflush',0x8c54,0x8cc6,None),('fclose',0x8318,0x83c6,None),('write',0xa368,0xa4a6,None),('close',0x868c,0x86ac,None),('free_buffer',0xa000,0xa02a,None),('putc',0x91a6,0x9286,None),('seek',0xa22e,0xa2a8,None),('error_zero',0x9420,0x9428,None),('error_value',0x9435,0x9442,None),('stack_available',0xa8d4,0xa8e6,None),('copy_wrapper',0x4735,0x4748,None),('copy',0x85b4,0x85fc,None),('periodic',0xdb2a,0xdbbc,'files_receive_resume'),('tail',0xddf6,0xde58,'files_receive_success')]
state={0x7b29:'files_handle_limit',0x7b2b:'files_handle_flags',0x7b6a:'files_stream_table',0x7c0a:'files_extra_table',0x7c0e:'files_extra_temporary',0x7b72:'files_stdout',0x7b7a:'files_stderr',0x7b8a:'files_aux',0x7dd6:'files_stack_floor',0x8e24:'files_overlay_cookie',0x8e26:'files_overlay_callback',0x7ae4:'files_temp_prefix',0x7ae6:'files_temp_separator',0x39c0:'files_receive_buffer',0xcbaa:'files_receive_stream',0xcd34:'files_receive_used',0x9006:'files_receive_size_low',0x9008:'files_receive_size_high',0x8ffa:'files_receive_total_low',0x8ffc:'files_receive_total_high',0x1d1e:'files_receive_flow_switch'}
services={0x86ac:'files_fwrite',0x8c54:'files_fflush',0x8318:'files_fclose',0xa368:'files_write',0x868c:'files_close',0xa000:'files_free_buffer',0x91a6:'files_putc',0xa22e:'files_seek',0x9420:'files_error_zero',0x9435:'files_error_value',0x9448:'program_map_error',0xa8d4:'files_stack_available',0x4735:'files_copy_wrapper',0x85b4:'files_copy',0x92a4:'files_heap_free',0xa71a:'files_allocate_buffer',0x8cce:'files_flush_all',0xa8bc:'files_stack_failure',0x8268:'files_string_copy',0x8bea:'files_string_append',0x8e6c:'files_unsigned_decimal',0x9086:'files_unlink',0xe498:'files_receive_status',0xabfa:'files_receive_flow',0x3af8:'files_receive_timestamp'}
exits={0xdc07:'files_receive_resume',0xd734:'files_receive_failure',0xda9e:'files_receive_success',0xd731:'files_receive_stack_failure'}
alladdresses=set();decoded=[]
with tempfile.TemporaryDirectory() as directory:
 work=Path(directory)
 def assemble(text,address):
  (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {address}\n%include "encodings.inc"\n{text}\n')
  p=subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
  return (work/'one.bin').read_bytes() if p.returncode==0 else None
 for name,start,end,tail in units:
  offset=0x1200+start if start<0xd000 else overlay['source_file_offset']+start-overlay['relative_load_segment']*16
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
 names={address:f'files_at_{address:04x}' for address in alladdresses}
 names.update(services);names.update(exits)
 # Entry services correspond to exact instruction labels, not duplicate callback bodies.
 layout={**state,**services,**exits,**{a:n for a,n in names.items() if a in alladdresses}}
 for name,start,end,tail,offset,blob,rows in decoded:
  own={a for a,_ in rows};needed=set();lines=[]
  for address,text in rows:
   m=re.fullmatch(r'(j\w+|call|loop\w*)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
   if m:
    target=int(m[3],16);symbol=names[target];needed.add(target);text=m[1]+' '+((m[2]+' ') if m[2] else '')+symbol
   for original,symbol in state.items():
    if False:continue
    if re.search(rf'0x{original:x}\b',text) or (original>=0x8000 and f'-0x{0x10000-original:x}]' in text):needed.add(original)
    text=re.sub(rf'0x{original:x}\b',symbol,text)
    if original>=0x8000:text=text.replace(f'-0x{0x10000-original:x}]',f'+{symbol}]')
   lines.append(names[address]+': '+text)
  header=['; Exact original receiver/CRT file instructions; analyst regeneration is explicit.', 'BITS 16','CPU 8086','%ifdef TRANSFER_FILES_OMF','SEGMENT _TEXT public class=CODE use16','%define short']
  header+=['global '+names[a] for a in sorted(own)]+['extern '+layout[a] for a in sorted(needed-own)]
  if tail:header+=['extern '+tail] if tail not in [layout[a] for a in needed-own] else []
  header+=['%else',f'ORG 0x{start:x}']+['%%define %s 0x%x'%(layout[a],a) for a in sorted(needed-own)]+['%endif','%include "encodings.inc"']
  footer=['%ifdef TRANSFER_FILES_OMF','jmp '+tail,'%endif'] if tail else []
  (OUT/(name+'.asm')).write_text('\n'.join(header+lines+footer)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(OUT/(name+'.asm')),'-o',str(work/'flat')],check=True)
  assert (work/'flat').read_bytes()==blob,name
 evidence=json.loads(json.loads((ROOT/'analysis/pcplus-overlay-anchored-21/functions/0x1d6a4-asm.json').read_text())['content'][0]['text'])['evidence_id']
 proof={'source_sha256':SHA,'overlay':21,'receiver_evidence_id':evidence,'units':[{'source':n+'.asm','start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'source_file_offset':o,'sha256':hashlib.sha256(b).hexdigest()} for n,s,e,t,o,b,r in decoded],'state':{hex(a):n for a,n in state.items() if a not in (0x40b1,0x40b9)},'boundaries':{hex(a):n for a,n in {**services,**exits}.items()}}
 proof['supporting_evidence']=[]
 for address in ['186ac','18318','18c54','1a368','1868c','191a6','1a000']:
  path=ROOT/'analysis/pcplus-main/functions'/(f'0x{address}-asm.json')
  evidence=json.loads(json.loads(path.read_text())['content'][0]['text'])['evidence_id']
  proof['supporting_evidence'].append({'export':str(path.relative_to(ROOT)),'evidence_id':evidence})
 proof['limitations']=['CRT source accepts unchecked FILE pointers and sizes; standalone diagnostic initializes only bounded synthetic FILE objects.','Heap allocation/free, temporary-file cleanup and full receiver UI/flow/session remain explicit boundaries.','Periodic fwrite uses one full-sized element and rejects short writes; final receiver tail ignores fwrite/fclose errors.']
 (OUT/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',sum(e-s for n,s,e,t,o,b,r in decoded),'exact bytes')
