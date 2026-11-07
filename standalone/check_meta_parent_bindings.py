#!/usr/bin/env python3
"""Check Meta callback ABI against exact source-built parent and diagnostic MZs."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(binary,listing):
 raw=binary.read_bytes();h=struct.unpack_from('<14H',raw);assert raw[:2]==b'MZ'
 text=listing.read_text()
 symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]+):([0-9a-f]+)\*?\s+(\w+)\s*$',text,re.M|re.I)}
 sections={n:(int(s,16),int(o,16),int(size,16))for n,s,o,size in re.findall(r'^(\w+)\s+\w+\s+\w+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',text,re.M|re.I)}
 return raw[h[4]*16:],symbols,sections

def callbacks(image,symbols,services):
 def body(name,target,words):
  s,o=symbols[name];ts,to=symbols[target];assert s==ts
  prefix=b'' if not words else bytes.fromhex('55 89 e5')+b''.join(bytes((0xff,0x76,8+2*i))for i in reversed(range(words)))
  suffix=b'\xcb' if not words else bytes.fromhex('8d 66 00 5d cb')
  return prefix+b'\xe8'+struct.pack('<H',(to-o-len(prefix)-3)&0xffff)+suffix
 def verify(data):
  for name,target,words in services:
   s,o=symbols[name];at=s*16+o;expected=body(name,target,words);assert data[at:at+len(expected)]==expected,name
 verify(image);rejected=[]
 for name,target,words in services:
  s,o=symbols[name];at=s*16+o;expected=body(name,target,words)
  for kind,index in (('wrong-return',len(expected)-1),('wrong-target',len(expected)-(1 if not words else 5)-2)):
   bad=bytearray(image);bad[at+index]^=1
   try:verify(bad)
   except AssertionError:rejected.append(name+':'+kind)
   else:raise AssertionError(('invalid callback admitted',name,kind))
 return dict(callbacks={name:dict(target=target,cdecl_words=words,segment=symbols[name][0],offset=symbols[name][1],bytes=len(body(name,target,words)))for name,target,words in services},invalid_variants_rejected=rejected)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('parent','diagnostic','linked-parent','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--parent-source-revision',required=True,help='Public historical source revision for deployed-parent provenance.')
 a=p.parse_args();parent=a.parent.resolve();diagnostic=a.diagnostic.resolve();out=a.output.resolve()
 assert all(d.is_relative_to(ROOT/'build') for d in (parent,diagnostic,out)) and not out.exists();out.mkdir()
 manifest=json.loads((parent/'manifest.json').read_text());assert sha(parent/'TERMINAL.EXE')==manifest['binary_sha256']
 revision=subprocess.run(['git','rev-parse',a.parent_source_revision],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip();historical=[]
 for n,h in manifest['sources'].items():
  path=Path(n);assert not path.is_absolute() and '..' not in path.parts
  if sha(ROOT/n)!=h:
   old=subprocess.run(['git','show',revision+':'+n],cwd=ROOT,capture_output=True,check=True).stdout
   assert hashlib.sha256(old).hexdigest()==h,n;historical.append(n)
 image,symbols,sections=read(parent/'TERMINAL.EXE',parent/'terminal.map')
 old=[('config_'+n+'_service__resident',n+'_',0)for n in ('memcpy','memset','memcmp','strchr','strcmp','strlen')]+[('config_canonical_service__resident','capture_fs_canonical_',0)]
 existing=callbacks(image,symbols,old)
 config=sections['CONFIG_CODE'];assert config[1]==0
 for name in ('_resource_pcplus_path','_capture_file_reserve','_capture_file_release'):assert symbols[name][0]==config[0],name
 # The selected parent omits optional directory callbacks. Explicit Meta
 # adapters bind its existing near helpers; do not assume those flags are on.
 for name in ('_directory_replace_paths','_key_actions_dos_read','capture_fs_attributes_'):assert symbols[name][0]==sections['_TEXT'][0]
 dm=json.loads((diagnostic/'result.json').read_text());assert dm['passed'] and dm['parent_services'] and sha(diagnostic/'METAEDIT.EXE')==dm['binary_sha256']
 di,ds,dsections=read(diagnostic/'METAEDIT.EXE',diagnostic/'METAEDIT.map')
 new=callbacks(di,ds,[('_meta_bank_paths_resident','_directory_replace_paths',3),('_meta_bank_actions_resident','_key_actions_dos_read',3),('meta_bank_attributes_service__resident','capture_fs_attributes_',0),('_meta_bank_resource_resident','_resource_pcplus_path',3)])
 for name in ('_meta_bank_resource_resident','_resource_pcplus_path'):assert ds[name][0]==dsections['CONFIG_CODE'][0]
 assert dm['new_parent_service_segments']=={'meta_bank_resident':{'_TEXT':44},'meta_bank_resource':{'CONFIG_CODE':20}}
 assert 65536-sections['_TEXT'][2]>=44 and 65536-config[2]>=35
 start=symbols['redisplay_snapshot'];end=symbols['redisplay_snapshot_end'];arena=(end[0]-start[0])*16+end[1]-start[1];assert arena==63000
 linked=a.linked_parent.resolve();assert linked.is_relative_to(ROOT/'build');lm=json.loads((linked/'manifest.json').read_text());assert lm['experimental_meta_services'] and sha(linked/'TERMINAL.EXE')==lm['binary_sha256']
 li,ls,lsections=read(linked/'TERMINAL.EXE',linked/'terminal.map');linked_new=callbacks(li,ls,[('_meta_bank_paths_resident','_directory_replace_paths',3),('_meta_bank_actions_resident','_key_actions_dos_read',3),('meta_bank_attributes_service__resident','capture_fs_attributes_',0),('_meta_bank_resource_resident','_resource_pcplus_path',3)])
 assert lsections['_TEXT'][2]-sections['_TEXT'][2]==44 and lm['data_stack_bytes']==manifest['data_stack_bytes']
 assert lsections['CONFIG_CODE'][2]-config[2]>=20 and lsections['CONFIG_CODE'][2]-config[2]<=35
 result=dict(passed=True,linked_parent_sha256=lm['binary_sha256'],linked_parent_new_services=linked_new,linked_parent_TEXT_spare_bytes=65536-lsections['_TEXT'][2],linked_parent_CONFIG_spare_bytes=65536-lsections['CONFIG_CODE'][2],parent_sha256=sha(parent/'TERMINAL.EXE'),parent_map_sha256=sha(parent/'terminal.map'),parent_manifest_sha256=sha(parent/'manifest.json'),diagnostic_sha256=sha(diagnostic/'METAEDIT.EXE'),parent_sources_verified=len(manifest['sources']),historical_source_revision=revision,historical_sources=historical,existing_services=existing,new_services=new,new_resident_TEXT_bytes=44,new_CONFIG_bytes=20,resident_TEXT_spare_bytes=65536-sections['_TEXT'][2],CONFIG_spare_bytes=65536-config[2],DGROUP_spare_bytes=65536-manifest['data_stack_bytes'],snapshot_arena_bytes=arena,original_inputs=[],sources={n:sha(ROOT/n)for n in ('standalone/check_meta_parent_bindings.py','src/key_mapping/meta_bank_runtime.asm','src/key_mapping/meta_bank_resource.asm','src/key_mapping/meta_bank_resident.asm')},scope=__doc__+' Seven existing callbacks and four new adapters have exact near-call/RETF instruction checks. CONFIG resolver/lease placement and pre-integration capacity checked. Historical deployed source is verified by digest, not asserted equal to current code. No changed/corrupted parent executed; loader/arena lifetime/linked-parent/UART/physical acceptance remain open.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS seven existing callbacks/four new adapters;22 invalid variants reject;TEXT/CONFIG/DGROUP spare:',result['resident_TEXT_spare_bytes'],result['CONFIG_spare_bytes'],result['DGROUP_spare_bytes'])
if __name__=='__main__':main()
