#!/usr/bin/env python3
"""Bind native printer CPU/DOS evidence to exact source and executable identities."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 manifest=read('build/printer/manifest.json')
 cpu=read('build/printer/checks.json');dos=read('build/printer-dos/result.json')
 digest=sha('build/printer/PRINTER.EXE')
 assert manifest['binary_sha256']==cpu['binary_sha256']==dos['binary_sha256']==digest
 assert cpu['passed'] and dos['passed']
 for name,want in manifest['sources'].items():assert sha(name)==want,name
 proof=read('reconstruction/printer/provenance.json')
 for u in proof['units']:
  name='build/printer/'+Path(u['source']).stem+'.bin'
  assert sha(name)==u['sha256'] and (ROOT/name).stat().st_size==u['bytes']
 source_hashes={p:sha(p) for p in ['standalone/build_printer.py','standalone/check_printer.py','standalone/printer_host.asm','standalone/test_printer_dos.py','standalone/record_printer.py']}
 result={'passed':True,'manifest':manifest,'native_provenance':proof,'CPU_checks':cpu,'DOS_checks':dos,'evidence_source_sha256':source_hashes,'scope':'Source-built native printer toggle and per-character wrappers, composed with the previously recovered logger. CRT/device operations are explicit memory fixtures. This establishes native instruction behavior and ABI on synthetic data, not live Alt-L integration, DOS printer drivers, physical printer availability or safe failure handling in the maintained application.'}
 (ROOT/'docs/validation/printer-native.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded printer native CPU/DOS evidence',digest)
if __name__=='__main__':main()
