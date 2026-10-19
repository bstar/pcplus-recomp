#!/usr/bin/env python3
"""Build exact attribute repair and its real coordinate/video dependencies."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/attribute-repair';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((ROOT/'reconstruction/attribute_repair/provenance.json').read_text())
units=list(proof['units']);sources={};outputs={}
for module,names in [('attribute_boundary',['position']),('erase',['default_attribute','previous_attribute']),('text',['char'])]:
 data=json.loads((ROOT/f'reconstruction/{module}/provenance.json').read_text())
 units.extend(u for u in data['units'] if Path(u['file']).stem in names)
for u in units:
 source=ROOT/u['file'];sources[u['file']]=sha(source)
 module=source.parent.name
 for fmt,extra in [('bin',[]),('obj',['-D'+module.upper()+'_OMF'])]:
  dest=OUT/(module+'-'+source.stem+'.'+fmt)
  subprocess.run(['nasm','-f',fmt,*extra,'-I',str(ROOT/'reconstruction/uart')+'/',str(source.relative_to(ROOT)),'-o',str(dest)],cwd=ROOT,check=True)
  if fmt=='bin':assert sha(dest)==u['sha256'] and dest.stat().st_size==u['bytes'],source
  outputs[str(dest.relative_to(ROOT))]=sha(dest)
manifest=dict(passed=True,bytes=sum(u['bytes'] for u in proof['units']),sources=sources,units=units,outputs=outputs,original_inputs=[],scope='Exact flat repair, advance, write and four real coordinate/erase/video dependencies; relocatable OMF objects. No original executable or analysis input.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Attribute repair',manifest['bytes'],'exact bytes PASS')
