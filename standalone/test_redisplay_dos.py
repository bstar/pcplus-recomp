#!/usr/bin/env python3
"""Actual DOS serviced scrollback, independent BIOS-timer video samples."""
import hashlib,json,struct,subprocess
from pathlib import Path
from test_connection_dos import run,ROOT,BINARY

def main():
 out=ROOT/'build/redisplay-dos';out.mkdir(parents=True,exist_ok=True)
 child=out/'RVWATCH.COM'
 subprocess.run(['nasm','-f','bin',str(ROOT/'standalone/redisplay_watch.asm'),'-o',str(child)],check=True)
 banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c\r\n'
 banner+=b''.join(f'ROW{i:03d}'.encode()+(b' TARGET' if i==60 else b'')+b'\r\n' for i in range(80))
 banner+=b'\x1b[2J\x1b[HFIRST BYTE SAFE'
 folder=ROOT/'build/connection-dos/redisplay-live'
 (folder/'RVIEW.BIN').unlink(missing_ok=True)
 proof=run('redisplay-live','success','p3000 c-pgup p700 home p700 pgdown p700 / t a r g e t enter p700 escape p1000 r e a d y p500 a-x',
  files={'RVWATCH.COM':child.read_bytes()},observer='RVWATCH',banner=banner,
  online_updates=[(4.2,b'\x1b[5;1HBACKGROUND\x1b[6n')])
 raw=(folder/'RVIEW.BIN').read_bytes();assert len(raw)==10246
 magic,count,ticks=struct.unpack_from('<3H',raw);assert magic==0x4452 and count<=32
 frames=[raw[6+i*320:6+(i+1)*320] for i in range(count)]
 rows=[f[:80].rstrip() for f in frames];footers=[f[240:].rstrip() for f in frames]
 wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
 proof['checks'].update(independent_timer_observed_redisplay=ticks>5,
  Home_shows_oldest_line=any(b'FIRST BYTE SAFE' in f[:240] for f in frames),
  page_navigation_shows_history=any(r.startswith(b'ROW021') for r in rows),
  search_finds_old_case_insensitive_target=any(r==b'ROW060 TARGET' for r in rows),
  query_prompt_observed=any(b'Search:' in f for f in footers),
  received_while_browsing_actual_CPR=b'\x1b[5;11R' in wire,
  latest_live_screen_restored=screen[640:660:2]==b'BACKGROUND',
  local_navigation_and_query_not_transmitted=b'target' not in wire and b'\x1b[5~' not in wire,
  post_view_keyboard_transmitted=b'ready' in wire)
 proof['passed']=all(proof['checks'].values());proof['observed_rows']=[f[:240].decode('cp437') for f in frames]
 proof['sources']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/test_redisplay_dos.py','standalone/redisplay_watch.asm','standalone/test_connection_dos.py','src/terminal/redisplay.asm','src/redisplay/redisplay.c']}
 proof['scope']='Production DOS terminal + CtrlPgUp/Home/PgDn/search/Esc. Independent INT1C observer samples actual viewer rows/footer; peer sends new bytes and CPR while browsing, final live screen and UART/IRQ/PIC restoration independently sampled. No product test mode or original executable.'
 (out/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));assert proof['passed']
if __name__=='__main__':main()
