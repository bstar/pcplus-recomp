#!/usr/bin/env python3
"""Owned loopback Synchronet stock FSEditor draft; Ctrl-Q abort only."""
import json
from pathlib import Path
from synchronet import Peer
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/bbs-lab/results/synchronet/editor-reference'
def run():
 OUT.mkdir(parents=True,exist_ok=True);steps=[]
 with Peer() as p:
  def sendwait(label,data=b'',needle=None,delay=1):
   p.text.clear();p.scan_from=0
   if data:p.send(data,label)
   if needle:p.wait(needle,25)
   else:p.pump(delay)
   t=p.clean;(OUT/(label+'.bin')).write_bytes(p.text);(OUT/(label+'.txt')).write_text(t);steps.append({'name':label,'sent':data.hex(),'received':len(p.text)});print(label,repr(t[-1100:]),flush=True)
  try:
   p.wait('Login:');sendwait('login',b'LABUSER\r','Password:');sendwait('password',b'LABPASS42\r','[Hit a key]');sendwait('welcome',b' ','Enter number of bulletin or [Quit]');sendwait('bulletins',b'Q','Search all groups for new messages?');sendwait('scan',b'n\r','[Hit a key]');sendwait('main',b' ','Read/Post Messages');
   if 'Notices:' in p.clean:sendwait('general-area',b'}',delay=1)
   assert 'General:' in p.clean,p.clean
   sendwait('post',b'P',delay=2);assert 'Subject:' in p.clean or 'To:' in p.clean,p.clean

   if 'To:' in p.clean:sendwait('recipient',b'All\r',delay=1)
   assert 'Subject:' in p.clean,p.clean
   sendwait('subject',b'LOCAL UNSAVED KEY TEST\r',delay=2)
   assert 'Insert Mode' in p.clean or 'FSEditor' in p.clean,p.clean
   for name,data in [('body',b'ABCDE'),('home',b'\x1b[H'),('home-marker',b'H'),('end',b'\x1b[F'),('end-marker',b'E'),('left',b'\x1b[D'),('delete',b'\x1b[3~'),('insert',b'\x1b[2~'),('overtype-marker',b'Z'),('tab',b'\t'),('tab-marker',b'T'),('pageup',b'\x1b[5~'),('pagedown',b'\x1b[6~'),('ctrl-y',b'\x19'),('abort',b'\x11')]:sendwait(name,data,delay=.6)
  finally:
   result={'passed':(OUT/'subject.bin').exists() and b'FSEditor v1.105' in (OUT/'subject.bin').read_bytes() and (OUT/'abort.bin').exists() and b'Aborted.' in (OUT/'abort.bin').read_bytes(),'scope':'Independent loopback reference FSEditor entry and unsaved draft abort; one-line page keys only establish boundary behavior.','steps':steps}
   (OUT/'semantic-audit.json').write_text(json.dumps(result,indent=2)+'\n')
   (OUT/'server-wire.bin').write_bytes(p.rx);(OUT/'client-wire.bin').write_bytes(p.tx);(OUT/'transcript.txt').write_text(p.cleaned(p.history));(OUT/'steps.json').write_text(json.dumps(steps,indent=2)+'\n')
if __name__=='__main__':run()
