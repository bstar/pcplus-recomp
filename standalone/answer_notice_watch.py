"""Build a passive timer witness for the native Auto Answer notice text cells."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
def build(out,rows):
 source=(ROOT/'standalone/pause_watch.asm').read_text()
 changes=[("message: db 'Screen paused.  Press any key to continue...'","message: db 'AUTO ANSWER...'"),('mov di,(PAUSE_ROWS-1)*160+18*2','mov di,(PAUSE_ROWS-1)*160+2'),('mov cx,44','mov cx,14'),('cmp word [cs:pause_ticks],18','cmp word [cs:pause_ticks],1')]
 for old,new in changes:assert source.count(old)==1,old;source=source.replace(old,new)
 (out/'answer-watch.asm').write_text(source)
 subprocess.run(['nasm','-fbin','-DPAUSE_ROWS='+str(rows),str(out/'answer-watch.asm'),'-o',str(out/'ANSWERW.COM')],check=True)
