#!/usr/bin/env python3
"""Production DOS clipboard; serial peer and independent INT1C view sampler."""
import hashlib,json,struct,subprocess
from test_connection_dos import run,ROOT,BINARY

def main():
 out=ROOT/'build/clipboard-live-dos';out.mkdir(parents=True,exist_ok=True)
 child=out/'CLWATCH.COM'
 subprocess.run(['nasm','-f','bin',str(ROOT/'standalone/clipboard_watch.asm'),'-o',str(child)],check=True)
 cases=[]
 def case(name,keys,want,banner=None,updates=(),check=None):
  folder=ROOT/'build/connection-dos'/name;(folder/'CWATCH.BIN').unlink(missing_ok=True)
  proof=run(name,'success',keys,files={'CLWATCH.COM':child.read_bytes()},observer='CLWATCH',banner=banner,online_updates=updates)
  raw=(folder/'CWATCH.BIN').read_bytes();assert len(raw)==10246
  magic,count,ticks=struct.unpack_from('<3H',raw);assert magic==0x434c and count<=32
  frames=[raw[6+i*320:6+(i+1)*320] for i in range(count)]
  wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
  proof['checks'].update(independent_timer_observed_clipboard=ticks>3,expected_paste_bytes=want in wire.replace(b'\x1b[5;11R',b''),post_clipboard_keyboard=b'ready' in wire,local_menu_commands_absent=b'one.zip' not in wire)
  if check:proof['checks'].update(check(frames,wire,screen))
  proof['passed']=all(proof['checks'].values());proof['observed_frames']=[f.decode('cp437') for f in frames]
  cases.append(proof);print(name,proof['passed'],flush=True);assert proof['passed'],proof
 keys='p3000 a-= p400 a o n e . z i p enter p400 a t w o . a r j enter p400 space r 3 2 enter p400 t p500 s p500 p p500 escape p500 r e a d y p400 a-x'
 def live(frames,wire,screen):
  return dict(list_entries_observed=any(b'ONE.ZIP' in f[:240] and b'TWO.ARJ' in f[:240] for f in frames),single_removed_first_only=any(b'TWO.ARJ' in f[:80] and b'ONE.ZIP' not in f[:240] for f in frames),received_while_clipboard=b'\x1b[5;11R' in wire,live_screen_restored=screen[640:660:2]==b'BACKGROUND')
 case('clipboard-live-list',keys,b'ONE.ZIP \rONE.ZIP\rTWO.ARJ \r',updates=[(4.2,b'\x1b[5;1HBACKGROUND\x1b[6n')],check=live)
 banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c\r\n old.zip [next.arj]\r\n'
 keys='p3000 c-pgup p300 c p300 c enter p300 enter p300 escape p400 p p500 escape p300 escape p300 r e a d y p300 a-x'
 case('clipboard-live-cut',keys,b'OLD.ZIP\rNEXT.ARJ\r\r',banner=banner,check=lambda f,w,s:dict(cut_entries_observed=any(b'OLD.ZIP' in x[:240] and b'NEXT.ARJ' in x[:240] for x in f),cut_keys_not_transmitted=b'cc' not in w))
 sources=['standalone/test_clipboard_live_dos.py','standalone/clipboard_watch.asm','standalone/test_connection_dos.py','src/clipboard/clipboard.c','src/clipboard/clipboard.h','src/clipboard/clipboard_ui.c','src/clipboard/clipboard_ui.h','src/terminal/clipboard.asm','src/terminal/transport.asm','src/terminal/redisplay.asm','src/redisplay/redisplay.c']
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},scope='Actual DOS production terminal, real emulated UART/IRQ, BIOS keyboard and video. Independent timer samples clipboard list; synthetic modem peer records exact paste bytes and sends data/CPR during UI. No original executable, product test mode, physical modem or real remote-file existence claim.')
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Clipboard actual DOS:',len(cases),'passed')
if __name__=='__main__':main()
