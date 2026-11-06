#!/usr/bin/env python3
"""Bind a public viewer candidate package to cold builds, launchers and Enigma IO."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['package','source-proof','archive','splash','setup','script','upload','download','cancel','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 def read(path):
  r=json.loads(path.read_text());assert r['passed'],path
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values()),path
  for field in ['sources','captures']:
   for n,h in r.get(field,{}).items():assert sha(ROOT/n)==h,n
  return r
 m=json.loads((a.package/'manifest.json').read_text());digest=m['files']['TERMINAL.EXE']
 assert m['dos_directory']=='PCPLUS' and len(m['files'])==10 and m['experimental_file_viewer'] and m['experimental_external_viewer'] and not m['card_written'] and m['original_inputs']==[]
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 for n,h in m['files'].items():assert sha(a.package/'PCPLUS'/n)==h,n
 proof=read(a.source_proof);assert proof['source_commit']==m['source_base_commit'] and proof['files']==m['files'] and proof['ancestor_git_unavailable'] and proof['original_inputs']==[]
 assert proof['package_manifest_sha256']==sha(a.package/'manifest.json') and len(proof['rebuilt_executables'])==5
 archive=read(a.archive);assert archive['files']==m['files'] and archive['package_manifest_sha256']==sha(a.package/'manifest.json')
 assert sha(a.archive.parent/archive['archive'])==archive['archive_sha256'] and not archive['card_written'] and not archive['selector_changed']
 launchers=[]
 for name,path in [('splash',a.splash),('setup',a.setup),('script',a.script)]:
  r=read(path);assert r['package_manifest_sha256']==sha(a.package/'manifest.json') and r['package_files']==m['files']
  assert (r['cpu'],r['port'],r['irq'])==('8086',3,5) and 'private PRM/DIR/XLT unchanged' in r['checks']
  for n,h in r['artifacts'].items():assert sha(path.parent/n)==h,n
  if name=='script':assert r['precompiled_before_terminal'] and r['bios_port_omitted'] and 'script writes expected result' in r['checks']
  else:assert 'actual magenta splash captured by independent timer' in r['checks']
  launchers.append(dict(case=name,report=bind(path),checks=r['checks']))
 upload=read(a.upload);download=read(a.download);cancel=read(a.cancel)
 for r in [upload,download,cancel]:assert r['terminal_sha256']==digest and r['payload_bytes']==65539
 assert upload['payload_sha256']==download['payload_sha256']==cancel['payload_sha256']
 for r,mode in [(upload,'upload'),(download,'download')]:assert r['mode']==mode and r['all256_values'] and r['payload_size_lookalikes']>0 and r['exact_destination'] and r['NAWS']==[[80,24]]
 assert cancel['same_DOS_process'] and cancel['authenticated_sessions']==cancel['proxy_connections']==1 and cancel['exact_retry'] and cancel['partial_disk_bytes']>0
 result=dict(passed=True,binary_sha256=digest,package=dict(manifest=bind(a.package/'manifest.json'),source_commit=m['source_base_commit'],files=m['files']),public_source_build=bind(a.source_proof),archive=dict(report=bind(a.archive),file=bind(a.archive.parent/archive['archive'])),launchers=launchers,
  stock_enigma=dict(upload=bind(a.upload),download=bind(a.download),cancel_retry=bind(a.cancel),payload_bytes=65539,payload_sha256=upload['payload_sha256'],partial_cancel_bytes=cancel['partial_disk_bytes']),
  card_written=False,selector_changed=False,sources={n:sha(ROOT/n) for n in ['standalone/record_viewer_release.py','standalone/build_path_session.py']},original_inputs=[],
  limits=['This is a local connection-test candidate, not a published release or physical installation.','Real stock Enigma/sexyz and isolated SynthModem Telnet proxy are exercised through synthetic Hayes serial transport; SIP/audio/DSP/analog/Boca CTS acceptance remains open.','The accepted isolated bridge snapshot includes the menu-owned WindowSizeReply patch, which is absent from the workstation SynthModem checkout. These runs do not prove runtime equivalence to that checkout or deploy the patch.','Three launcher cases use dummy8086 COM3/IRQ5 UART fixtures; stock transfers use25 physical rows and24 logical rows.','The cancellation run receives the exact same large payload on retry in one DOS process and connection; it does not establish physical carrier-loss behavior.','Complete original PCPlus, compiler/ASPECT/emulation/protocol/Host parity remains open.'])
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS five cold-built executables,ten archive files,three DOS launchers and exact stock Enigma upload/download/cancel-retry')
if __name__=='__main__':main()
