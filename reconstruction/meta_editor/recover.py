#!/usr/bin/env python3
"""Explicit original-byte recovery; normal component builds use public ASM only."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PARTS=[('defaults',0xe24a,0xe261),('field_key',0xe261,0xe294),('row',0xe294,0xe3a5)]
DATA={0x1f7c:'meta_editor_attribute',0x2068:'meta_editor_wait_default',
 0x2290:'meta_editor_kind_labels',0x3756:'meta_editor_records',
 0x3758:'meta_editor_text',0x3972:'meta_editor_records_end',
 0x5df4:'meta_editor_field_previous',0x5df8:'meta_editor_field_next',
 0x5e00:'meta_editor_edit_previous',0x5e04:'meta_editor_edit_next',
 0x6644:'meta_editor_kind_format',0x7a50:'meta_editor_wait_active'}
CALLS={0x4a04:'meta_editor_inverse',0x6e66:'meta_editor_cursor',
 0x7878:'meta_editor_read_key',0x7880:'meta_editor_edit_text',0x75e8:'meta_editor_draw_kind'}
ASM_IDS=['ev_759edfe9e57c43926b819d4c40d8094b66cede44556408d4b01e2c039ff69468',
 'ev_4d2fb7babb06d907ee451f5172b5786156748aefeac0e8996b678a9f7f173b40',
 'ev_9715e3d77e9540c7766bdcd522bb72e2dae440aa96513c0c0a338c292866cdc3']


def main():
 raw=(ROOT/'analysis/pcplus-install/PCPLUS.EXE').read_bytes();digest=hashlib.sha256(raw).hexdigest()
 assert digest=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 manifest=json.loads((ROOT/'analysis/pcplus-overlay-entry-images/manifest.json').read_text())
 image=next(x for x in manifest['images'] if x['overlay']==3)
 assert image['sha256']=='fff9700d3b5e76b8f0d76c3a9df7051bfa39f87c0891bd593a8f84f19c758b19'
 region=next(x for x in image['source_ranges'] if x['role']=='overlay-3');proof=[]
 with tempfile.TemporaryDirectory() as temporary:
  work=Path(temporary)
  def assemble(text,at):
   (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n'+text+'\n')
   p=subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
   return (work/'one.bin').read_bytes() if p.returncode==0 else None
  for (name,start,end),evidence_id in zip(PARTS,ASM_IDS):
   offset=region['source_file_offset']+start-region['relative_address'];blob=raw[offset:offset+end-start]
   (work/'code.bin').write_bytes(blob)
   decoded=subprocess.check_output(['ndisasm','-b16',f'-o{start}',str(work/'code.bin')],text=True);rows=[]
   for line in decoded.splitlines():
    match=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line);assert match,line
    at,encoded,text=int(match[1],16),bytes.fromhex(match[2]),match[3];assert not text.startswith('db ')
    instruction=text
    if encoded[0]==0xeb:instruction=instruction.replace('jmp ','jmp short ',1)
    elif encoded[0]==0xe9:instruction=instruction.replace('jmp ','jmp near ',1)
    elif 0x70<=encoded[0]<=0x7f:instruction=instruction.replace(' ',' short ',1)
    if assemble(instruction,at)!=encoded:
     candidates=[]
     if len(encoded)==2 and encoded[1]>=0xc0 and encoded[0] in (2,3,10,11,18,19,26,27,34,35,42,43,50,51,58,59,138,139):
      op,args=text.split(' ',1);candidates.append(op+'_load '+args)
     for width in ('word','byte'):candidates.append(re.sub(r',(-?0x[0-9a-f]+)$',rf',strict {width} \1',instruction))
     instruction=next((c for c in candidates if assemble(c,at)==encoded),None);assert instruction is not None,(at,text)
    rows.append((at,instruction))
   used_data={k:v for k,v in DATA.items() if any(re.search(r'(?<![0-9a-f])'+hex(k)+r'(?![0-9a-f])',t) for _,t in rows)}
   used_calls={k:v for k,v in CALLS.items() if any(re.fullmatch('call '+hex(k),t) for _,t in rows)}
   lines=['; Recovered 2.01 Meta Keys component; external UI boundaries remain explicit.','BITS 16','CPU 8086',
    '%ifdef META_EDITOR_OMF','GROUP DGROUP _DATA','SEGMENT _TEXT public class=CODE use16','global meta_editor_'+name]
   for symbol in sorted(set(used_data.values())):
    if symbol=='meta_editor_text':lines+=['%define meta_editor_text (meta_editor_records+2)']
    elif symbol=='meta_editor_records_end':lines+=['%define meta_editor_records_end (meta_editor_records+540)']
    else:lines+=['extern '+symbol+':wrt DGROUP']
   lines+=['extern '+symbol for symbol in used_calls.values()]
   if name=='row':lines+=['extern meta_editor_field_key']
   lines+=['%else',f'ORG {start}']+['%define '+v+' '+hex(k) for k,v in (used_data|used_calls).items()]
   if name=='row':lines+=['%define meta_editor_field_key 0xe261']
   lines+=['%endif','%include "encodings.inc"','meta_editor_'+name+':']
   for at,text in rows:
    for k,symbol in used_data.items():text=re.sub(r'(?<![0-9a-f])'+hex(k)+r'(?![0-9a-f])',symbol,text)
    if name=='row':text=text.replace('mov ax,0xe261','mov ax,meta_editor_field_key')
    branch=re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
    if branch:
     target=int(branch[3],16);symbol=f'L_{target:04x}' if start<=target<end else CALLS[target]
     text=branch[1]+' '+(branch[2]+' ' if branch[2] else '')+symbol
    lines.append(f'L_{at:04x}: '+text)
   lines+=['%ifdef META_EDITOR_OMF','SEGMENT _DATA public class=DATA use16','%endif']
   source=ROOT/'reconstruction/meta_editor'/(name+'.asm');source.write_text('\n'.join(lines)+'\n')
   subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(work/'whole.bin')],check=True)
   assert (work/'whole.bin').read_bytes()==blob
   proof.append(dict(name=name,start=start,end_exclusive=end,source_file_offset=offset,bytes=len(blob),instructions=len(rows),sha256=hashlib.sha256(blob).hexdigest(),REA_assembly=evidence_id,data={hex(k):v for k,v in used_data.items()},services={hex(k):v for k,v in used_calls.items()}))
 report=dict(original_sha256=digest,overlay=3,analysis_image_sha256=image['sha256'],ranges=proof,
  REA_dispatch='ev_a1a870d1d2c2754325165f8155f2645805d413818b24f53fbf8bf375476f9bbf',
  limitations=['Static synthetic overlay analysis input was never executed; recovered bytes independently match original file ranges.',
   'Row index must be0..9. Original row editor does not validate it or corrupt kind-label indices.',
   'Shared text editor, cursor/keyboard/rendering/file/window services are explicit external boundaries. No whole Alt-M UI, save, service scheduling or terminal integration claim.'])
 (ROOT/'reconstruction/meta_editor/provenance.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Recovered Meta Keys:',sum(x['bytes'] for x in proof),'exact bytes,3 routines')


if __name__=='__main__':main()
