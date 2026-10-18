#!/usr/bin/env python3
"""Loopback-only stock ENiGMA editor draft probe; never saves a message."""
import json,re,socket,time
from pathlib import Path
import synchronet
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/bbs-lab/results/enigma/editor-reference'
LOG=ROOT/'build/bbs-lab/enigma/source/logs/enigma-bbs.log'

def run():
 OUT.mkdir(parents=True,exist_ok=True)
 offset=LOG.stat().st_size
 synchronet.PORT=23233
 steps=[]
 with synchronet.Peer() as p:
  # ENiGMA's home probe expects home, unlike Synchronet's edge size probe.
  def plain(data):
   p.text.extend(data);p.history.extend(data)
   while b'\x1b[6n' in p.text[p.scan_from:]:
    i=p.text.find(b'\x1b[6n',p.scan_from);p.scan_from=i+4;p.send(b'\x1b[1;1R','CPRhome')
  p.plain=plain
  def rows():
   with LOG.open('rb') as f:f.seek(offset);return [json.loads(x) for x in f if x.strip()]
  def menu():
   names=[r['menuName'] for r in rows() if r.get('menuName')];return names[-1] if names else None
  def step(name,data=b'',delay=.7):
   start=len(p.text)
   if data:p.send(data,name)
   p.pump(delay);chunk=bytes(p.text[start:]);(OUT/(name+'.bin')).write_bytes(chunk);(OUT/(name+'.txt')).write_text(p.cleaned(chunk));steps.append({'name':name,'sent':data.hex(),'menu':menu(),'received':len(chunk)});print(name,menu(),repr(p.cleaned(chunk)[-180:]),flush=True)
  step('matrix',delay=3);step('login',b'\r');step('username',b'loclab\r');step('password',b'LoC-Lab-2026!\r',2)
  for i in range(20):
   m=menu()
   if m=='mainMenu':break
   step(f'advance-{i}',b'\x1b' if m=='fullLoginSequenceOnelinerz' else b'N' if m=='fullLoginSequenceNewScanConfirm' else b'\r',1)
  assert menu()=='mainMenu',menu()
  step('messages',b'M\r',1);step('conferences',b'J\r',1);step('select-conference',b'\r',1);step('areas',b'C\r',1);step('select-area',b'\r',1);step('new-post',b'P\r',1)
  assert menu()=='messageBaseNewPost',menu()
  step('to',b'\r');step('subject',b'LOCAL UNSAVED KEY TEST\r',1)
  step('body',b'ABCDE')
  for name,data in [('home',b'\x1b[1~'),('home-marker',b'H'),('end',b'\x1b[4~'),('end-marker',b'E'),('left',b'\x1b[D'),('delete',b'\x1b[3~'),('insert',b'\x1b[2~'),('overtype-marker',b'Z'),('tab',b'\t'),('tab-marker',b'T'),('pageup',b'\x1b[5~'),('pagedown',b'\x1b[6~'),('ctrl-y',b'\x19'),('after-delete-line',b'UNSAVED'),('editor-menu',b'\x1b')]:step(name,data)
  step('discard-select',b'\x1b[C');step('discard',b'\r',1)
  assert not any('posted message to' in r.get('msg','') for r in rows()),'Unexpected posted message'
  result={'passed':menu()=='messageBaseMainMenu','scope':'Independent reference peer, stock editor draft only; no DOS assertion and no Save command.','steps':steps,'server_rows':rows()}
  (OUT/'server-wire.bin').write_bytes(p.rx);(OUT/'client-wire.bin').write_bytes(p.tx);(OUT/'transcript.txt').write_text(p.cleaned(p.history));(OUT/'semantic-audit.json').write_text(json.dumps(result,indent=2)+'\n')
  assert result['passed'],menu()
if __name__=='__main__':run()
