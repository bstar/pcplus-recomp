"""Observe the owned unmodified PCPlus viewer; never execute analysis images.

Requires ignored local originals/configuration. The passive timer watcher reads
VGA/BDA only; generated payloads and all copied configuration stay in build/.
This producer records observations; record_viewer_original.py checks behavior.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--case',required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();BASE=a.output.resolve();case=a.case
assert BASE.is_relative_to(ROOT/'build');BASE.mkdir(parents=True,exist_ok=True)
assert case in ['long','binary','empty','unterminated','no-lf','exact-page','large','retry']
out=BASE/case;out.mkdir(exist_ok=False);c=out/'c';c.mkdir();(out/'d').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();producer=sha(Path(__file__))
original=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE';digest=sha(original);assert digest=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
shutil.copyfile(original,c/'PCPLUS.EXE');shutil.copyfile(ROOT/'build/cwd-ui-recovery-20261104/first/c/PCPLUS.PRM',c/'PCPLUS.PRM')
for n in ['PCPLUS.KEY','PCPLUS.KBD','PCPLUS.XLT']:
 p=ROOT/'analysis/pcplus-install'/n
 if p.exists():shutil.copyfile(p,c/n)
payloads={'long':b'L'*79+b'A\r\n'+b'M'*80+b'B\r\n'+b'X'*132+b'1\r\n'+b'Y'*133+b'2\r\nDONE\r\n',
'binary':b'TAB\tMID\r\nC\rR\nNUL\0HIDDEN\r\nZ\x1aAFTER\r\nE\x1b[31mRED\r\n'+bytes([0x80,0x81,0xdb,0xb0,0xff])+b'\r\nTRAIL  \t\x1a\r\n \t\r\n',
'empty':b'', 'unterminated':b'NO FINAL NEWLINE', 'no-lf':b'A'*400,
'exact-page':b''.join(('L%03d\r\n'%i).encode() for i in range(1,25)),
'large':b''.join(('L%04d'%i).encode()+b'X'*125+b'\r\n' for i in range(1,721)), 'retry':b'FOUND AFTER RETRY\r\n'}
(c/'PAGE.DAT').write_bytes(payloads[case])
watch=(ROOT/'standalone/viewer_original_watch.asm').read_text()
if case=='large':
 marker='.candidate:\n';assert marker in watch
 watch=watch.replace(marker,marker+''' cmp byte [es:0],'L'
 jne .done
 cmp byte [es:2],'0'
 jne .done
 cmp byte [es:4],'5'
 jne .done
 cmp byte [es:6],'2'
 jne .done
 cmp byte [es:8],'9'
 jne .done
''')
(out/'watch.asm').write_text(watch);subprocess.run(['nasm','-fbin',str(out/'watch.asm'),'-o',str(c/'WATCH.COM')],check=True)
body='a-v p900 '
if case=='retry':body+='N O F I L E . X enter p1000 space p600 home '+('del '*43)
body+='P A G E . D A T enter p1200 '
if case=='exact-page':body+='pgdown p900 pgdown p600 pgup p900 '
if case=='large':body+=('pgdown p150 '*22)+'p1200 '
keys='p750 enter p3250 '+body+'escape p500 a-x p400 y enter p500 a-x p400 y enter'
assert len('ADDKEY '+keys)<500
config=out/'dosbox.conf';config.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=dummy
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{c}"
mount d "{out/'d'}"
c:
WATCH T
ADDKEY {keys}
C:\\PCPLUS
C:\\WATCH
cd>C:\\AFTERCD.TXT
echo DONE>C:\\DONE.TXT
exit
''')
with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
b=(c/'EDITVIEW.BIN').read_bytes();magic,count,ticks=struct.unpack_from('<3H',b);assert magic==0x4544 and count
frames=[]
for i in range(count):
 cursor,shape=struct.unpack_from('<2H',b,6+i*4004);f=b[10+i*4004:4010+i*4004];(out/f'frame-{i}.bin').write_bytes(f)
 (out/f'frame-{i}.txt').write_text('\n'.join(f[r*160:(r+1)*160:2].decode('cp437') for r in range(25)))
 frames.append(dict(index=i,cursor=[cursor>>8,cursor&255],shape=shape,sha256=hashlib.sha256(f).hexdigest()))
assert sha(Path(__file__))==producer and sha(c/'PCPLUS.EXE')==digest and (c/'PAGE.DAT').read_bytes()==payloads[case] and (c/'DONE.TXT').exists()
r=dict(case=case,original_sha256=digest,producer_sha256=producer,keys=keys,payload_sha256=sha(c/'PAGE.DAT'),payload_bytes=len(payloads[case]),watcher_sha256=sha(out/'watch.asm'),frames=frames,exit_CWD=(c/'AFTERCD.TXT').read_text().strip(),original_unchanged=True,payload_unchanged=True,done=True)
(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(case,count,'frames')
