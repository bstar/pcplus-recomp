#!/usr/bin/env python3
"""Experimental GET/Help standard overlays; no package/physical promotion."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
from build_path_session import ROOT,sha


def mz_overlay(data):
 assert len(data)>=32
 h=struct.unpack_from('<14H',data);assert h[0]==0x5a4d and h[13]==0 and h[2] and h[1]<512
 declared=h[2]*512-(512-h[1] if h[1] else 0);header=h[4]*16
 assert 32<=header<declared<len(data) and h[12]>=28 and h[12]+h[3]*4<=header
 import hashlib
 digest=lambda b:hashlib.sha256(b).hexdigest()
 return dict(header_bytes=header,root_declared_bytes=declared,root_image_bytes=declared-header,
  root_image_sha256=digest(data[header:declared]),overlay_trailer_bytes=len(data)-declared,
  overlay_trailer_sha256=digest(data[declared:]),
  exact_minimum_including_PSP=((declared-header+15)//16+h[5]+16)*16,
  page_minimum_including_PSP=(h[2]*32-h[4]+h[5]+16)*16,
  limitation='Root MZ bounds and separate complete trailer identity, not a general parser of arbitrary overlay records. No header padding inserted.')


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 base=a.base.resolve();out=a.output.resolve()
 assert base.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads((base/'manifest.json').read_text());assert m['experimental_overlay_layout_ready']
 assert sha(base/'ASPECT.EXE')==m['binary_sha256'] and m['original_inputs']==[]
 for name,h in m['sources'].items():assert sha(ROOT/name)==h,name
 out.mkdir();groups=[[],[],[]];objects={}
 help_names={'input-view.obj','input-notice_content.obj','input-format.obj','input-document.obj','input-resource.obj',
             'help-cursor.obj','help-resource-io.obj','help_overlay_bridge_overlay.obj'}
 get_names={'get_runtime-c-bank.obj','get_context-c-bank.obj','get_command-c-bank.obj','get_native_field-c-bank.obj',
  'get_vm_bindings-c-bank.obj','get-field-bank.obj','get_native-bank.obj','get_checkpoint-bank.obj','get_command-bank.obj',
  'get_native_field-bank.obj','get_vm_bindings-bank.obj','get_bank_overlay-bank.obj'}
 seen=set()
 for line in (base/'GETVM.lnk').read_text().splitlines():
  if not line.startswith('file '):continue
  original=Path(line[5:])
  if not original.is_absolute():
   original=base/original
   if not original.exists():original=original.with_suffix('.o')
  assert original.is_file(),original
  name='obj'+str(len(objects)).zfill(4)+'.obj';shutil.copyfile(original,out/name)
  objects[name]=dict(original=str(original.relative_to(ROOT)),sha256=sha(out/name))
  group=1 if original.name in get_names else 2 if original.name in help_names else 0
  seen.add(original.name);groups[group].append('file '+name)
 assert get_names<=seen and help_names<=seen
 link=['system dos','option quiet','option stack=8192','option standard','option packcode=0',
       # Use DOSSEG rather than a manual ORDER. Its overlay-aware ordering
       # keeps manager tables in its CS and sorts the preloaded data section
       # too: far state before DGROUP, _NULL first, BSS then stack last.
       'name ASPECT.EXE','option map=ASPECT.map',*groups[0],'begin','section',*groups[1],'section',*groups[2],'end']
 (out/'OVERLAY.lnk').write_text('\n'.join(link)+'\n')
 subprocess.run(['wlink','@OVERLAY.lnk'],cwd=out,check=True)
 layout=mz_overlay((out/'ASPECT.EXE').read_bytes());text=(out/'ASPECT.map').read_text()
 symbols={n:(int(s,16)*16+int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',text,re.M|re.I)}
 segments={n:dict(segment=int(s,16),offset=int(o,16),size=int(z,16)) for n,cls,s,o,z in re.findall(
  r'^(\w+)\s+(\w+)\s+\w+\s+([0-9a-f]{4}):([0-9a-f]{4,8})\s+([0-9a-f]{8})\s*$',text,re.M|re.I) if cls!='_OVLCODE'}
 group=re.search(r'DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',text,re.I)
 ds=int(group[1],16)*16+int(group[2],16);size=int(group[3],16)
 assert size<=65536 and ds<=symbols['get_resident_checkpoint_state']<ds+size
 assert segments['STACK']['size']==8192 and segments['_TEXT']['size']<=65536
 assert all(symbols[n]<layout['root_image_bytes'] for n in ('__OVLTAB__','__OVLSTARTVEC__','__LOVLLDR__'))
 assert symbols['__OVLENDVEC__']<=layout['root_image_bytes']
 addresses={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',text,re.M|re.I)}
 assert all(addresses[n][0]==addresses['__LOVLLDR__'][0] for n in ('__OVLTAB__','__OVLSTARTVEC__','__OVLENDVEC__'))
 assert segments['GET_RUNTIME_STORAGE']['size']==206
 linear=lambda name:segments[name]['segment']*16+segments[name]['offset']
 assert linear('GET_RUNTIME_STORAGE')+206<=linear('_NULL')==ds
 assert linear('_NULL')<linear('CONST')<linear('_BSS')<linear('STACK')
 assert linear('STACK')+8192==ds+size
 for name in ('LOCHELP.HLP','help-resource.json'):
  if (base/name).exists():shutil.copyfile(base/name,out/name)
 m.pop('MZ_header_layout',None)
 m.update(binary_sha256=sha(out/'ASPECT.EXE'),experimental_standard_overlays=True,package_eligible=False,
  base_manifest_sha256=sha(base/'manifest.json'),base_binary_sha256=sha(base/'ASPECT.EXE'),overlay_objects=objects,
  MZ_overlay_layout=layout,
  GET_bank_layout=dict(passed=True,near_code_bytes=segments['_TEXT']['size'],near_code_spare=65536-segments['_TEXT']['size'],
   GET_code_bytes=segments['GET_VM_CODE']['size'],editor_code_bytes=segments['GET_FIELD_CODE']['size'],
   Help_code_bytes=segments['HELP_OVL_CODE']['size'],field_state_bytes=206,DGROUP_bytes=size,stack_bytes=8192,
   minimum_DOS_bytes_including_PSP=layout['exact_minimum_including_PSP'],
   page_rounded_minimum_including_PSP=layout['page_minimum_including_PSP'],
   scope='Preliminary trusted-linker map/MZ bounds only; full callback, checkpoint, recovery and allocation acceptance requires DOS execution.'),
  scope='Experimental standard overlays for GET and Help, with resident ISR/mouse code and SS-relative GET checkpoint state. Not packaged or physically verified.')
 m['sources']['standalone/build_aspect_standard_overlay.py']=sha(Path(__file__))
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(binary=m['binary_sha256'],layout=m['GET_bank_layout']),indent=2))


if __name__=='__main__':main()
