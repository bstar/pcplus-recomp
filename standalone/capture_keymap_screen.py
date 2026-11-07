#!/usr/bin/env python3
"""Explicit original DOS helper observation on synthetic media, no live machine."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA='f079418fca6392cde318e2eb657874a1f5ee10db83616c83054d191441fb6244'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 assert hashlib.sha256(a.original.read_bytes()).hexdigest()==SHA
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 watcher=(ROOT/'standalone/path_dialog_watch.asm').read_text();start=watcher.index(' cmp word [es:806]');end=watcher.index('%if WATCH_KIND',start)
 watcher=watcher[:start]+''' xor di,di
.find:
 mov bx,di
 mov si,title
 mov cx,17
.match:
 mov al,[si]
 cmp al,[es:bx]
 jne .next
 inc si
 add bx,2
 loop .match
 jmp .found
.next:
 add di,2
 cmp di,3966
 jbe .find
 jmp .done
.found:
'''+watcher[end:]
 watcher=watcher.replace('last_sum: dw 0',"title: db 'PgUp/Dn:Terminals'\nlast_sum: dw 0").replace('D:\\PATHVIEW.BIN','C:\\PATHVIEW.BIN')
 (out/'watch.asm').write_text(watcher)
 subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(out/'watch.asm'),'-o',str(out/'WATCH.COM')],check=True)
 shutil.copyfile(a.original,out/'PCKEYMAP.EXE');(out/'SYN.KBD').write_bytes(bytes(31284))
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 1000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nWATCH T\nADDKEY p5000 escape\nPCKEYMAP 6 SYN.KBD\nWATCH\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
 raw=(out/'PATHVIEW.BIN').read_bytes();magic,flags,ticks=struct.unpack_from('<3H',raw)
 assert magic==0x5044 and flags==3 and ticks and len(raw)==4071
 frame=raw[6:4006];rows=[frame[n*160:(n+1)*160:2].decode('cp437') for n in range(25)]
 assert 'PgUp/Dn:Terminals' in rows[24] and 'READING DATA...' not in rows[24] and 'KEYBOARD MAPPING' in rows[2]
 assert (out/'SYN.KBD').read_bytes()==bytes(31284)
 (out/'screen.txt').write_text('\n'.join(rows)+'\n')
 names=['standalone/capture_keymap_screen.py','standalone/path_dialog_watch.asm']
 result=dict(passed=True,original_sha256=SHA,cpu='8086',cycles=1000,profile=6,synthetic_KBD_bytes=31284,synthetic_KBD_unchanged=True,stable_ready_screen=True,observer_unhook_verified=True,frame_bytes=4000,frame_sha256=hashlib.sha256(frame).hexdigest(),character_sha256=hashlib.sha256(frame[::2]).hexdigest(),attribute_counts={str(v):frame[1::2].count(v) for v in sorted(set(frame[1::2]))},sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},limitations=['Original helper executed only in DOSBox on synthetic media; original copied only into ignored build.','Captured original screen is a reference; no source-built editor screen or physical acceptance yet.','Initial READING DATA screen is excluded by readiness marker.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
