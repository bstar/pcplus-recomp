#!/usr/bin/env python3
"""Execute parent continuation consumption and native WAITFOR at their explicit boundary."""
import argparse,json,sys
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
import audio_recording
sys.path.insert(0,str(ROOT/'standalone'))
from check_terminal_reset_live import prepare
from check_aspect_serial_commands import Machine,timeout,RESULT,DATA,OUT,decode


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    fixture=ROOT/'lab/bbs/recording_marker_footer.json';raw=bytes.fromhex(json.loads(fixture.read_text())['hex'])
    manifest=json.loads((OUT/'manifest.json').read_text());images=[]
    for unit in manifest['units']:
        path=OUT/unit['name'];assert sha(path)==unit['sha256'];images.append((unit['start'],unit['end_exclusive'],path.read_bytes()))
    rejected_pattern=b' '*20+b'^[[24;18H^[[0;1;31m^[[0;1;31m'
    assert raw.endswith(decode(rejected_pattern)) and audio_recording.READY_FOOTER=='By Date Added'
    rows=[]
    for profile in (4,6):
        parent=prepare(profile);parent.receive_irq(raw);leads=bytearray()
        while parent.get('uart_rx_count'):
            value=parent.call('ansi_next_byte');assert value!=65535
            parent.call('terminal_receive_character',[value],limit=1000000);leads.append(value)
        assert len(leads)<len(raw) and b'By Date Added' in leads
        (out/f'profile-{profile}-leads.bin').write_bytes(leads)
        for name,pattern in [('raw-ANSI-suffix',rejected_pattern),('plain-footer',audio_recording.READY_FOOTER.encode('ascii'))]:
          for kind,stream in [('raw',raw),('display-leads',bytes(leads))]:
            child=Machine(images,b'\x64\0'+timeout(0));child.cancel_after=20
            child.write(DATA['bank'],pattern+b'\0\0');child.queued(stream);child.invoke('wait_for')
            matched=bool(child.word(RESULT));expected=name=='plain-footer' or kind=='raw';assert matched==expected
            rows.append(dict(profile=profile,pattern=name,input_kind=kind,native_match=matched,consumed=child.rx_head,stream_bytes=len(stream),passed=True))
    result=dict(passed=True,cases=rows,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),native_units_manifest_sha256=sha(OUT/'manifest.json'),inputs={str(path.relative_to(ROOT)):sha(path) for path in (Path(__file__).resolve(),fixture,Path(audio_recording.__file__),ROOT/'standalone/check_terminal_reset_live.py',ROOT/'standalone/check_line_edit_live.py',ROOT/'standalone/check_aspect_serial_commands.py')},scope=__doc__+' Actual linked parent IRQ/parser instructions produce leads; actual native WAITFOR/string/caret instructions consume explicit raw or lead fixtures. Device/time callbacks modeled; not one attached DOS process. Raw ANSI suffix matches raw capture but cannot match the connected display-lead interface. Plain bottom filter text matches both; live DOS/TCP/audio remains separate.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
