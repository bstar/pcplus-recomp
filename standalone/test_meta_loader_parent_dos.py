#!/usr/bin/env python3
"""Run the actual full-parent startup Meta load/edit/save/reload probe in DOS."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from directory_fixtures import prm
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir();m=json.loads(binary.with_name('manifest.json').read_text());assert m['diagnostic_meta_loader_probe']and m['binary_sha256']==sha(binary)
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 for leaf in ('TERMINAL.EXE','PCLINE.OVL','PCMETA.OVL'):shutil.copyfile(binary.with_name(leaf),out/leaf)
 (out/'TEST.PRM').write_bytes(prm(port=3,baud=5));(out/'CHECK.BAT').write_text('@echo off\nset PCPLUS=C:\\MISSING\nC:\\TERMINAL @C:\\TEST.PRM >C:\\REPORT.BIN\nif errorlevel 1 goto bad\necho PASS>C:\\RESULT.TXT\ngoto done\n:bad\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nC:\\CHECK.BAT\nexit\n')
 with(out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 raw=(out/'REPORT.BIN').read_bytes();assert len(raw)==16,raw;report=struct.unpack('<8H',raw)
 assert report[:2]==(0x4d50,1)and report[2]>=18 and report[3:7]==(0,0,0,0)and report[7]==m['meta_editor_overlay']['bank_bytes'],report
 assert(out/'RESULT.TXT').read_text().strip()=='PASS'
 expected=bytearray(540)
 for i in range(10):expected[i*54]=3
 expected[2]=ord('x');assert(out/'METAPRB.KEY').read_bytes()==expected
 assert not(out/'KEYSTG.$$$').exists()and not(out/'KEYBAK.$$$').exists()
 result=dict(passed=True,parent_sha256=sha(binary),overlay_sha256=m['meta_editor_overlay']['sha256'],line_overlay_sha256=m['line_port_overlay']['sha256'],checks=report[2],report=list(report),saved_key_sha256=sha(out/'METAPRB.KEY'),original_inputs=[],sources={n:sha(ROOT/n)for n in ('standalone/test_meta_loader_parent_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py')},scope=__doc__+' Real source-built parent with synthetic owned KEY: exclusive pre-UART arena, native editor records, checked save/read, lease refusal, code overwrite/reload and clean release. Probe exits before normal UART/menu; no ordinary live terminal/arena arbitration or hardware acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS full parent Meta loader/save/reload:',report[2],'checks;exact540-byte KEY')
if __name__=='__main__':main()
