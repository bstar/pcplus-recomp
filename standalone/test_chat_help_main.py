#!/usr/bin/env python3
"""Actual DOS main Chat Alt-Z, native context3 helper and unfinished-line return."""
import argparse,json,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('package','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--rows',type=int,choices=(25,28,43,50),default=25)
 a=p.parse_args();package=a.package.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 bundle=json.loads((package/'package.json').read_text());m=json.loads((package/'manifest.json').read_text())
 assert m['experimental_chat_help']
 for name,digest in bundle['sources'].items():assert sha(ROOT/name)==digest,name
 stage=out/'program';stage.mkdir()
 for name,digest in bundle['products'].items():
  assert sha(package/name)==digest;shutil.copyfile(package/name,stage/name)
 source=(ROOT/'standalone/global_help_watch.asm').read_text()
 for old,new in [("cmp byte [es:190],'P'","cmp byte [es:72],'R'"),("cmp byte [es:194],'R'","cmp byte [es:74],'E'"),("cmp byte [es:198],'O'","cmp byte [es:76],'M'"),("cmp byte [es:2],'T'","cmp byte [es:2],'C'"),("cmp byte [es:4],'e'","cmp byte [es:4],'h'"),("cmp byte [es:6],'r'","cmp byte [es:6],'a'")]:
  assert source.count(old)==1;source=source.replace(old,new)
 local=(34 if a.rows>28 else 20)*160
 source=source.replace(' jmp .candidate\n.help:',f" cmp byte [es:{local}],'A'\n jne .done\n cmp byte [es:{local+2}],'B'\n jne .done\n jmp .candidate\n.help:")
 observer_source=out/'HELPWAT.ASM';observer_source.write_text(source);observer=out/'HELPWAT.COM'
 subprocess.run(['nasm','-fbin',str(observer_source),'-o',str(observer)],check=True)
 settings=bytearray(prm(port=3,baud=5))
 for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,a.rows),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',settings,off,value)
 harness.BINARY=stage/'TERMINAL.EXE';label=out.name+'-main';capture=ROOT/'build/connection-dos'/label;assert not capture.exists()
 keys='p900 enter p4000 a-o p1200 A B p900 a-z p2500 escape p1000 enter p1500 escape p900 r e a d y enter p1000 a-x'
 r=harness.run(label,'success',keys,prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',arguments='@TEST.PRM /D:CaseTest:23',observer='HELPWAT',timeout=40,files={'HELPWAT.COM':observer.read_bytes()},online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-HELP\x1b[6n'),))
 raw=(capture/'HELPUI.BIN').read_bytes();words=struct.unpack_from('<10H',raw);before=raw[20:8020];helper=raw[8020:16020];after=raw[16020:24020];wire=(capture/'serial.bin').read_bytes()
 checks=dict(r['checks']);checks.update(complete_observer=len(raw)==24020 and words[:2]==(0x4847,3),actual_BIOS_rows=words[3]==a.rows,Chat_frame_retained=before==after,Chat_cursor_retained=words[4:6]==words[8:10],context3_helper=helper[2:20:2]==b'Chat Mode',unfinished_line_retained=before[local:local+4:2]==b'AB' and after[local:local+4:2]==b'AB',line_sent_once=wire.count(b'AB\r')==1,ordinary_keys_resume=b'AB\rready\r' in wire,fresh_CPR=b'\x1b[3;11R' in wire,products_unchanged=all(sha(stage/n)==d for n,d in bundle['products'].items()))
 report=dict(passed=all(checks.values()),rows=a.rows,checks=checks,observer_words=words,products=bundle['products'],capture=str(capture.relative_to(ROOT)),sources={**bundle['sources'],**{n:sha(ROOT/n) for n in ['standalone/test_chat_help_main.py','standalone/global_help_watch.asm']}},generated_observer_sha256=sha(observer_source),scope=__doc__+' Passive timer copies actual full Chat/Help/Chat frames and BDA cursor; source-generated observer never writes product/video state. Real BIOS keys, DOS EXEC and UART. No physical/SIP/audio acceptance or busy/flow/fault coverage.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in checks.items() if not v});return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
