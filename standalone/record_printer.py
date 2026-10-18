#!/usr/bin/env python3
"""Bind native printer CPU/DOS evidence to exact source and executable identities."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def record_live(labels):
 from test_terminal_printer_dos import recipes
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==runtime
 for name,want in manifest['sources'].items():assert sha(name)==want,name
 device=read('build/printer-device/result.json');assert device['passed']
 for name,want in device['sources'].items():assert sha(name)==want,name
 for name,want in device['binaries'].items():assert sha('build/printer-device/'+name)==want,name
 linked=read('build/terminal/terminal-printer-live-checks.json');assert linked['passed'] and linked['binary_sha256']==runtime
 latest={};history=[]
 for label in labels:
  assert label and all(c.isalnum() or c in '-_' for c in label)
  batch=read('build/terminal-printer-dos/'+label+'/checks.json')
  for case in batch['cases']:
   folder=ROOT/'build/terminal-printer-dos'/label/case['case']
   assert case==json.loads((folder/'result.json').read_text())
   record=dict(case,label=label,retained_artifacts={str(q.relative_to(ROOT)):sha(q.relative_to(ROOT)) for q in sorted(folder.iterdir()) if q.is_file()})
   history.append(record);latest[case['case']]=dict(label=label,passed=case['passed'],binary_sha256=case['binary_sha256'])
 assert set(latest)=={r['name'] for r in recipes()}
 assert all(r['passed'] and r['binary_sha256']==runtime for r in latest.values())
 # The device probe has its own source-built COM identity, not the terminal hash.
 # Its positive/negative kernel observations complement the linked application.
 probe_path='build/terminal-printer-dos/parallel-key-probe-3'
 probes=read(probe_path+'/probe.json');assert len(probes)==2 and all(r['passed'] for r in probes)
 assert (ROOT/probe_path/'key/KEY.BIN').read_bytes()==b'\x00\x26'
 assert (ROOT/probe_path/'file/PRINTER.RAW').read_bytes()==bytes(range(256))
 assert not (ROOT/probe_path/'disabled/PRINTER.RAW').exists()
 for mode in ('file','disabled'):assert read(probe_path+'/'+mode+'/result.json')==next(r for r in probes if r['mode']==mode)
 artifacts={str(q.relative_to(ROOT)):sha(q.relative_to(ROOT)) for q in sorted((ROOT/probe_path).rglob('*')) if q.is_file()}
 source_hashes={p:sha(p) for p in ['standalone/test_terminal_printer_dos.py','standalone/check_terminal_printer_live.py','standalone/record_printer.py']}
 report=dict(passed=True,binary_sha256=runtime,linked_checks=linked,device_backend_checks=device,device_probe=probes,device_probe_artifacts=artifacts,runs=history,latest_selected_cases=latest,latest_selected_cases_passed=True,all_recorded_cases_passed=all(r['passed'] for r in history),evidence_source_sha256=source_hashes,scope='Nine actualDOS live AltL PRN tests use file-only DOSBox-X parallel output, actual BIOS/UART/PRN calls, independent processed-byte oracle, capture/monitor coexistence and hardware restoration. The backend diagnostic uses explicit fault-driver boundaries; the separate source-built device probe delivers all256 bytes and verifies AltL2600. No physical printer, hostile-driver call-time bounds, processed SUB control1248, live disk/device faults or complete UI parity claim.')
 (ROOT/'docs/validation/terminal-printer-live.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Recorded live printer',runtime,len(latest),'selected actualDOS cases')
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dos-label',action='append',default=[]);args=parser.parse_args()
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
 if args.dos_label:record_live(args.dos_label)
if __name__=='__main__':main()
