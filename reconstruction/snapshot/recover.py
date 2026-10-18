#!/usr/bin/env python3
"""Explicit analyst-only regeneration from SHA-verified original, never called by builds."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
assert hashlib.sha256(image).hexdigest()==SHA
units=[('writer',0x3496,0x353d,None),('row',0x3446,0x3496,None),('copy',0x64b8,0x64fd,None),('keyboard',0x1310,0x132e,None),('video_begin',0x77be,0x77d2,None),('video_end',0x77ae,0x77bd,None)]
state={0x7a8e:'snapshot_cga_status_port',0xcdfa:'snapshot_shadow_enabled',0x325a:'snapshot_shadow_columns',0x5dea:'snapshot_shadow_offset',0x5dec:'snapshot_shadow_segment',0x7a7a:'snapshot_video_stride',0x7a78:'snapshot_video_segment',0x3250:'snapshot_video_columns',0x7a74:'snapshot_rows',0x334c:'snapshot_special_row',0x42c0:'snapshot_status_pointer',0x4716:'snapshot_append_mode',0x1e5f:'snapshot_filename',0x4719:'snapshot_newline',0x2b3a:'snapshot_error_text'}
services={0x3496:'snapshot_write_original',0x3446:'snapshot_row_original',0x64b8:'snapshot_copy_original',0x1310:'snapshot_keyboard_original',0x841a:'snapshot_open',0x33f3:'snapshot_prepare_screen',0x31bb:'snapshot_status',0x8268:'program_strcpy',0x8d18:'program_strlen',0x8e88:'snapshot_puts',0x8318:'snapshot_close',0x6bb6:'snapshot_wait_key',0x2fb8:'snapshot_refresh',0x427f:'snapshot_error',0x77be:'snapshot_video_begin',0x77ae:'snapshot_video_end',0xdae:'snapshot_keyboard_state'}
RESIDENT={n for n,_,_,_ in units}
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
 names={address:f'snapshot_at_{address:04x}' for address in alladdresses}
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
  header=['; Exact original screen snapshot instructions; analyst regeneration is explicit.', 'BITS 16','CPU 8086','%ifdef SNAPSHOT_OMF','SEGMENT _TEXT public class=CODE use16','%define short']
  header+=['global '+names[a] for a in sorted(own)]+['extern '+layout[a] for a in sorted(needed-own)]
  if tail:header+=['extern '+tail] if tail not in [layout[a] for a in needed-own] else []
  header+=['%else',f'ORG 0x{start:x}']+['%%define %s 0x%x'%(layout[a],a) for a in sorted(needed-own)]+['%endif','%include "encodings.inc"']
  footer=['%ifdef SNAPSHOT_OMF','jmp '+tail,'%endif'] if tail else []
  (OUT/(name+'.asm')).write_text('\n'.join(header+lines+footer)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(OUT/(name+'.asm')),'-o',str(work/'flat')],check=True)
  assert (work/'flat').read_bytes()==blob,name
 proof={'source_sha256':SHA,'units':[{'source':n+'.asm','start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'source_file_offset':o,'sha256':hashlib.sha256(b).hexdigest(),'region':'resident'} for n,s,e,t,o,b,r in decoded],'state':{hex(a):n for a,n in state.items()},'boundaries':{hex(a):n for a,n in services.items()}}
 proof['supporting_evidence']=[]
 for address in ['13496','13446','164b8','177be','177ae','146ba','16d1a']:
  path=ROOT/'analysis/pcplus-main/functions'/('0x'+address+'-asm.json');r=json.loads(path.read_text());ev=r.get('structuredContent',{}).get('evidence_id')
  if not ev:ev=json.loads(r['content'][0]['text'])['evidence_id']
  proof['supporting_evidence'].append({'export':str(path.relative_to(ROOT)),'evidence_id':ev})
 proof['keyboard_provenance']='Original resident1310..132d decoded from SHA-verified EXE bytes, selected by verified DS44e0 scan22h entry. No saved REA function export for this wrapper.'
 proof['reused_sources']=['reconstruction/program_exec/strcpy.asm','reconstruction/program_exec/strlen.asm']
 proof['limitations']=['Exact unbounded originals; no live checked file owner.','Native FILE/UI/video mode services remain explicit diagnostic boundaries; output geometry requires maintained validation.']
 (OUT/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',sum(e-s for n,s,e,t,o,b,r in decoded),'exact new snapshot bytes')
