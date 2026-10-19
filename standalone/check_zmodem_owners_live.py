#!/usr/bin/env python3
"""Reject prior unresolved owners before arena reuse or transport/file IO."""
import hashlib,json
from pathlib import Path
from check_terminal_zmodem_live import LiveZmodem,ROOT,BINARY
def main():
 cases=[]
 for sending in (False,True):
  for owner in ('source-open','source-uncertain','stage-open','stage-sealed','stage-uncertain'):
   m=LiveZmodem(sending=sending)
   if owner.startswith('source'):
    m.files['SEND.BIN']=bytearray(m.source)
    path=m.scratch(b'SEND.BIN\0',6000)
    assert m.call('_batch_upload_begin',[path])==0 and m.call('_batch_upload_next')==1
    if owner=='source-uncertain':m.fault=m.upload_fault='close';assert m.call('_batch_upload_abort')==8
   else:
    path=m.scratch(b'D:\\RECV\\\0',6000)
    assert m.call('_batch_download_begin',[path])==0 and m.call('_batch_download_open',[m.header()])==0
    if owner=='stage-uncertain':m.fault=m.upload_fault='close'
    if owner!='stage-open':assert m.call('_transfer_download_seal')==(8 if owner=='stage-uncertain' else 0)
   names=[('_upload_source_result',92),('_batch_upload_current',90),('_transfer_download_result',148),('_batch_download_result',240),('_terminal_batch_buffer',10240)]
   snapshots={name:m.snapshot(name,n) for name,n in names};fs=len(m.fs_calls);wire=bytes(m.tx);handles=dict(m.handles)
   assert m.run()==1 and m.get('terminal_transfer_fault')==7 and m.get('terminal_transfer_cleanup_status')==1
   assert all(m.snapshot(name,len(data))==data for name,data in snapshots.items())
   assert len(m.fs_calls)==fs and bytes(m.tx)==wire and m.handles==handles
   cases.append(dict(case=f'{sending}-{owner}',passed=True))
 report=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),inputs=len(cases),cases=cases,test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  scope='Actual linked live entry rejects cross-direction open/sealed/ambiguous owners before arena reuse, file operations or UART output. Snapshots and handle identity preserved. Kernel/hardware modeled; no original inputs.')
 (ROOT/'build/terminal/zmodem-owners-live-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Passed',len(cases),'unresolved-owner checks')
if __name__=='__main__':main()
