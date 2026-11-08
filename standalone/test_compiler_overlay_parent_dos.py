#!/usr/bin/env python3
"""Run actual full-parent whole-kernel startup loading/init/release in DOS.

No child RPC, serial session or source compiler integration is implied.
"""
import argparse,hashlib,json,os,re,shutil,struct,subprocess,zlib
from pathlib import Path
from directory_fixtures import prm
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case',choices=['valid','missing','corrupt','truncated','fixup-range','fixup-order'],default='valid')
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['diagnostic_compiler_lease_arena_probe'] and m['binary_sha256']==sha(binary)
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 for leaf in ('TERMINAL.EXE','PCLINE.OVL','PCMETA.OVL','PCCOMP.OVL'):shutil.copyfile(binary.with_name(leaf),out/leaf)
 module=m['experimental_compiler_lease_module'];assert module['whole_kernel']
 data=bytearray((out/'PCCOMP.OVL').read_bytes())
 if a.case=='missing':(out/'PCCOMP.OVL').unlink()
 elif a.case!='valid':
  if a.case=='corrupt':data[0]^=1
  elif a.case=='truncated':data.pop()
  else:
   assert module['relocations']>2
   if a.case=='fixup-range':struct.pack_into('<H',data,module['bank_bytes'],module['bank_bytes'])
   else:struct.pack_into('<H',data,len(data)-2,struct.unpack_from('<H',data,len(data)-4)[0])
   raw=bytearray((out/'TERMINAL.EXE').read_bytes());header=struct.unpack_from('<14H',raw)
   mat=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_compiler_overlay_expected\b',binary.with_name('terminal.map').read_text(),re.M);assert mat
   at=header[4]*16+int(mat[1],16)*16+int(mat[2],16)
   assert struct.unpack_from('<2H',raw,at)==(0x434b,1)
   struct.pack_into('<I',raw,at+8,zlib.crc32(data));(out/'TERMINAL.EXE').write_bytes(raw)
  (out/'PCCOMP.OVL').write_bytes(data)
 (out/'TEST.PRM').write_bytes(prm(port=3,baud=5))
 (out/'CHECK.BAT').write_bytes(b'@echo off\r\nset PCPLUS=C:\\MISSING\r\nC:\\TERMINAL @C:\\TEST.PRM >C:\\REPORT.BIN\r\nif errorlevel 1 goto bad\r\necho PASS>C:\\RESULT.TXT\r\ngoto done\r\n:bad\r\necho FAIL>C:\\RESULT.TXT\r\n:done\r\nexit\r\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nC:\\CHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 raw=(out/'REPORT.BIN').read_bytes();assert len(raw)>=16,raw
 suffix=raw[16:]
 expected_notice=b'\r\nUnsupported keyboard binding or local command; terminal stopped.\r\n'
 assert suffix==(b'' if a.case=='valid' else expected_notice),raw
 report=struct.unpack('<8H',raw[:16]);assert report[:2]==(0x434f,1),report
 result=(out/'RESULT.TXT').read_text().strip()
 if a.case=='valid':assert report[2]>=10 and report[3]==0 and report[4:6]==(1,0) and result=='PASS',report
 else:assert report[2]==1 and report[3:6]==(4,0,0) and result=='FAIL',report
 assert report[6:]==(module['bank_bytes'],module['keep_paragraphs']),report
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 d=dict(passed=True,case=a.case,parent_sha256=sha(binary),tested_parent_sha256=sha(out/'TERMINAL.EXE'),
  shutdown_notice=suffix.decode('ascii'),original_inputs=[],production_integrated=False,physical_verified=False,report=list(report),
  fixture_module_missing=a.case=='missing',expected_module_sha256=module['sha256'],fixture_module_sha256=None if a.case=='missing' else sha(out/'PCCOMP.OVL'),
  sources={n:sha(ROOT/n) for n in ['standalone/test_compiler_overlay_parent_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py']},
  scope=__doc__+' Source-only full parent before UART startup; duplicate load refusal, checked init/idle/valid, two loads/releases. Faults require refusal before init and release of arena. Fixup cases patch expected CRC in the owned diagnostic parent only. DOSBox8086/FPU-off integrated DOS; no live arbitration/child compilation/hardware claim.')
 (out/'result.json').write_text(json.dumps(d,indent=2)+'\n');print('PASS compiler parent startup:',a.case,list(report))
if __name__=='__main__':main()
