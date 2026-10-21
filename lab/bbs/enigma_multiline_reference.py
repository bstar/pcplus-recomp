#!/usr/bin/env python3
"""Exercise an unsaved stock ENiGMA draft beyond one screen over loopback TCP."""
import argparse,json,re,sqlite3,subprocess,time
from pathlib import Path
import enigma,synchronet
from synthmodem_vm_control import ROOT,sha


def messages():
 with sqlite3.connect(f'file:{enigma.SOURCE}/db/message.sqlite3?mode=ro',uri=True) as db:
  return db.execute('SELECT COUNT(*) FROM message').fetchone()[0]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()==enigma.COMMIT
 subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=enigma.SOURCE,check=True)
 sources=[enigma.SOURCE/n for n in ('main.js','core/client.js','core/multi_line_edit_text_view.js','config/config.hjson')]
 sources+=sorted((enigma.SOURCE/'config/menus').glob('*.hjson'))
 identities={str(q.relative_to(ROOT)):sha(q) for q in sources}
 log=enigma.SOURCE/'logs/enigma-bbs.log';offset=log.stat().st_size;inode=log.stat().st_ino;count=messages()
 def rows():
  assert log.stat().st_ino==inode
  with log.open('rb') as f:f.seek(offset);return [json.loads(line) for line in f if line.strip()]
 def menu():
  names=[r['menuName'] for r in rows() if r.get('menuName')];return names[-1] if names else None
 out.mkdir(parents=True);checks={'multiline_sequence_complete':False};steps=[];error=None
 synchronet.HOST=enigma.HOST;synchronet.PORT=enigma.PORT
 with synchronet.Peer() as peer:
  def plain(data):
   peer.text.extend(data);peer.history.extend(data)
   while b'\x1b[6n' in peer.text[peer.scan_from:]:
    at=peer.text.find(b'\x1b[6n',peer.scan_from);peer.scan_from=at+4;peer.send(b'\x1b[1;1R','declared-CPR-home')
  peer.plain=plain
  def step(name,data=b'',delay=.4):
   start=len(peer.text)
   if data:peer.send(data,name)
   peer.pump(delay);chunk=bytes(peer.text[start:]);clean=peer.cleaned(chunk)
   positions=[(m,int(r),int(c)) for m,r,c in re.findall(r'(INS|OVR) (\d{2}),(\d{2})',clean)]
   row=dict(name=name,sent_hex=data.hex(),menu=menu(),positions=positions,bytes=len(chunk))
   steps.append(row);(out/(name+'.bin')).write_bytes(chunk)
   print(json.dumps(dict(step=name,position=positions[-1] if positions else None)),flush=True)
   return positions[-1] if positions else None
  try:
   step('matrix',delay=3);step('login',b'\r');step('username',enigma.USERNAME.encode()+b'\r');step('password',enigma.PASSWORD.encode()+b'\r',2)
   for i in range(20):
    current=menu()
    if current=='mainMenu':break
    step(f'advance-{i}',b'\x1b' if current=='fullLoginSequenceOnelinerz' else b'N' if current=='fullLoginSequenceNewScanConfirm' else b'\r',1)
   assert menu()=='mainMenu',menu()
   for name,data in [('messages',b'M\r'),('conferences',b'J\r'),('conference',b'\r'),('areas',b'C\r'),('area',b'\r'),('new-post',b'P\r'),('to',b'\r'),('subject',b'KEYTEST MULTILINE\r')]:step(name,data,.7)
   checks['actual_editor_entered']=menu()=='messageBaseNewPost';assert checks['actual_editor_entered']
   body=b'\r'.join(f'L{i:02d}:ABCD'.encode() for i in range(1,31))
   expected=[('seed30',body,('INS',30,9)),('up',b'\x1b[A',('INS',29,9)),('home',b'\x1b[H',('INS',29,1)),('insert-H',b'H',('INS',29,2)),('delete',b'\x1b[3~',('INS',29,2)),('end',b'\x1b[F',('INS',29,9)),('down',b'\x1b[B',('INS',30,9)),('backspace',b'\x08',('INS',30,8)),('split-newline',b'\r',('INS',31,1)),('tail',b'TAIL',('INS',31,5))]
   for name,data,position in expected:checks[name+'_position']=step(name,data,1 if name=='seed30' else .4)==position
   up1=step('page-up',b'\x1b[5~');up2=step('page-up-top-visible',b'\x1b[5~');up3=step('page-up-start',b'\x1b[5~')
   down1=step('page-down',b'\x1b[6~');down2=step('page-down-late',b'\x1b[6~');down3=step('page-down-end',b'\x1b[6~')
   # The owned80x25 editor has a14-line viewport. PageUp first changes its
   # top index, preserving cursor row; only at top index0 does it move to row1.
   checks['page_up_crosses_real_lines']=up1==('INS',17,5)
   checks['second_page_up_reaches_top_viewport']=up2==('INS',14,5)
   checks['third_page_up_reaches_start']=up3==('INS',1,5)
   checks['page_down_crosses_real_lines']=down1==('INS',15,5)
   checks['second_page_down_reaches_line29']=down2==('INS',29,5)
   checks['third_page_down_returns_to_tail']=down3==('INS',31,5)
   redraw=peer.cleaned(b''.join((out/n).read_bytes() for n in ('page-down.bin','page-down-late.bin','page-down-end.bin')))
   checks['edited_line29_reappears_on_scroll']='H29:ABCD' in redraw
   checks['backspaced_line30_reappears_on_scroll']='L30:ABC' in redraw and 'L30:ABCD' not in redraw
   checks['new_line31_reappears_on_scroll']='TAIL' in redraw
   checks['unique_final_overtype_mode']=step('final-insert-mode',b'\x1b[2~')==('OVR',31,5)
   checks['multiline_sequence_complete']=True
  except Exception as exc:error=repr(exc)
  finally:
   (out/'server-wire.bin').write_bytes(peer.rx);(out/'client-wire.bin').write_bytes(peer.tx)
   (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 time.sleep(.2);server_rows=rows();(out/'server-session.json').write_text(json.dumps(server_rows,indent=2)+'\n')
 checks['no_post_logged']=not any('posted message to' in r.get('msg','') for r in server_rows)
 checks['message_count_preserved']=messages()==count
 checks['source_and_configuration_preserved']=all(sha(ROOT/n)==h for n,h in identities.items())
 result=dict(passed=all(checks.values()),checks=checks,error=error,steps=steps,source_commit=enigma.COMMIT,server_inputs=identities,
  message_count_before=count,message_count_after=messages(),inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/synchronet.py',ROOT/'lab/bbs/enigma.py')},
  captures_sha256={q.name:sha(q) for q in out.iterdir() if q.is_file()},
  scope='Independent loopback TCP reference on pinned stock owned ENiGMA: thirty-line unsaved draft, up/down/Home/End/insert/Delete/Backspace/newline and three PageUp/three PageDown operations with edited text redisplay in the80x25/14-line viewport. Declared fixed CPRhome reference, not DOS rendering, BIOS mapping, SIP/audio, latency or physical hardware acceptance. Connection closes without saving; source/config and message count preserved.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'error':error}));assert result['passed']


if __name__=='__main__':main()
