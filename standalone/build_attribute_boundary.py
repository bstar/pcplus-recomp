#!/usr/bin/env python3
"""Build recovered boundary/coordinate instructions from source only."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/attribute-boundary';OUT.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/attribute_boundary/provenance.json').read_text());sources={}
for u in proof['units']:
 source=ROOT/u['file'];sources[u['file']]=hashlib.sha256(source.read_bytes()).hexdigest()
 for fmt,suffix,extra in [('bin','bin',[]),('obj','obj',['-DATTRIBUTE_BOUNDARY_OMF'])]:
  dest=OUT/(source.stem+'.'+suffix)
  subprocess.run(['nasm','-f',fmt,*extra,'-I',str(ROOT/'reconstruction/uart')+'/',str(source.relative_to(ROOT)),'-o',str(dest)],cwd=ROOT,check=True)
  if fmt=='bin':assert hashlib.sha256(dest.read_bytes()).hexdigest()==u['sha256']
manifest=dict(passed=True,bytes=sum(u['bytes'] for u in proof['units']),sources=sources,units=proof['units'],original_inputs=[],scope='Flat exact recovered routines and OMF objects; ordinary build never reads an original or REA database.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Attribute boundary',manifest['bytes'],'exact bytes PASS')
