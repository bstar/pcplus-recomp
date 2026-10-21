#!/usr/bin/env python3
"""Challenge multiline evidence gates with retained TCP data and changed copies."""
import argparse,json,re
from pathlib import Path
from editor_multiline_evidence import ROOT,sha,load,check,STEPS


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--keys',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 keys=a.keys.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 proof,ref,body,_=load(keys);cohort=ROOT/ref['cohort']
 display=b'KEYTEST'+b''.join((cohort/(step+'.bin')).read_bytes() for step in STEPS)
 video=bytearray(b' \x07'*2000)
 def text(offset,value):
  for i,c in enumerate(value):video[offset+i*2]=c
 text(160,b'TAIL');text(3840,b'OVR 31,05');video=bytes(video)
 baseline,evidence=check(display,body,video,keys);assert all(baseline.values()),baseline
 cases=[];plain=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display)
 def reject(name,gate,d=display,b=body,s=video):
  changed,_=check(d,b,s,keys);cases.append(dict(name=name,passed=not changed[gate],expected_failed_gate=gate,failed_gates=[k for k,v in changed.items() if not v]))
 reject('missing_body_byte','multiline_exact_BIOS_to_serial_body',b=body[:-1])
 reject('wrong_page_key','multiline_exact_BIOS_to_serial_body',b=body.replace(b'\x1b[5~',b'\x1b[6~',1))
 page=plain.rfind(b'INS 17,05');assert page>=0
 reject('wrong_page_position','multiline_page_start_and_end',d=plain[:page]+b'INS 18,05'+plain[page+9:])
 reject('missing_edited_line29','multiline_edited_line29_redisplayed',d=plain.replace(b'H29:ABCD',b'X29:ABCD'))
 reject('missing_shortened_line30','multiline_shortened_line30_redisplayed',d=plain.replace(b'L30:ABC',b'X30:ABC'))
 reject('missing_tail_redisplay','multiline_tail_redisplayed',d=plain.replace(b'TAIL',b'FAIL'))
 no_tail=bytearray(video)
 for i in range(4):no_tail[160+i*2]=32
 reject('missing_DOS_tail','multiline_actual_DOS_tail_and_cursor_visible',s=bytes(no_tail))
 no_cursor=bytearray(video)
 for i in range(9):no_cursor[3840+i*2]=32
 reject('missing_DOS_cursor','multiline_actual_DOS_tail_and_cursor_visible',s=bytes(no_cursor))
 earlier=bytearray(video)
 for i,c in enumerate(b'INS'):earlier[3840+i*2]=c
 reject('earlier_tail_screen_cannot_finish','multiline_actual_DOS_tail_and_cursor_visible',s=bytes(earlier))
 reject('missing_position_response','multiline_all318_cursor_effects_match_TCP',d=plain.replace(b'INS 17,05',b'INS ??,??',1))
 unchanged=all(sha(cohort/n)==h for n,h in ref['captures_sha256'].items())
 result=dict(passed=all(c['passed'] for c in cases) and unchanged,baseline_checks=baseline,cases=cases,original_TCP_captures_unchanged=unchanged,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/editor_multiline_evidence.py',keys,ROOT/proof['reference']]},
  scope='Semantic audit controls only: real retained TCP display and typed body, explicitly synthetic final DOS video, and ten damaged copies. Missing/wrong keys, positions, edited redisplay, either final-video marker and the earlier INS31,05 tail screen must reject. No new DOS application, audio or hardware acceptance.')
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'counterexamples':len(cases),'baseline_checks':len(baseline)}));assert result['passed']


if __name__=='__main__':main()
