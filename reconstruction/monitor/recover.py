#!/usr/bin/env python3
"""Explicit analyst-only regeneration from SHA-verified original, never called by builds."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
assert hashlib.sha256(image).hexdigest()==SHA
units=[('owner',0x1aaa,0x1bbd,None),('resolver',0x353d,0x35a6,None),('yesno',0x6dde,0x6e59,None)]
state={0x332c:'monitor_active',0x1d6e:'monitor_hook',0x1f7e:'monitor_prompt_attribute',0x1f7c:'monitor_choice_attribute',0x329e:'monitor_window_descriptor',0x422a:'monitor_prompt_text',0x468b:'monitor_dump_mode',0x468e:'monitor_dump_name',0x397a:'monitor_help_context',0x8e20:'monitor_rx_count',0x1d34:'monitor_special_attribute',0x1f70:'monitor_active_attribute',0x1d32:'monitor_normal_attribute',0xcffa:'monitor_key',0x324c:'monitor_environment_name_pointer',0x8f09:'monitor_path_before',0x8f0a:'monitor_path',0x471c:'monitor_probe_mode',0x471e:'monitor_separator',0x7a9a:'monitor_yes_label',0x7a96:'monitor_no_label',0x7a6c:'monitor_cursor_visibility',0x7a9e:'monitor_prompt_key'}
services={0x1aaa:'monitor_run_original',0x353d:'monitor_resolve_original',0x6dde:'monitor_yesno_original',0x2fb8:'monitor_status',0x24e2:'monitor_clear',0x3fc7:'monitor_save_window',0x6bf0:'monitor_draw_text',0x4015:'monitor_restore_window',0x841a:'monitor_open',0x8318:'monitor_close',0xaa65:'monitor_dequeue',0x0730:'monitor_render',0x8436:'monitor_putc',0x651a:'monitor_keyboard_available',0x64fe:'monitor_keyboard_read',0x1604:'monitor_dispatch_key',0x8e12:'monitor_getenv',0x8268:'program_strcpy',0x8d18:'program_strlen',0x8bea:'program_strcat',0x6b5a:'monitor_prompt_lock',0x6b42:'monitor_prompt_unlock',0x6e78:'monitor_cursor_position',0x6dca:'monitor_cursor_6dca',0x6e5a:'monitor_cursor_6e5a',0x376d:'monitor_beep'}
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
 names={address:f'monitor_at_{address:04x}' for address in alladdresses}
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
  header=['; Exact original raw monitor instructions; analyst regeneration is explicit.', 'BITS 16','CPU 8086','%ifdef MONITOR_OMF','SEGMENT _TEXT public class=CODE use16','%define short']
  header+=['global '+names[a] for a in sorted(own)]+['extern '+layout[a] for a in sorted(needed-own)]
  if tail:header+=['extern '+tail] if tail not in [layout[a] for a in needed-own] else []
  header+=['%else',f'ORG 0x{start:x}']+['%%define %s 0x%x'%(layout[a],a) for a in sorted(needed-own)]+['%endif','%include "encodings.inc"']
  footer=['%ifdef MONITOR_OMF','jmp '+tail,'%endif'] if tail else []
  (OUT/(name+'.asm')).write_text('\n'.join(header+lines+footer)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(OUT/(name+'.asm')),'-o',str(work/'flat')],check=True)
  assert (work/'flat').read_bytes()==blob,name
 proof={'source_sha256':SHA,'units':[{'source':n+'.asm','start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'source_file_offset':o,'sha256':hashlib.sha256(b).hexdigest(),'region':'resident'} for n,s,e,t,o,b,r in decoded],'state':{hex(a):n for a,n in state.items()},'boundaries':{hex(a):n for a,n in services.items()}}
 proof['supporting_evidence']=[]
 for address in ['11aaa','1353d','16dde']:
  path=ROOT/'analysis/pcplus-main/functions'/('0x'+address+'-asm.json');r=json.loads(path.read_text());ev=r.get('structuredContent',{}).get('evidence_id')
  if not ev:ev=json.loads(r['content'][0]['text'])['evidence_id']
  proof['supporting_evidence'].append({'export':str(path.relative_to(ROOT)),'evidence_id':ev})
 proof['reused_sources']=['reconstruction/program_exec/strcpy.asm','reconstruction/program_exec/strlen.asm','reconstruction/program_exec/strcat.asm']
 proof['limitations']=['Exact503nativeinstructionbytes:275monitor,105resolver,123Y/Nprompt.','UARTdequeue,keyboard,render,UIandCRTareexplicitmemorydiagnosticboundaries;noclaimofliveUARTorfileowner.','Originaloverwritebinarywb,nullopen/ignoredIOerrors,unboundedresolvercopiesandsynchronouslooparepreservedonlyforcomparison.']
 (OUT/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',sum(e-s for n,s,e,t,o,b,r in decoded),'exact new monitor bytes')
