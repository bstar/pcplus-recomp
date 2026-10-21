#!/usr/bin/env python3
"""Linked foreground receive policy through real UART ISR and file owners.

BIOS/hardware/DOS service boundaries are modeled, as in LiveZmodem; this is
not an actual DOS application or audio-path test.
"""
import hashlib,json
from collections import deque
from pathlib import Path
from check_terminal_zmodem_live import LiveZmodem,ROOT,BINARY,h


def main():
 rows=[]
 for credit in (0,1,128,256,1024,8192):
  for fmt in (65,67):
   for source in (b'',bytes(range(256))*5+b'\0\xff'):
    m=LiveZmodem(source=source,fmt=fmt)
    m.put('terminal_zmodem_receive_credit',credit)
    m.script=deque((h(1,0x23000000|(credit or 8192)) if want==h(1,0x23002000) else want,reply) for want,reply in m.script)
    assert m.run(owner=True)==0
    assert not m.script and not m.pending and not m.handles
    assert bytes(m.files['D:\\RECV\\ONE.BIN'])==source
    assert m.get('_terminal_zmodem_files',4)==1
    assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
    rows.append(dict(case='foreground-receive',credit=credit,format=fmt,size=len(source),passed=True))
 for credit in (1,256,8192,8193,65535):
  m=LiveZmodem(sending=True);m.put('terminal_zmodem_receive_credit',credit)
  assert m.run(owner=True)==0 and not m.script and not m.pending and not m.handles
  assert bytes(m.files['SEND.BIN'])==m.source
  assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
  rows.append(dict(case='receive-policy-does-not-change-sending',credit=credit,passed=True))
 for credit in (8193,65535):
  m=LiveZmodem();m.put('terminal_zmodem_receive_credit',credit)
  before_files={n:bytes(b) for n,b in m.files.items()};before_calls=list(m.fs_calls);before_tx=bytes(m.tx)
  assert m.run()==1 and m.get('terminal_transfer_fault')==7
  assert not m.handles and bytes(m.tx)==before_tx and m.fs_calls==before_calls
  assert {n:bytes(b) for n,b in m.files.items()}==before_files
  rows.append(dict(case='invalid-before-file-or-wire-effects',credit=credit,passed=True))
 result=dict(passed=True,case_count=len(rows),cases=rows,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
  test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope=__doc__)
 (ROOT/'build/terminal/terminal-zmodem-receive-credit-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Passed',len(rows),'linked receive-credit cases')


if __name__=='__main__':main()
