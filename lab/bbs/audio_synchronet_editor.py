#!/usr/bin/env python3
"""Fresh owned Synchronet editor reference; synthetic draft and Ctrl-Q abort."""
import argparse,json,re
from pathlib import Path
from audio_synchronet import ROOT,snapshot,message_bodies,statistics,sha
from synchronet import Peer

KEYS=[('clear',b'\x19'),('body',b'ABCDE'),('home',b'\x1b[H'),('home-marker',b'H'),
 ('end',b'\x1b[F'),('end-marker',b'E'),('left',b'\x1b[D'),('delete',b'\x1b[3~'),
 ('insert',b'\x1b[2~'),('overwrite-marker',b'Z'),('tab',b'\t'),('tab-marker',b'T'),
 ('pageup',b'\x1b[5~'),('pagedown',b'\x1b[6~'),('delete-line',b'\x19'),
 ('unsaved',b'UNSAVED'),('abort',b'\x11')]

def editor_checks(display):
 clean=Peer.cleaned(display);csi=rb'\x1b\[[0-?]*[ -/]*[@-~]'
 return dict(stock_editor_entered='FSEditor v1.105' in clean,draft_aborted='Aborted.' in clean,
  insert_toggled_overtype='Overwrite Mode' in clean,
  home_marker_at_line_start=b'\x1b[5;1HHABCDE' in display,
  end_marker_at_line_end=b'\x1b[5;7HE' in display,
  delete_erases_final_character=b'\x1b[5;7H\x1b[5;7H\x1b[K' in display,
  tab_advances_to_next_stop=b'\x1b[5;8H \x1b[5;9H' in display,
  page_keys_report_document_boundaries=bool(re.search(b'T(?:'+csi+b')*\x07(?:'+csi+b')*\x07',display)),
  ctrl_y_delete_line_response=b'\x1b[M' in display and 'unsupported terminal' not in clean.lower())

def reference(out):
 out=out.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 server=snapshot();bodies=message_bodies();stats=statistics();steps=[];checks={};error=None
 with Peer() as peer:
  def phase(label,data=b'',needle=None):
   peer.text.clear();peer.scan_from=0
   if data:peer.send(data,label)
   if needle:peer.wait(needle,30)
   peer.pump(.7)
   (out/(label+'.bin')).write_bytes(peer.text);(out/(label+'.txt')).write_text(peer.clean)
   steps.append(label);return peer.clean
  try:
   phase('login',needle='Login:');phase('password',b'LABUSER\r','Password:')
   phase('welcome',b'LABPASS42\r','[Hit a key]');phase('bulletins',b' ','Enter number of bulletin or [Quit]')
   phase('scan',b'Q','Search all groups for new messages?');phase('pause',b'n\r','[Hit a key]')
   text=phase('main',b' ','Read/Post Messages')
   assert 'General:' in text,'This recipe requires the owned General area'
   text=phase('post',b'P','Subject:');assert 'To:' not in text,'Unexpected recipient prompt'
   phase('subject',b'KEYTEST\r','FSEditor v1.105')
   for label,data in KEYS:phase(label,data)
   assert 'Aborted.' in (out/'abort.txt').read_text()
   phase('final',b' ','Read/Post Messages')
   checks.update(editor_checks(bytes(peer.history)));checks['complete_reference_route']=True
  except Exception as exc:error=repr(exc);checks['complete_reference_route']=False
  finally:
   (out/'server-wire.bin').write_bytes(peer.rx);(out/'client-wire.bin').write_bytes(peer.tx)
   (out/'display.bin').write_bytes(peer.history);(out/'transcript.txt').write_text(Peer.cleaned(peer.history))
   (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 after=statistics();checks.update(pinned_server_inputs_preserved=server==snapshot(),message_bodies_preserved=bodies==message_bodies(),
  no_message_mail_or_transfer_writes=all(stats['Total'][k]==after['Total'][k] for k in ('posts','email','feedback','uploads','uploadb','dnloads','dnloadb')))
 result=dict(passed=all(checks.values()),checks=checks,error=error,steps=steps,server=server,message_bodies=bodies,
  statistics_before=stats,statistics_after=after,reference_inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py']},
  scope='Independent TCP reference with declared fixed CPR. Synthetic one-line draft is cleared first, exercises editing keys and Ctrl-Q abort; no save command. Page keys test one-line boundaries only. No DOS/audio/physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('passed','checks','error','steps')}));assert result['passed']

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);reference(p.parse_args().output)
