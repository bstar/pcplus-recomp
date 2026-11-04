#!/usr/bin/env python3
"""Actual DOS Auto Answer partial-command carrier loss and same-parent redial.
Owned TCP peers, passive full-height notice frames and call-log observer. The
emulated modem supplies DCD/results; no product state or UART replies injected.
"""
import argparse,asyncio,inspect,json,re,types
from pathlib import Path
import test_phone_log_carrier_terminal as carrier
from answer_notice_watch import build as build_watcher
ROOT=carrier.ROOT;sha=carrier.sha
def adapter(rows):
 source=inspect.getsource(carrier.run_case)
 changes={
  "out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'":"out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'\n    build_watcher(out,SELECTED_ROWS)",
  "keys='p900 enter p6000 a-d p4500 r e a d y p1800 a-x'":"keys='p900 enter p2500 a-y p6000 a-d p4500 r e a d y p1800 a-x'",
  'sampler=SAMPLER':"sampler=SAMPLER.replace('mov cx,4000','mov cx,8000')",
  'cycles=fixed 6000':'cycles=fixed 12000',
  'D:\\\\PLWATCH T\nADDKEY':'D:\\\\PLWATCH T\nD:\\\\ANSWERW T\nADDKEY',
  'D:\\\\SNAP S\nD:\\\\PLWATCH':'D:\\\\SNAP S\nD:\\\\ANSWERW\nD:\\\\PLWATCH',
  "banner=b'\\x1b[2J\\x1b[HFIRST BYTE SAFE\\x1b[6n\\x1b[0c'":"banner=b'\\x1b[2J\\x1b[HFIRST BYTE SAFE\\x1b[6n\\x1b[0c'+LOWER_BANNER",
  "drop_ready=b'SCRIPTREADY\\r' in item['received'] if aspect else b'\\x1b[1;16R' in item['received'] and b'\\x1b[?1;2c' in item['received']":"drop_ready=b'ATS' in item['received']",
  'await asyncio.sleep(.2)':'await asyncio.sleep(0)',
  "(out/'TEST.PRM').write_bytes(config);(out/'TEST.DIR').write_bytes(directory_bytes)":"config[0x92:0xab]=b'~ATS0=1^M\\0'.ljust(25,b'\\0')\n    struct.pack_into('<H',config,0x1bc,0)\n    (out/'TEST.PRM').write_bytes(config);(out/'TEST.DIR').write_bytes(directory_bytes)",
 }
 for old,new in changes.items():
  expected=2 if old=='await asyncio.sleep(.2)' else 1
  assert source.count(old)==expected,(old,source.count(old));source=source.replace(old,new)
 m=types.ModuleType('answer_carrier');m.__dict__.update(carrier.__dict__);m.SELECTED_ROWS=rows;m.build_watcher=build_watcher
 m.LOWER_BANNER=b'\x1b'+f'[{rows-1};1HLOWER-{rows}'.encode()+b'\x1b[6n\x1b[H'
 exec(compile(source,carrier.__file__,'exec'),m.__dict__);return m
async def run_case(m,parent,out,rows,soft):
 name='soft' if soft else 'hard';r=await m.run_case(parent,out,name,0,soft);assert r['passed'],r['checks']
 frames=(out/'PAUSE.BIN').read_bytes();size=rows*160;first=(out/'connection-1.bin').read_bytes();second=(out/'connection-2.bin').read_bytes()
 log=(out/'dosbox.log').read_text();cmd=[s for s in re.findall(r'Command sent to modem: ->(.*?)<-',log) if s]
 dial=(out/'TEST.DIR').read_bytes()[275:296].split(b'\0',1)[0].decode();init='AT&K4' if soft else 'AT&K3';expected=[init,'ATD'+dial]*2
 checks=dict(r['checks'],two_complete_notice_frames=len(frames)==size*2,
  notice_on_reserved_row=all(frames[at+size-158:at+size-130:2]==b'AUTO ANSWER...' for at in (0,size)),
  lower_body_preserved=all(f'LOWER-{rows}'.encode() in frames[at+(rows-2)*160:at+(rows-1)*160:2] for at in (0,size)),
  first_partial_answer=b'ATS' in first and b'ATS0=1\r' not in first,
  clean_modem_commands=cmd in (expected,expected+['ATH']),no_modem_ERROR='Modem response: ERROR' not in log,
  lower_queries_on_both_calls=all(b'\x1b'+f'[{rows-1};9R'.encode() in data for data in (first,second)),
  final_notice_retired=b'AUTO ANSWER...' not in (out/'SCREEN.BIN').read_bytes()[::2])
 starts=list(re.finditer(re.escape('Command sent to modem: ->'+init+'<-'),log));assert len(starts)==2
 for at in starts:assert 'Modem response: OK' in log[at.end():log.index('Command sent to modem: ->ATD',at.end())]
 r.update(passed=all(checks.values()),checks=checks,rows=rows,soft=soft,modem_commands=cmd,
  artifacts={str(p.relative_to(ROOT)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='checks.json'})
 (out/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(rows,name,'FINAL PASS' if r['passed'] else str([n for n,v in checks.items() if not v]),flush=True);assert r['passed'];return r
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--rows',type=int,choices=[25,28,43,50],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);parent=(a.build/str(a.rows)).resolve()
 manifest=json.loads((parent/'manifest.json').read_text());assert manifest['diagnostic_session_rows_probe']==a.rows and sha(parent/'TERMINAL.EXE')==manifest['binary_sha256']
 sources=dict(manifest['sources'])
 for name in ['standalone/test_large_answer_carrier_dos.py','standalone/test_phone_log_carrier_terminal.py','standalone/answer_notice_watch.py','standalone/pause_watch.asm','standalone/phone_log_slow_write.asm','standalone/phone_log_events_watch.asm','standalone/test_phone_log_events_terminal.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','lab/bbs/phone_log_evidence.py']:sources[name]=sha(ROOT/name)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 m=adapter(a.rows)
 async def run():return [await run_case(m,parent,out/('soft' if soft else 'hard'),a.rows,soft) for soft in (0,1)]
 cases=asyncio.run(run())
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,rows=a.rows,cases=cases,sources=sources,terminal_path=str((parent/'TERMINAL.EXE').relative_to(ROOT)),terminal_sha256=sha(parent/'TERMINAL.EXE'),scope=__doc__+' Actual8086 DOS COM3/IRQ5/19200 HARD/SOFT, original-menu redial and two logged calls. Not physical/SIP/BBS acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
