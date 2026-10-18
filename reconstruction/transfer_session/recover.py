#!/usr/bin/env python3
"""Explicit analyst-only regeneration from SHA-verified original, never called by builds."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
assert hashlib.sha256(image).hexdigest()==SHA
overlay=next(x for x in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if x['id']==21)
units=[('ordinary_gate',0xda31,0xda3a,None),('success_return',0xda9e,0xdaa7,None),('commit_gate',0xdcfd,0xdd4a,None),('entry',0xd6a4,0xd731,'session_failure_cleanup_argument'),('entry_display',0xd73c,0xd752,'session_handshake_enter'),('error_file_cleanup',0xd8ae,0xd8e8,None),('initialize',0xd656,0xd6a4,None),('totals',0xefb0,0xefcb,None),('handshake',0xd752,0xd87c,'session_context_enter'),('context',0xd87c,0xd8ae,'session_file_cleanup'),('retry',0xdc1f,0xdc6a,'session_header_checkpoint'),('wait',0xf070,0xf0d3,None),('timestamp',0xf0d4,0xf0df,None),('setjmp',0x9048,0x9065,None),('longjmp',0x9065,0x9086,None),('failure_return',0xd731,0xd73c,None)]
state={0x1d1e:'session_serial_gate',0x1ea0:'session_download_prefix',0x77f0:'session_open_mode',0x1b86:'session_baud_index',0x1f76:'session_ui_attribute',0x203e:'session_short_wait',0x3270:'session_baud_table',0x3272:'session_baud_table_high',0x3986:'session_wait_mode',0x3996:'session_protocol',0x39c0:'session_buffer_pointer',0x8e20:'session_queued_count',0x8ffa:'session_total_low',0x8ffc:'session_total_high',0x9006:'session_expected_low',0x9008:'session_expected_high',0x905a:'session_rate_low',0x905c:'session_rate_high',0x9062:'session_payload',0xcb2c:'session_bytes_low',0xcb2e:'session_bytes_high',0xcb3a:'session_state_cb3a',0xcb54:'session_state_cb54',0xcb56:'session_state_cb56',0xcbaa:'session_file_handle',0xcd34:'session_buffer_used',0xcc9a:'session_last_block',0xcd3a:'session_state_cd3a',0xcd76:'session_state_cd76',0xcd7a:'session_state_cd7a',0xcd80:'session_blocks_accepted',0xcd8a:'session_error_count',0xcd94:'session_context',0xcdcc:'session_streaming_mode',0xce06:'session_started_low',0xce08:'session_started_high',0x2e44:'session_integrity_labels'}
services={0x9c7c:'session_long_remainder',0x3717:'session_path_test',0x3ea4:'session_display_path',0x841a:'session_file_open',0x86ac:'session_file_write',0xabfa:'session_serial_gate_set',0x8318:'session_file_close_boundary',0x3f4b:'session_local_cancel',0x4861:'session_carrier_present',0x6b98:'session_delay_ticks',0x6bf0:'session_ui_print',0x77fe:'session_clock',0xe498:'session_status',0xab0b:'session_transmit_byte',0xaad9:'session_timed_byte',0xd077:'session_protocol12_boundary',0xd06b:'session_protocol9_boundary',0x40b9:'session_send_nak',0xf050:'session_control_status'}
exits={0xda3a:'session_batch_metadata_boundary',0xdaea:'session_accept_data',0xddf6:'session_commit_buffer',0xde02:'session_commit_partial',0xde20:'session_commit_unknown_size',0xd731:'session_failure_cleanup_argument',0xd734:'session_failure_return',0xd87c:'session_context_enter',0xd8ae:'session_file_cleanup',0xdc1f:'session_retry_enter',0xdc6a:'session_header_checkpoint',0xdcf1:'session_retry_limit'}
alladdresses=set();decoded=[]
with tempfile.TemporaryDirectory() as directory:
 work=Path(directory)
 def assemble(text,address):
  (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {address}\n%include "encodings.inc"\n{text}\n')
  p=subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
  return (work/'one.bin').read_bytes() if p.returncode==0 else None
 for name,start,end,tail in units:
  offset=0x1200+start if start in (0x9048,0x9065) else overlay['source_file_offset']+start-overlay['relative_load_segment']*16
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
 names={address:f'session_at_{address:04x}' for address in alladdresses}
 names.update(services);names.update(exits)
 names.update({0xda31:'session_validated',0xda9e:'session_success_return',0xdcfd:'session_commit_enter',0xd6a4:'session_receive',0xd656:'session_initialize',0xefb0:'session_totals_initialize',0xd752:'session_handshake_enter',0xf070:'session_wait',0xf0d4:'session_timestamp',0x9048:'session_setjmp',0x9065:'session_longjmp'})
 # Entry services correspond to exact instruction labels, not duplicate callback bodies.
 layout={**state,**services,**exits,**{a:n for a,n in names.items() if a in alladdresses}}
 for name,start,end,tail,offset,blob,rows in decoded:
  own={a for a,_ in rows};needed={};lines=[]
  for address,text in rows:
   m=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
   if m:
    target=int(m[3],16);symbol=names[target];
    if target not in own:needed[symbol]=target
    text=m[1]+' '+((m[2]+' ') if m[2] else '')+symbol
   for original,symbol in ([] if m else state.items()):
    if original in ():continue
    if re.search(rf'0x{original:x}\b',text) or (original>=0x8000 and f'-0x{0x10000-original:x}]' in text):needed[symbol]=original
    text=re.sub(rf'0x{original:x}\b',symbol,text)
    if original>=0x8000:text=text.replace(f'-0x{0x10000-original:x}]',f'+{symbol}]')
   lines.append(names[address]+': '+text)
  header=['; Exact native transfer session instructions; analyst regeneration is explicit.', 'BITS 16','CPU 8086','%ifdef TRANSFER_SESSION_OMF','SEGMENT _TEXT public class=CODE use16','%define short']
  header+=['global '+names[a] for a in sorted(own)]+['extern '+symbol for symbol in sorted(needed)]
  if tail:header+=['extern '+tail] if tail not in needed else []
  header+=['%else',f'ORG 0x{start:x}']+['%%define %s 0x%x'%(symbol,needed[symbol]) for symbol in sorted(needed)]+['%endif','%include "encodings.inc"']
  footer=['%ifdef TRANSFER_SESSION_OMF','jmp '+tail,'%endif'] if tail else []
  if name=='context':footer=['%ifdef TRANSFER_SESSION_OMF','%ifdef TRANSFER_SESSION_DIAGNOSTIC','extern session_file_cleanup_checkpoint','jmp session_file_cleanup_checkpoint','%else','jmp '+tail,'%endif','%endif']
  (OUT/(name+'.asm')).write_text('\n'.join(header+lines+footer)+'\n')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(OUT/(name+'.asm')),'-o',str(work/'flat')],check=True)
  assert (work/'flat').read_bytes()==blob,name
 proof={'source_sha256':SHA,'overlay':21,'units':[{'source':n+'.asm','start':hex(s),'end_exclusive':hex(e),'bytes':e-s,'source_file_offset':o,'sha256':hashlib.sha256(b).hexdigest()} for n,s,e,t,o,b,r in decoded],'state':{hex(a):n for a,n in state.items()},'boundaries':{hex(a):n for a,n in {**services,**exits}.items()}}
 proof['supporting_evidence']=[]
 for address,name in [('1d656','session-initialization'),('1d6a4','receive-controller'),('1efb0','session-byte-totals'),('1f070','handshake-wait'),('1f0d4','timestamp'),('1d0d0','application-owner')]:
  path=ROOT/'analysis/pcplus-overlay-anchored-21/functions'/(f'0x{address}-asm.json')
  evidence=json.loads(json.loads(path.read_text())['content'][0]['text'])['evidence_id']
  proof['supporting_evidence'].append({'name':name,'export':str(path.relative_to(ROOT)),'evidence_id':evidence})
 proof['setjmp_evidence']='ev_5e9883fbf1946afde585338918ee467ff5dc65e55e792ba44922b0db819f2d4e'
 proof['limitations']=['Exact native session fragments; OMF-only fallthrough jumps expose diagnostic checkpoints.','Original9048/9065 are real nonlocal setjmp/longjmp, not event posting. Context10bytes(BP,DI,SI,SP,returnIP) requires DS=SS and same live code segment.','Diagnostic models UART timing, carrier, keyboard and UI explicitly; no live transfer/application owner or file IO is claimed.','Protocol9/12 specialized controllers, file cleanup and application UI lifecycle remain explicit boundaries.']
 (OUT/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',sum(e-s for n,s,e,t,o,b,r in decoded),'exact bytes')
