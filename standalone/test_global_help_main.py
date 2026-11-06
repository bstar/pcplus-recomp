#!/usr/bin/env python3
"""Normal DOS main Alt-Z/Help/return, passive frames and resumed UART/parser."""
import argparse,json,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',choices=['normal','repeat','missing-helper','missing-resource','bad-resource','flow'],default='normal');a=p.parse_args();package=a.package.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((package/'package.json').read_text())
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 for name,digest in manifest['products'].items():assert sha(package/name)==digest,name
 stage=out/'program';stage.mkdir()
 for name in manifest['products']:
  if a.case=='missing-helper' and name=='PCHELP.RTE':continue
  if a.case=='missing-resource' and name=='PCPLUS.HLP':continue
  shutil.copyfile(package/name,stage/name)
 if a.case=='bad-resource':(stage/'PCPLUS.HLP').write_bytes(b'\x2f\0\0')
 staged={f.name:sha(f) for f in stage.iterdir() if f.is_file()}
 failed=a.case in ['missing-helper','missing-resource','bad-resource']
 observer=out/'HELPWAT.COM';subprocess.run(['nasm','-fbin',*(['-DWATCH_FAILURE'] if failed else []),*(['-DWATCH_REPEAT'] if a.case=='repeat' else []),str(ROOT/'standalone/global_help_watch.asm'),'-o',str(observer)],check=True)
 settings=bytearray(prm(port=3,baud=5,soft=1 if a.case=='flow' else 0))
 for at,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',settings,at,value)
 harness.BINARY=stage/'TERMINAL.EXE';label=out.name+'-main';drive=ROOT/'build/connection-dos'/label;assert not drive.exists()
 body='a-z p900 a-z p2500 '+('enter' if failed else 'escape')+' p900 '
 if a.case=='repeat':body+='a-z p2500 escape p900 '
 flow=dict(flow_updates=((3,b'\x1b[4;1HFLOW-BEFORE'),(6,b'\x1b[5;1HFLOW-AFTER\x1b[6n'))) if a.case=='flow' else {}
 result=harness.run(label,'success','p900 enter p4000 '+body+'escape p700 r e a d y enter p1000 a-x',prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',observer='HELPWAT',timeout=35,files={'HELPWAT.COM':observer.read_bytes()},online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-HELP\x1b[6n'),),**flow)
 raw=(drive/'HELPUI.BIN').read_bytes();words=struct.unpack_from('<10H',raw);before=raw[20:8020];help_frame=raw[8020:16020];after=raw[16020:24020]
 wire=(drive/'serial.bin').read_bytes();checks=dict(result['checks'])
 checks.update(complete_observer=len(raw)==24020 and words[:2]==(0x4847,5 if a.case=='repeat' else 3),reference_preserved=before==after,reference_cursor_lifetime=(words[4:6]==words[8:10] if a.case!='flow' else words[4:6]==(0x030b,0x2000) and words[8:10]==(0x040a,0x2000)),helper_or_error= b'Program could not run' in help_frame[::2] if failed else help_frame[2:28:2]==b'Terminal Help',ordinary_keys_resume=wire.count(b'ready\r')==1,fresh_CPR_after_help=b'\x1b[3;11R' in wire,unchanged_staged_files=all(sha(stage/n)==d for n,d in staged.items()))
 if a.case=='flow':
  state=json.loads((drive/'flow-state.json').read_text());events=[e['byte'] for e in state['events']]
  checks.update(help_flow_pause_and_resume=0x13 in events and 0x11 in events,flow_text_retained=b'FLOW-BEFORE' in (drive/'SCREEN.BIN').read_bytes()[::2] and b'FLOW-AFTER' in (drive/'SCREEN.BIN').read_bytes()[::2],scheduled_chunk_held_until_XON=len(state['sends'])==2 and any(e['byte']==0x13 and e['at']<6 for e in state['events']) and any(e['byte']==0x11 and 6<=e['at']<=state['sends'][1]['at'] for e in state['events']))
 report=dict(passed=all(checks.values()),case=a.case,checks=checks,products=manifest['products'],observer_words=words,capture=str(drive.relative_to(ROOT)),sources={**manifest['sources'],**{n:sha(ROOT/n) for n in ['standalone/test_global_help_main.py','standalone/global_help_watch.asm']}},scope='Normal DOS8086 COM3/IRQ5 synthetic modem, real BIOS Alt-Z twice, source PCHELP through PROGRAM, passive full frame/cursor reference return, ordinary key transmission and fresh parser reply. Helper/resources reside beside launching program on C while working directory is D. Repeat stores last Help/return frames and observes both cycles. Missing/damaged fixtures require the ordinary error acknowledgement. No physical/modem DSP/whole parity acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in checks.items() if not v});return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
