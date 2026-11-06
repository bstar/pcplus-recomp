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
 p.add_argument('--case',choices=('normal','repeat','missing-helper','missing-resource','bad-resource','flow'),default='normal')
 a=p.parse_args();package=a.package.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 bundle=json.loads((package/'package.json').read_text());m=json.loads((package/'manifest.json').read_text())
 assert m['experimental_chat_help']
 for name,digest in bundle['sources'].items():assert sha(ROOT/name)==digest,name
 stage=out/'program';stage.mkdir()
 for name,digest in bundle['products'].items():
  assert sha(package/name)==digest
  if (a.case=='missing-helper' and name=='PCHELP.RTE') or (a.case=='missing-resource' and name=='PCPLUS.HLP'):continue
  shutil.copyfile(package/name,stage/name)
 if a.case=='bad-resource':(stage/'PCPLUS.HLP').write_bytes(b'\x2f\0\0')
 staged={f.name:sha(f) for f in stage.iterdir() if f.is_file()}
 failed=a.case in ('missing-helper','missing-resource','bad-resource')
 source=(ROOT/'standalone/global_help_watch.asm').read_text()
 for old,new in [("cmp byte [es:190],'P'","cmp byte [es:72],'R'"),("cmp byte [es:194],'R'","cmp byte [es:74],'E'"),("cmp byte [es:198],'O'","cmp byte [es:76],'M'"),("cmp byte [es:2],'T'","cmp byte [es:2],'C'"),("cmp byte [es:4],'e'","cmp byte [es:4],'h'"),("cmp byte [es:6],'r'","cmp byte [es:6],'a'")]:
  assert source.count(old)==1;source=source.replace(old,new)
 local=(34 if a.rows>28 else 20)*160
 remote=(32 if a.rows>28 else 18)*160
 if failed:
  # PROGRAM's BIOS CR/LF prompt starts below the saved local-pane cursor,
  # rather than below the command-reference cursor on row0.
  for offset,c in [(160,'P'),(162,'r'),(164,'o')]:
   old=f"cmp byte [es:{offset}],'{c}'";assert source.count(old)==1
   source=source.replace(old,f"cmp byte [es:{local+offset}],'{c}'")
 source=source.replace(' jmp .candidate\n.help:',f" cmp byte [es:{local}],'A'\n jne .done\n cmp byte [es:{local+2}],'B'\n jne .done\n jmp .candidate\n.help:")
 if failed:
  # The PROGRAM error prompt overlays Chat, so REMOTE/AB still match before
  # acknowledgement. Do not mistake that for the restored Chat continuation.
  guard=f" cmp word [sample+2],2\n jne .failure_restored\n cmp byte [es:{local+160}],'P'\n je .done\n push es\n mov ax,0x40\n mov es,ax\n mov ax,[es:0x50]\n pop es\n cmp ax,[sample+8]\n jne .done\n.failure_restored:\n"
  source=source.replace(f" cmp byte [es:{local}],'A'",guard+f" cmp byte [es:{local}],'A'")
 if a.case=='flow':
  guard=' cmp word [sample+2],2\n jne .flow_ready\n'
  for i,c in enumerate(b'RXLIVE\xf0'):guard+=f' cmp byte [es:{remote+i*2}],{c}\n jne .done\n'
  source=source.replace(f" cmp byte [es:{local}],'A'",guard+f".flow_ready:\n cmp byte [es:{local}],'A'")
 observer_source=out/'HELPWAT.ASM';observer_source.write_text(source);observer=out/'HELPWAT.COM'
 subprocess.run(['nasm','-fbin',*(['-DWATCH_FAILURE'] if failed else []),*(['-DWATCH_REPEAT'] if a.case=='repeat' else []),str(observer_source),'-o',str(observer)],check=True)
 settings=bytearray(prm(port=3,baud=5,soft=1 if a.case=='flow' else 0))
 for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,a.rows),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',settings,off,value)
 harness.BINARY=stage/'TERMINAL.EXE';label=out.name+'-main';capture=ROOT/'build/connection-dos'/label;assert not capture.exists()
 body='a-z p2500 '+('enter' if failed else 'escape')+' '+('p3000 ' if a.case=='flow' else 'p1000 ')
 if a.case=='repeat':body+='a-z p2500 escape p1000 '
 keys='p900 enter p4000 a-o p1200 A B p900 '+body+'enter p1500 escape p900 r e a d y enter p1000 a-x'
 flow=dict(flow_updates=((6,b'RXLIVE\xf0'),)) if a.case=='flow' else {}
 r=harness.run(label,'success',keys,prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',arguments='@TEST.PRM /D:CaseTest:23',observer='HELPWAT',timeout=45,files={'HELPWAT.COM':observer.read_bytes()},online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-HELP\x1b[6n'),),**flow)
 raw=(capture/'HELPUI.BIN').read_bytes();words=struct.unpack_from('<10H',raw);before=raw[20:8020];helper=raw[8020:16020];after=raw[16020:24020];wire=(capture/'serial.bin').read_bytes()
 expected=bytearray(before)
 if a.case=='flow':expected[remote:remote+14:2]=b'RXLIVE\xf0'
 checks=dict(r['checks']);checks.update(complete_observer=len(raw)==24020 and words[:2]==(0x4847,5 if a.case=='repeat' else 3),actual_BIOS_rows=words[3]==a.rows,Chat_frame_retained=bytes(expected)==after,Chat_cursor_retained=words[4:6]==words[8:10],context3_helper_or_error=b'Program could not run' in helper[::2] if failed else helper[2:20:2]==b'Chat Mode',unfinished_line_retained=before[local:local+4:2]==b'AB' and after[local:local+4:2]==b'AB',line_sent_once=wire.count(b'AB\r')==1,ordinary_keys_resume=b'AB\rready\r' in wire,fresh_CPR=b'\x1b[3;11R' in wire,staged_inputs_unchanged=all(sha(stage/n)==d for n,d in staged.items()))
 if a.case=='flow':
  state=json.loads((capture/'flow-state.json').read_text());events=state['events'];sends=state['sends']
  checks.update(data_held_until_XON=len(sends)==1 and any(e['byte']==19 and e['at']<6 for e in events) and any(e['byte']==17 and 6<=e['at']<=sends[0]['at'] for e in events),raw_CP437_resumed_in_Chat=after[remote:remote+14:2]==b'RXLIVE\xf0' and before[remote:remote+14:2]==b' '*7)
 report=dict(passed=all(checks.values()),case=a.case,rows=a.rows,checks=checks,observer_words=words,products=bundle['products'],capture=str(capture.relative_to(ROOT)),sources={**bundle['sources'],**{n:sha(ROOT/n) for n in ['standalone/test_chat_help_main.py','standalone/global_help_watch.asm']}},generated_observer_sha256=sha(observer_source),scope=__doc__+' Passive timer copies actual full Chat/Help/Chat frames and BDA cursor; source-generated observer never writes product/video state. Real BIOS keys, DOS EXEC and UART. Repeat observes both cycles. Failure requires ordinary PROGRAM acknowledgement before Chat resumes. Flow requires timed raw CP437 traffic held until actual XON and exact returned frame with only the expected seven characters changed. No physical/SIP/audio or busy/geometry-fault acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in checks.items() if not v});return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
