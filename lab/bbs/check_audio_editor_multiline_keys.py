#!/usr/bin/env python3
"""Check multiline BIOS keys and independent final-screen/watchdog guards in DOS."""
import argparse,json,os,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from check_audio_editor_burst_keys import PROBE,SAMPLER


def body():
 return b'\r'.join(f'L{i:02d}:ABCD'.encode() for i in range(1,31))+b'\x1b[A\x1b[HH\x1b[3~\x1b[F\x1b[B\x08\rTAIL'+b'\x1b[5~'*3+b'\x1b[6~'*3+b'\x1b[2~'


def words():
 scans={'L':0x26,':':0x27,'A':0x1e,'B':0x30,'C':0x2e,'D':0x20,'\r':0x1c,'0':0x0b}
 scans.update({str(i):i+1 for i in range(1,10)})
 seed='\r'.join(f'L{i:02d}:ABCD' for i in range(1,31))
 return [(scans[c]<<8)|ord(c) for c in seed]+[0x4800,0x4700,0x2348,0x5300,0x4f00,0x5000,0x0e08,0x1c0d,0x1454,0x1e41,0x1749,0x264c]+[0x4900]*3+[0x5100]*3+[0x5200]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--reference',type=Path,default=ROOT/'docs/validation/current-enigma-multiline-reference-04.json');a=p.parse_args()
 out=a.output.resolve();reference=a.reference.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 assert reference.is_relative_to(ROOT/'docs/validation');ref=json.loads(reference.read_text());assert ref['passed'] and ref['actual_TCP_editor_reference_accepted'] and len(ref['checks'])==25 and all(ref['checks'].values())
 for n,h in ref['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in ref['captures_sha256'].items():assert sha(ROOT/ref['cohort']/n)==h,n
 names=['seed30','up','home','insert-H','delete','end','down','backspace','split-newline','tail','page-up','page-up-top-visible','page-up-start','page-down','page-down-late','page-down-end','final-insert-mode']
 assert [s['name'] for s in ref['steps'] if s['name'] in names]==names
 assert b''.join(bytes.fromhex(s['sent_hex']) for s in ref['steps'] if s['name'] in names)==body()
 expected=words();assert len(expected)==288
 source=PROBE.replace('mov cx,25','mov cx,288').replace('received+50','received+576').replace('mov cx,52','mov cx,578').replace('times 26 dw','times 289 dw').replace("'UNSAVED'","'TAIL'").replace("'OVR 01,08'","'OVR 31,05'")
 start=source.index('keys: dw');end=source.index('subject: db',start)
 source=source[:start]+'keys: dw '+','.join(hex(v) for v in expected)+'\n'+source[end:]
 out.mkdir();helper=ROOT/'lab/bbs/audio_editor_keys.asm'
 for name,flags,baseline in [('DEFAULT.COM',[],ROOT/'build/bbs-lab/current-enigma-editor-audio-01/program/EXITKEY.COM'),('BURST.COM',['-DAUDIO_EDITOR_BURST=1','-DAUDIO_EDITOR_KEY_TICKS=1'],ROOT/'build/bbs-lab/current-enigma-editor-burst-audio-01/program/EXITKEY.COM')]:
  subprocess.run(['nasm','-fbin',*flags,str(helper),'-o',str(out/name)],check=True);assert (out/name).read_bytes()==baseline.read_bytes()
 subprocess.run(['nasm','-fbin','-DAUDIO_EDITOR_MULTILINE=1','-DAUDIO_EDITOR_KEY_TICKS=3',str(helper),'-o',str(out/'MULTILINE.COM')],check=True)
 modes=('complete-final-screen','text-only-blocks-exit','cursor-only-blocks-exit','prerequisite-watchdog','final-screen-watchdog');cases=[]
 for index,mode in enumerate(modes):
  folder=out/mode;folder.mkdir();(folder/'probe.asm').write_text(source);(folder/'sampler.asm').write_text(SAMPLER)
  watchdog=36 if index==3 else 327 if index==4 else 600
  flags=['-DAUDIO_EDITOR_MULTILINE=1','-DAUDIO_EDITOR_KEY_TICKS=1','-DAUDIO_EDITOR_INITIAL_TICKS=4',f'-DAUDIO_EDITOR_WATCHDOG_TICKS={watchdog}']
  subprocess.run(['nasm','-fbin',*flags,str(helper),'-o',str(folder/'EXITKEY.COM')],check=True)
  for src,leaf,extra in [(folder/'probe.asm','PROBE.COM',[f'-DCASE={index}']),(folder/'sampler.asm','SNAP.COM',[]),(ROOT/'lab/bbs/audio_get_vector.asm','KEYVEC.COM',[])]:subprocess.run(['nasm','-fbin',*extra,str(src),'-o',str(folder/leaf)],check=True)
  (folder/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[autoexec]
@echo off
mount c "{folder}"
mount d "{folder}"
c:
SNAP B
EXITKEY
PROBE
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
KEYVEC
SNAP A
exit
''')
  with (folder/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=log,stderr=log,timeout=35,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
  read=lambda n:(folder/n).read_bytes() if (folder/n).exists() else b''
  values=[0x2d00] if index==3 else expected+[0x2d00]
  checks=dict(exact_BIOS_words_and_final_guard=bool(read('PASS.TXT')) and not read('FAIL.TXT') and read('KEYS.BIN')==b''.join(v.to_bytes(2,'little') for v in values),normal_DOS_exit=r.returncode==0,hardware_and_timer_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),original_INT1C_restored=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'))
  cases.append(dict(mode=mode,checks=checks,captures_sha256={n:sha(folder/n) for n in ('KEYS.BIN','BEFORE.BIN','AFTER.BIN','KEYOLD.BIN','KEYNEW.BIN') if (folder/n).exists()}))
  print(json.dumps({'case':mode,'checks':checks}),flush=True)
 inputs=['lab/bbs/check_audio_editor_multiline_keys.py','lab/bbs/check_audio_editor_burst_keys.py','lab/bbs/audio_editor_keys.asm','lab/bbs/audio_get_vector.asm','standalone/test_terminal.py',str(reference.relative_to(ROOT))]
 result=dict(passed=all(v for c in cases for v in c['checks'].values()),cases=cases,body_key_count=len(expected),expected_serial_hex=body().hex(),reference=str(reference.relative_to(ROOT)),default_helper_binary_exact=True,burst_helper_binary_exact=True,default_helper_sha256=sha(out/'DEFAULT.COM'),burst_helper_sha256=sha(out/'BURST.COM'),production_helper_sha256=sha(out/'MULTILINE.COM'),inputs={n:sha(ROOT/n) for n in inputs},
  scope='Five actual8086 DOS BIOS helper probes,288 exact body key words and Alt-X, independent text/cursor final guards and prerequisite/final watchdogs; all sampler/vector state restores. Body matches the independently accepted TCP reference. Test initial/key delays4/1 ticks only; production multiline uses360/3 ticks and21600tick watchdog. Both original paced and rapid helpers assemble byte-identically. No DOS application/serial/BBS/audio multiline acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
