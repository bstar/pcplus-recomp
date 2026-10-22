#!/usr/bin/env python3
"""Replay captured late footer through actual linked renderer; only hardware is modeled."""
import argparse,json,re,sys
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
import audio_recording
sys.path.insert(0,str(ROOT/'standalone'))
from check_terminal_reset_live import prepare
from check_aspect_console import decode


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    fixture=ROOT/'lab/bbs/recording_marker_footer.json';f=json.loads(fixture.read_text());footer=bytes.fromhex(f['hex'])
    import hashlib
    assert hashlib.sha256(footer).hexdigest()==f['fragment_sha256'] and len(footer)==f['count']==458 and footer.startswith(b'\n')
    text=re.fullmatch('message "([^"]+)"\n',audio_recording.READY_MESSAGE).group(1)
    candidate=decode(text.encode('ascii'))+b'\r\n'
    assert candidate==b'\r\nRECORDER READY\r\n\r\n\r\n'
    rows=[];reproduced=0
    for profile in (4,6):
     for bottom in (23,24):
       for row in range(22,bottom+1):
        for col in (17,65):
         for leading_processed in (False,True):
          observed={}
          for variant,message in [('preceding',b'RECORDER READY\r\n'),('separated',candidate)]:
             machine=prepare(profile);machine.put('screen_last_row',bottom);machine.position(row,col)
             if leading_processed:machine.feed(footer[:1])
             machine.feed(message);before=bytes(machine.uc.mem_read(0xb8000,4000));assert b'RECORDER READY' in before[::2]
             cursor=[machine.get('screen_cursor_row'),machine.get('screen_cursor_column')]
             machine.feed(footer[1:] if leading_processed else footer);after=bytes(machine.uc.mem_read(0xb8000,4000))
             visible=b'RECORDER READY' in after[::2]
             if variant=='separated':assert visible
             name=f'{profile}-{bottom}-{row}-{col}-{int(leading_processed)}-{variant}'
             (out/(name+'-before.BIN')).write_bytes(before);(out/(name+'-after.BIN')).write_bytes(after)
             observed[variant]=dict(marker_survives=visible,cursor_after_message=cursor,before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest())
          if bottom==24 and row==22 and col==17 and not leading_processed:
             assert not observed['preceding']['marker_survives'] and observed['preceding']['cursor_after_message']==[23,0]
             reproduced+=1
          rows.append(dict(profile=profile,scroll_bottom=bottom,start=[row,col],leading_LF_already_processed=leading_processed,variants=observed,passed=True))
    assert reproduced==2
    result=dict(passed=True,cases=rows,observed_cursor_counterexamples=reproduced,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),fixture_sha256=sha(fixture),inputs={str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__).resolve(),fixture,Path(audio_recording.__file__),ROOT/'standalone/check_terminal_reset_live.py',ROOT/'standalone/check_line_edit_live.py',ROOT/'standalone/check_aspect_console.py',ROOT/'src/aspect/console_commands.asm']},scope=__doc__+' Both supported profiles, explicit23/24 scroll bottoms and selected bottom-row cursors/fragment boundaries. Local MESSAGE bytes use existing caret decoder plus native trailing CRLF. Preceding marker is erased in placements consistent with the cursor observed in audio; separating lines preserves it through this captured footer. No live BBS/audio or physical acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),old_layout_counterexamples=reproduced)))


if __name__=='__main__':main()
